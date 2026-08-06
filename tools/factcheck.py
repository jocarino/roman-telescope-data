#!/usr/bin/env python3
"""Check prose against the repo and the catalogue it describes.

Every factual error this project has made in its own drafts fell into one of a few shapes,
and most of them were checkable without leaving the repo:

- a planet was described as rendering "near-black" when its shipped swatch is vivid blue;
- an object was listed as a target when it is not in the catalogue at all;
- a code reference (`pipeline/cie.py`) named a file that moved (`pipeline/colour/cie.py`);
- a count ("five anchors", "5,764 planets") drifted from the data;
- a modelled upper limit was written up as a measurement.

The first four are mechanical: the dataset and the source tree are the ground truth, so prose
that contradicts them can be caught before it is published rather than by a reader. The fifth
is not decidable here — but a sentence that states a measurement with no source next to it can
at least be *listed*, so a human checks it deliberately instead of by luck.

    python3 tools/factcheck.py docs/**/*.md README.md
    python3 tools/factcheck.py --data ../data/planets.json docs/notes/marketing
    python3 tools/factcheck.py --json docs | jq '.findings[] | select(.severity=="error")'

Exit status is 1 if any `error` finding survives, so this can gate a publish step. Suppress a
line with a trailing `<!-- factcheck: ignore -->`; suppress a file with `<!-- factcheck: off -->`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Prose checks run on prose. Paths and symbols are still checked inside fenced blocks, because a
# stale path in a runnable command is exactly as wrong as a stale path in a sentence.
_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_LINE_IGNORE = re.compile(r"<!--\s*factcheck:\s*ignore\s*-->")
_FILE_OFF = re.compile(r"<!--\s*factcheck:\s*off\s*-->")

_FILE_SUFFIXES = ("py", "json", "html", "css", "js", "md", "yaml", "yml", "toml", "cff", "conf",
                  "txt", "sh", "lock", "cfg", "ini")
_PATH_RE = re.compile(r"\b([\w.\-]+(?:/[\w.\-]+)+\.(?:" + "|".join(_FILE_SUFFIXES) + r"))\b")
# A repo-local module path used bare, e.g. `pipeline/colour/cie.py`, is caught above. A bare
# filename with no directory is too ambiguous to check, so it is left alone.
#
# A symbol must carry an underscore to be checked. Without that rule the check fires on every
# survey acronym a draft quotes in backticks (`KELT`, `OGLE`, `MASCARA`) and on filenames
# (`LICENSE`, `README`) — none of which are claims about our source at all.
_SYMBOL_RE = re.compile(r"^_?[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")

# Directories that are built, vendored or gitignored: a path under them is not a claim about
# the source tree, so a miss there is noise rather than a finding.
_UNCHECKED_PREFIXES = ("dist/", "node_modules/", ".git/", "data/planets.json", "docs/notes/",
                       "obs/", "web/static/planets/")


#: Flags whose argument is a file the command writes rather than one that must already exist.
_WRITES_TO = re.compile(r"(?:^|\s)(?:>|>>|-o|--(?:\w+-)?(?:emit|out|output|write|save|to)"
                        r"(?:-\w+)?)\s+\S*$")


@dataclass
class Finding:
    """One problem with one line of prose."""

    path: str
    line: int
    check: str
    severity: str  # error | warn | info
    message: str
    excerpt: str

    def to_json(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "check": self.check,
                "severity": self.severity, "message": self.message, "excerpt": self.excerpt}


# --------------------------------------------------------------------------------------------
# The catalogue: names, colours and counts come from the shipped dataset, never from memory.
# --------------------------------------------------------------------------------------------

@dataclass
class Catalogue:
    """The facts a draft can be checked against, loaded once from `planets.json`."""

    by_key: dict[str, dict] = field(default_factory=dict)      # normalised name -> record
    display: dict[str, str] = field(default_factory=dict)      # normalised name -> display name
    prefixes: set[str] = field(default_factory=set)            # "WASP", "HD", "Kepler", ...
    counts: dict[str, int] = field(default_factory=dict)
    loaded: bool = False


def _norm(name: str) -> str:
    """Collapse the ways the same object gets written: case, spacing, hyphens, attached letter."""
    s = name.strip().lower()
    s = re.sub(r"[\s_\-]+", " ", s)
    # "HD189733b", "HD 189733 b" and "hd-189733b" are one object: split letter/digit runs, then
    # detach a trailing planet letter.
    s = re.sub(r"([a-z])(\d)", r"\1 \2", s)
    s = re.sub(r"(\d)\s*([a-h])\b", r"\1 \2", s)
    return re.sub(r"\s+", " ", s).strip()


#: Catalogue aliases the Archive resolves but prose does not. The site labels these objects by
#: the right-hand form, so a draft using the left-hand one sends a reader to a dead search.
_NAME_ALIASES = {"gliese": "gj", "gl": "gj", "hip": "hip", "bd": "bd"}


def _alias_forms(key: str) -> list[str]:
    """Alternative normalised keys the same object may be catalogued under."""
    head, _, rest = key.partition(" ")
    swapped = _NAME_ALIASES.get(head)
    return [f"{swapped} {rest}"] if swapped and swapped != head and rest else []


#: True once we know whether the pipeline's own abbreviation map is reachable. Duplicating that
#: map here would be the very drift this tool exists to catch, so we import it or say we can't.
_EXPAND_AVAILABLE: bool | None = None


def _expand(name: str) -> str:
    """Expand Archive abbreviations ("47 UMa b" -> "47 Ursae Majoris b") via the pipeline map."""
    global _EXPAND_AVAILABLE
    try:
        from pipeline.catalog import _display_name  # noqa: PLC0415 - optional, heavy import
    except Exception:
        _EXPAND_AVAILABLE = False
        return name
    _EXPAND_AVAILABLE = True
    return _display_name(name)


def load_catalogue(data_path: Path | None) -> Catalogue:
    """Load `planets.json`. Missing data is not fatal: catalogue checks simply stand down."""
    cat = Catalogue()
    if data_path is None or not data_path.exists():
        return cat
    payload = json.loads(data_path.read_text())
    records = payload.get("planets", payload if isinstance(payload, list) else [])
    for rec in records:
        name = rec.get("name")
        if not name:
            continue
        cat.by_key[_norm(name)] = rec
        cat.display[_norm(name)] = name
        host = (rec.get("host_star") or {}).get("name")
        if host:
            cat.by_key.setdefault(_norm(host), rec)
            cat.display.setdefault(_norm(host), host)
        # The detector's vocabulary is the catalogue's own naming systems, so it covers exactly
        # the prefixes in use (WASP, HD, HIP, TOI, TrES, Kepler, ...) and nothing invented.
        # Single-word names are not designations: taking "Jupiter" as a prefix turns the phrase
        # "Jupiter 1x/3x metallicity" into a hunt for a planet called "Jupiter 1".
        tokens = name.split()
        head = tokens[0].split("-")[0]
        if len(tokens) > 1 and head[:1].isalpha() and len(head) >= 2:
            cat.prefixes.add(head)
    cat.counts = {
        "planets": len(records),
        "anchors": sum(1 for r in records if r.get("provenance") == "measured-albedo"),
        "cgi_targets": sum(1 for r in records if r.get("provenance") == "simulated-cgi"),
        "microlensing": sum(1 for r in records if r.get("provenance") == "model-microlensing"),
    }
    cat.loaded = True
    return cat


def _family(rec: dict) -> str | None:
    """The colour family the site itself would file this planet under."""
    srgb = ((rec.get("true_colour") or {}).get("srgb"))
    if not srgb or len(srgb) != 3:
        return None
    try:
        from pipeline.colour.family import colour_family  # noqa: PLC0415 - optional import
    except Exception:
        return None
    return colour_family(tuple(int(c) for c in srgb))


# --------------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------------

def check_paths(line: str, lineno: int, path: Path, repo: Path,
                elsewhere: dict[str, list[str]]) -> list[Finding]:
    """A path written in prose must exist in the source tree."""
    out: list[Finding] = []
    seen: set[str] = set()
    for match in _PATH_RE.finditer(line):
        ref = match.group(1)
        if ref in seen or ref.startswith(("http", "//")) or "://" in line[:match.start()][-12:]:
            continue
        seen.add(ref)
        if any(ref.startswith(p) for p in _UNCHECKED_PREFIXES):
            continue
        # `--emit-manifest data/manifest.json` names a file the command *creates*. Absence is
        # the normal state there, so it is not a stale reference.
        if _WRITES_TO.search(line[max(0, match.start() - 28):match.start()]):
            continue
        if (repo / ref).exists() or (path.parent / ref).exists():
            continue
        # A path that is plainly someone else's (an npm package, a URL fragment) is not a claim
        # about this repo. Only flag paths whose first segment is a directory we actually have.
        first = ref.split("/")[0]
        if not (repo / first).exists():
            continue
        # A wrong path is worth far more as a fix than as a complaint, so offer the file that
        # has this basename if exactly one exists. `pipeline/cie.py` -> `pipeline/colour/cie.py`.
        hits = elsewhere.get(Path(ref).name, [])
        hint = f" — did you mean `{hits[0]}`?" if len(hits) == 1 else ""
        out.append(Finding(str(path), lineno, "code-ref", "error",
                           f"`{ref}` does not exist in the repo{hint}", line.strip()))
    return out


def index_basenames(roots: list[Path]) -> dict[str, list[str]]:
    """basename -> the paths that actually carry it, for 'did you mean' on a stale reference."""
    index: dict[str, list[str]] = {}
    for root in roots:
        if not root.exists():
            continue
        for src in root.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(root)
            if any(part in _SKIP_DIRS - {"docs"} for part in rel.parts):
                continue
            index.setdefault(src.name, []).append(str(rel))
    return {k: sorted(set(v)) for k, v in index.items()}


def check_symbols(line: str, lineno: int, path: Path, repo: Path,
                  symbol_index: dict[str, bool]) -> list[Finding]:
    """A CONSTANT quoted in backticks must be defined somewhere in the source tree."""
    out: list[Finding] = []
    for match in _INLINE_CODE.finditer(line):
        token = match.group(1).strip()
        if not _SYMBOL_RE.match(token):
            continue
        if token not in symbol_index:
            symbol_index[token] = _grep_symbol(repo, token)
        if not symbol_index[token]:
            out.append(Finding(str(path), lineno, "code-ref", "error",
                               f"`{token}` is not defined anywhere in the repo", line.strip()))
    return out


_SOURCE_GLOBS = ("*.py", "*.js", "*.html", "*.css", "*.toml", "*.yaml", "*.yml", "*.conf",
                 "*.sh", "Dockerfile*", "Makefile")
# Skipped by their path *relative to the repo*: an absolute check would skip everything when the
# repo is itself a worktree under `.claude/`.
_SKIP_DIRS = {".git", "dist", "node_modules", "__pycache__", ".venv", ".claude", "docs"}


def _iter_sources(repo: Path):
    for glob in _SOURCE_GLOBS:
        for src in repo.rglob(glob):
            rel = src.relative_to(repo)
            if any(part in _SKIP_DIRS for part in rel.parts):
                continue
            yield src


def _grep_symbol(repo: Path, token: str) -> bool:
    """True if the token appears in any source file. Cheap, and good enough for a name."""
    for src in _iter_sources(repo):
        try:
            if token in src.read_text(errors="ignore"):
                return True
        except OSError:
            continue
    return False


#: Seeded rather than derived, because the error we most need to catch is an object from a
#: naming system our catalogue does not contain at all — HIP 71618 B was flagged only because
#: the data happens to hold other HIP planets, and that is luck, not a check.
_BASE_PREFIXES = {
    "HD", "HIP", "HR", "GJ", "Gliese", "Gl", "BD", "WASP", "HAT-P", "HATS", "KELT", "TrES",
    "XO", "K2", "Kepler", "TOI", "TIC", "KOI", "CoRoT", "OGLE", "MOA", "KMT", "LHS", "LP",
    "LTT", "TRAPPIST", "PSR", "WD", "NGTS", "MASCARA", "Qatar", "EPIC", "2MASS", "WISE",
}
#: Flamsteed/Bayer designations ("47 UMa b", "51 Peg b", "ups And d", "upsilon Andromedae d")
#: carry no catalogue prefix at all, so they need their own shape.
_BAYER_RE = re.compile(
    r"\b((?:\d{1,3}|alf|bet|gam|del|eps|zet|tet|iot|kap|lam|ksi|omi|sig|ups|ome|alpha|beta|"
    r"gamma|delta|epsilon|zeta|theta|iota|kappa|lambda|xi|omicron|sigma|upsilon|omega|tau|mu|"
    r"nu|rho|pi|chi|phi|psi|eta)\s+[A-Z][A-Za-z]{1,12}(?:\s+[A-Z][a-z]{2,12})?\s+[a-h])\b")


def _object_candidates(line: str, prefixes: set[str]) -> list[str]:
    """Pull catalogue-shaped object designations out of a sentence."""
    alt = "|".join(sorted((re.escape(p) for p in prefixes | _BASE_PREFIXES),
                          key=len, reverse=True))
    pattern = re.compile(rf"\b((?:{alt})[-\s]?\d+(?:[-\s]?\d+)?\s*[A-Ha-h]?)\b")
    found = [m.group(1).strip() for m in pattern.finditer(line)]
    found += [m.group(1).strip() for m in _BAYER_RE.finditer(line)]
    return found


def check_objects(line: str, lineno: int, path: Path, cat: Catalogue) -> list[Finding]:
    """An object named in prose should be in the catalogue, under the label the site shows."""
    if not cat.loaded:
        return []
    out: list[Finding] = []
    for raw in _object_candidates(line, cat.prefixes):
        key = _norm(raw)
        if key in cat.by_key:
            continue
        alt = next((k for k in [_norm(_expand(raw)), *_alias_forms(key)] if k in cat.by_key), None)
        if alt is not None:
            out.append(Finding(str(path), lineno, "object-name", "warn",
                               f"'{raw}' is an alias; the site labels it "
                               f"'{cat.display[alt]}', so that is what a reader can search for",
                               line.strip()))
            continue
        # A truncated designation ("OGLE-2005" for OGLE-2005-BLG-390L b) is the regex stopping
        # early, not a wrong name. Only report it if nothing in the catalogue extends it.
        if any(k.startswith(key + " ") or k.startswith(key) for k in cat.by_key
               if len(k) > len(key)):
            continue
        near = _nearest_name(key, cat)
        hint = f" — closest catalogue entry is '{near}'" if near else ""
        out.append(Finding(str(path), lineno, "object-name", "error",
                           f"'{raw}' is not in the catalogue{hint}. Check it is a real target "
                           f"and that it passes the completeness gate", line.strip()))
    return out


def _nearest_name(key: str, cat: Catalogue) -> str | None:
    """The catalogue label a mistyped or aliased designation most likely meant."""
    import difflib  # noqa: PLC0415 - only needed on the failure path

    match = difflib.get_close_matches(key, list(cat.by_key), n=1, cutoff=0.85)
    return cat.display.get(match[0]) if match else None


# What a reader would call each family. A claim is wrong only if it lands outside the
# neighbourhood of the family the site itself assigns.
_COLOUR_WORDS: dict[str, set[str]] = {
    "near-black": {"dark"}, "black": {"dark"}, "sooty": {"dark"}, "pitch": {"dark"},
    "blue": {"blue", "azure", "periwinkle", "teal"},
    "cobalt": {"blue", "azure"}, "azure": {"azure", "blue"},
    "teal": {"teal", "green", "azure"}, "blue-green": {"teal", "green", "azure"},
    "green": {"green", "teal"},
    "cream": {"white", "gold", "grey"}, "off-white": {"white", "grey"},
    "white": {"white", "grey"}, "pale": {"white", "grey"},
    "gold": {"gold", "orange"}, "golden": {"gold", "orange"}, "yellow": {"gold"},
    "orange": {"orange", "gold", "brown"}, "amber": {"gold", "orange"},
    "red": {"red", "orange", "brown"}, "crimson": {"red"},
    "brown": {"brown", "orange"}, "grey": {"grey", "white"}, "gray": {"grey", "white"},
    "violet": {"violet", "periwinkle"}, "purple": {"violet", "periwinkle"},
    "pink": {"pink", "red"},
}
_COLOUR_RE = re.compile(r"\b(" + "|".join(sorted(_COLOUR_WORDS, key=len, reverse=True)) + r")\b",
                        re.IGNORECASE)


def check_colour_claims(line: str, lineno: int, path: Path, cat: Catalogue) -> list[Finding]:
    """A colour word next to a planet name must agree with that planet's shipped swatch."""
    if not cat.loaded:
        return []
    out: list[Finding] = []
    seen: set[str] = set()
    for sentence in _SENTENCES.split(line):
        for raw, span in _object_candidates_spanned(sentence, cat.prefixes):
            rec = cat.by_key.get(_norm(raw)) or cat.by_key.get(_norm(_expand(raw)))
            if rec is None or rec["name"] in seen:
                continue
            actual = _family(rec)
            if actual is None:
                continue
            # The colour word has to be talking about *this* planet: near the name, in the same
            # sentence. Without that, one long line naming four planets and mentioning molten
            # iron reports four wrong colours.
            near = _colour_words_near(sentence, span)
            if not near or any(actual in _COLOUR_WORDS[w] for w in near):
                continue
            # A sentence that says the colour is unknown, wished-for or surprising is not
            # claiming it. Hedges are how this project writes honestly; do not punish them.
            if _COLOUR_HEDGE.search(sentence):
                continue
            seen.add(rec["name"])
            shown = (rec.get("true_colour") or {}).get("hex", "?")
            out.append(Finding(str(path), lineno, "colour-claim", "error",
                               f"{rec['name']} renders {shown} ({actual}); this sentence calls "
                               f"it {'/'.join(sorted(near))}", sentence.strip()))
    return out


#: Sentence-ish split. Markdown prose is not English prose, so table cells and list bullets end
#: a thought as surely as a full stop does.
_SENTENCES = re.compile(r"(?<=[.!?;])\s+|\s*\|\s*|\s+[–—]\s+")
#: How far from the planet's name a colour word may sit and still be describing it.
_COLOUR_WINDOW = 70
#: Language that frames a colour as unknown, desired or contrary to appearance.
_COLOUR_HEDGE = re.compile(
    r"\b(don't know|do not know|unknown|wants? to be|would be|expected to be|not actually|"
    r"looks normal|isn't|is not|rather than|instead of|despite|even though|one model)\b",
    re.IGNORECASE)


def _object_candidates_spanned(text: str, prefixes: set[str]) -> list[tuple[str, tuple[int, int]]]:
    """Object designations with where they sit, so proximity can be judged."""
    alt = "|".join(sorted((re.escape(p) for p in prefixes | _BASE_PREFIXES),
                          key=len, reverse=True))
    pattern = re.compile(rf"\b((?:{alt})[-\s]?\d+(?:[-\s]?\d+)?\s*[A-Ha-h]?)\b")
    found = [(m.group(1).strip(), m.span()) for m in pattern.finditer(text)]
    found += [(m.group(1).strip(), m.span()) for m in _BAYER_RE.finditer(text)]
    return found


#: A colour word attached to one of these is describing the page, not the planet.
_NOT_THE_PLANET = re.compile(
    r"^\W*(background|backdrop|canvas|card|page|grid|text|type|border|frame|bar|letterbox|"
    r"gradient|overlay|panel|swatch card|chrome|starfield|sky|space)\b", re.IGNORECASE)


def _colour_words_near(sentence: str, span: tuple[int, int]) -> set[str]:
    start, end = span
    left = max(0, start - _COLOUR_WINDOW)
    window = sentence[left:end + _COLOUR_WINDOW]
    words = set()
    for m in _COLOUR_RE.finditer(window):
        if _NOT_THE_PLANET.match(window[m.end():m.end() + 24]):
            continue
        words.add(m.group(1).lower())
    return words


_COUNT_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\b([\d,]{3,})\s+(?:known\s+|catalogued\s+)?(?:planets|worlds|exoplanets)\b"),
     "planets", "planets in the dataset"),
    (re.compile(r"\b(\w+)\s+solar[- ]system\s+anchors\b", re.IGNORECASE),
     "anchors", "solar-system anchors"),
    (re.compile(r"\b(\w+)\s+(?:CGI|Roman)\s+(?:tech[- ]demo\s+)?targets\b", re.IGNORECASE),
     "cgi_targets", "planets with simulated-CGI provenance"),
]
_WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def _as_int(token: str) -> int | None:
    token = token.strip().lower().replace(",", "")
    if token.isdigit():
        return int(token)
    return _WORD_NUMBERS.get(token)


#: A sentence about the Archive's total, or about some other population, is not a claim about
#: our dataset and must not be measured against it.
_OTHER_DENOMINATOR = re.compile(
    r"\b(archive|nasa|pscomppars|known to science|discovered|confirmed by)\b", re.IGNORECASE)
#: A difference, a range or an approximation is not a count of the dataset.
_NOT_A_COUNT = re.compile(
    r"([~≈–—]\s*[\d,]+\s*(?:planets|worlds)|\b(?:about|roughly|around|only|up to|under|over|"
    r"more than|fewer than)\s+[\d,]+\s*(?:planets|worlds)|[\d,]+\s*(?:planets|worlds)\s+"
    r"(?:behind|ahead|short|more|fewer|missing))", re.IGNORECASE)
#: Only a sentence that ties its number to *our* data can be judged wrong against our data.
_OUR_DATASET = re.compile(
    r"\b(the site ships|we ship|the dataset|planets\.json|the gallery|the catalogue ships|"
    r"our catalogue|the site (?:has|holds|covers))\b", re.IGNORECASE)


def check_counts(line: str, lineno: int, path: Path, cat: Catalogue) -> list[Finding]:
    """A count stated in prose must match what the dataset actually holds.

    Rounding is honest ("about 5,700 worlds"); a precise number that is wrong is not. So a round
    number close to the truth passes silently, a round number far from it is a warning that the
    sentence may be counting something else, and a precise mismatch is an error.
    """
    if not cat.loaded or _NOT_A_COUNT.search(line):
        return []
    out: list[Finding] = []
    for pattern, key, label in _COUNT_PATTERNS:
        for match in pattern.finditer(line):
            claimed = _as_int(match.group(1))
            actual = cat.counts.get(key)
            if claimed is None or actual is None or claimed == actual:
                continue
            # "another table holds N" only excuses the number when the cue is *beside* it. A
            # sentence-wide test let a stale README count hide behind the word "NASA" 30 words
            # further on.
            if _OTHER_DENOMINATOR.search(line, max(0, match.start() - 30), match.end() + 30):
                continue
            rounded = claimed % 100 == 0 and claimed >= 100
            drift = abs(claimed - actual) / max(actual, 1)
            if rounded and drift <= 0.05:
                continue
            # A number is only an *error* when the sentence says it is describing our data;
            # otherwise it may be counting a subset, a future build or someone else's table.
            severity = "error" if _OUR_DATASET.search(line) and not rounded else "warn"
            out.append(Finding(str(path), lineno, "count", severity,
                               f"says {claimed:,} {label}; the dataset has {actual:,}",
                               line.strip()))
    return out


_MEASUREMENT_CUE = re.compile(
    r"\b(geometric albedo|albedo of|albedo is|measured (?:at|to be)|reflects\s+[\d.]+\s*%"
    r"|A_?g\s*[=<>]|brightness temperature of)\b", re.IGNORECASE)
_SOURCE_CUE = re.compile(
    r"(et al\.|\(\d{4}\)|arXiv|doi\.|doi:|https?://|upper limit|lower limit|\bmodel(?:led)?\b"
    r"|\bpredicted\b|\bassumed\b|\bsimulated\b)", re.IGNORECASE)


#: How close a number must sit to the measurement cue to be *its* value rather than a list
#: marker or an unrelated figure elsewhere in the sentence.
_VALUE_WINDOW = 40


def check_sourcing(line: str, lineno: int, path: Path) -> list[Finding]:
    """List measurement claims with no source and no hedge beside them, for a human to settle.

    Only claims carrying an actual *value* count, and only when that value sits next to the
    claim. Defining a term, or naming a quantity the site computes, is not a measurement claim,
    and counting those drowns the ones a human needs to check.
    """
    cue = _MEASUREMENT_CUE.search(line)
    if cue is None or _SOURCE_CUE.search(line):
        return []
    window = line[max(0, cue.start() - _VALUE_WINDOW):cue.end() + _VALUE_WINDOW]
    if not re.search(r"\d*\.?\d+\s*(?:%|per cent)|\b0\.\d+|\b\d+\.\d+\b", window):
        return []
    return [Finding(str(path), lineno, "sourcing", "warn",
                    "states a measurement with no citation, limit or hedge on the same line",
                    line.strip())]


# --------------------------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------------------------

def _outside_code(text: str) -> str:
    """Text with inline-code spans blanked out.

    A marker only counts when it is *used*. Documenting `<!-- factcheck: off -->` in the README
    switched the README off — found by this tool reporting nothing about a file with known stale
    numbers in it, which is the quietest way a checker can fail.
    """
    return _INLINE_CODE.sub(" ", text)


def check_file(path: Path, cat: Catalogue, repo: Path, symbol_index: dict[str, bool],
               elsewhere: dict[str, list[str]]) -> list[Finding]:
    text = path.read_text(errors="ignore")
    if _FILE_OFF.search(_outside_code(text)):
        return []
    findings: list[Finding] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if _LINE_IGNORE.search(_outside_code(line)):
            continue
        findings += check_paths(line, lineno, path, repo, elsewhere)
        findings += check_symbols(line, lineno, path, repo, symbol_index)
        if in_fence:
            continue
        findings += check_objects(line, lineno, path, cat)
        findings += check_colour_claims(line, lineno, path, cat)
        findings += check_counts(line, lineno, path, cat)
        findings += check_sourcing(line, lineno, path)
    return findings


def collect_files(targets: list[str]) -> list[Path]:
    out: list[Path] = []
    for target in targets:
        p = Path(target)
        if p.is_dir():
            out += sorted(q for q in p.rglob("*.md") if ".git" not in q.parts)
        elif p.exists():
            out.append(p)
    return out


_SEVERITY_RANK = {"error": 0, "warn": 1, "info": 2}
_MARK = {"error": "✗", "warn": "!", "info": "·"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", nargs="*", default=["docs", "README.md"],
                    help="markdown files or directories to check")
    ap.add_argument("--data", default=str(REPO_ROOT / "data" / "planets.json"),
                    help="planets.json to check names, colours and counts against")
    ap.add_argument("--repo", default=str(REPO_ROOT), help="source tree paths are resolved against")
    ap.add_argument("--severity", default="warn", choices=["error", "warn", "info"],
                    help="lowest severity to report")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    data_path = Path(args.data)
    cat = load_catalogue(data_path)
    files = collect_files(args.targets or ["docs", "README.md"])

    # "Did you mean" looks in the repo and in the doc tree being checked, because the private
    # notes moved wholesale once and every path reference in them went stale at the same time.
    doc_roots = {Path(t).resolve() if Path(t).is_dir() else Path(t).resolve().parent
                 for t in (args.targets or ["docs"])}
    elsewhere = index_basenames([repo, *sorted(doc_roots)])

    symbol_index: dict[str, bool] = {}
    findings: list[Finding] = []
    for path in files:
        findings += check_file(path, cat, repo, symbol_index, elsewhere)

    floor = _SEVERITY_RANK[args.severity]
    findings = [f for f in findings if _SEVERITY_RANK[f.severity] <= floor]
    findings.sort(key=lambda f: (_SEVERITY_RANK[f.severity], f.path, f.line))

    if args.json:
        print(json.dumps({"files_checked": len(files), "catalogue_loaded": cat.loaded,
                          "alias_expansion": _EXPAND_AVAILABLE, "counts": cat.counts,
                          "findings": [f.to_json() for f in findings]}, indent=2))
    else:
        if not cat.loaded:
            print(f"note: {data_path} not found — name, colour and count checks stood down.\n")
        if _EXPAND_AVAILABLE is False:
            # Without it, "47 UMa b" reads as an unknown object rather than a known alias, so
            # the run over-reports. Better to say so than to let someone act on the noise.
            print("note: `pipeline.catalog` is not importable, so Archive abbreviations are not "
                  "expanded — run under `uv run` for the full check.\n")
        for f in findings:
            print(f"{_MARK[f.severity]} {f.path}:{f.line}  [{f.check}] {f.message}")
            print(f"    {f.excerpt[:160]}")
        errors = sum(1 for f in findings if f.severity == "error")
        warns = len(findings) - errors
        print(f"\n{len(files)} files · {errors} error(s) · {warns} warning(s)")

    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
