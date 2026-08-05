#!/usr/bin/env python3
"""newswatch — turn an exoplanet headline into a briefing you can post from.

The job (see docs/notes/marketing/01-newsjacking.md): when a planet makes the news,
put *our computed colour of that exact planet* in front of the people already reading
about it, within the two-hour window that matters — without ever asserting a colour
built from parameters the very paper being reported has just superseded.

Everything here is deterministic. It polls feeds, matches planet names against an alias
table built from the Archive, ranks, and prints FACTS plus empty-slot copy scaffolds.
It never writes the sentence — a templated caption is the thing 11-bluesky-mastodon.md
says kills the account, and the sentence is the only part of a post with any value.

Subcommands
    feeds     Check every source resolves (and snapshot them as a test fixture).
    aliases   Build the name -> planet lookup from the Archive. Run once, then weekly.
    poll      Poll the feeds, rank, and print at most 3 briefings. The daily driver.
    brief     Briefing for one named planet, on demand. The test path and the bench.
    bench     Pre-write briefings for the ~20 planets that generate the headlines.
    log       Show the newsjack log.

Testing it without waiting for news
    python3 tools/newswatch.py brief "K2-18 b"          # the whole output, right now
    python3 tools/newswatch.py feeds --save-fixture tests/fixtures/feeds
    python3 tools/newswatch.py poll --fixture tests/fixtures/feeds --dry-run

Stdlib only, so it runs under bare python3 with no venv.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
import textwrap
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLANETS = REPO / "data" / "planets.json"
RELEASE_FILE = REPO / "data" / "RELEASE"
CACHE = REPO / "data" / "cache"
ALIAS_FILE = CACHE / "newswatch-aliases.json"
STATE_FILE = CACHE / "newswatch-state.json"

UA = "newswatch/1.0 (exoplanet-palette; polite daily poll)"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# --- the sources -----------------------------------------------------------
# Priority order matters: `press` feeds are the single best predictor that a story
# travels, and arXiv is a STOCK-BUILDING feed, not an early-warning one (a routine
# preprint precedes its press release by weeks; an embargoed one by hours at best).
# Every URL re-resolved live on 2026-08-05.


@dataclass(frozen=True)
class Feed:
    id: str
    name: str
    url: str
    kind: str  # "press" | "editorial" | "aggregator" | "preprint"


FEEDS: tuple[Feed, ...] = (
    Feed("nasa", "NASA", "https://www.nasa.gov/feed/", "press"),
    Feed("esa", "ESA Space Science",
         "https://www.esa.int/rssfeed/Our_Activities/Space_Science", "press"),
    Feed("eso", "ESO", "https://www.eso.org/public/news/feed/", "press"),
    Feed("aasnova", "AAS Nova", "https://aasnova.org/feed/", "editorial"),
    Feed("physorg", "Phys.org astronomy",
         "https://phys.org/rss-feed/space-news/astronomy/", "aggregator"),
    Feed("universetoday", "Universe Today", "https://www.universetoday.com/feed/", "aggregator"),
    Feed("arxiv", "arXiv astro-ph.EP", "https://rss.arxiv.org/rss/astro-ph.EP", "preprint"),
)

# Sources with no feed at all — printed as a reminder rather than polled, because a tool
# that silently omits them would imply we're watching something we aren't.
MANUAL_SOURCES = (
    ("NASA Exoplanet Archive updates", "Thursdays · no RSS exists · email list on the Connect "
     "page, or scrape https://exoplanetarchive.ipac.caltech.edu/docs/exonews_archive.html"),
    ("AAS meeting press-conference programme", "published ~2 weeks ahead — the only lead time "
     "in this whole plan that is verifiably longer than a day"),
    ("Bluesky astro feed / list", "fastest human signal; see 11-bluesky-mastodon.md"),
)

# Nouns a non-astronomer already owns. Test One of "will it travel" — stories travel on
# these, not on results.
TRAVEL_NOUNS = (
    "earth-like", "earthlike", "habitable", "life", "biosignature", "nearest", "closest",
    "first", "water", "ocean", "diamond", "rain", "seven planets", "twin", "super-earth",
    "atmosphere", "clouds", "colour", "color", "blue", "goldilocks", "alien", "signs of",
)

# The flight configuration of Roman's coronagraph, per pipeline/config.py:ROMAN_CGI.
# Repeated here (rather than imported) to keep this file stdlib-only; tests/test_newswatch.py
# pins the two together, so a change in config.py fails CI rather than silently un-gating
# the most dangerous number this tool prints.
FLIGHT_BANDS = ("cgi-575", "cgi-730", "cgi-825")

# The pre-built bench. Stock beats speed: these are the planets that actually generate
# exoplanet headlines, and a briefing written in daylight turns a jack into a 5-minute publish.
BENCH = (
    "TRAPPIST-1 b", "TRAPPIST-1 d", "TRAPPIST-1 e", "TRAPPIST-1 f", "TRAPPIST-1 g",
    "K2-18 b", "LHS 1140 b", "Proxima Cen b", "GJ 1214 b", "WASP-39 b", "55 Cnc e",
    "HD 189733 b", "HD 209458 b", "TrES-2 b", "Kepler-7 b", "WASP-12 b", "WASP-76 b",
    "WASP-121 b", "TOI-700 d", "Kepler-186 f", "GJ 486 b", "GJ 367 b", "LP 890-9 c",
    "47 UMa b", "ups And d", "HR 8799 b",
)

# Prefixes a designation regex always forgets, plus the press's own spellings. The lookup is
# built from the Archive; this file only holds what the Archive does NOT give us: IAU
# NameExoWorlds names the press loves, and the catalogue-prefix synonyms.
HAND_ALIASES: dict[str, str] = {
    # IAU NameExoWorlds — the press uses these and the Archive's pl_name does not.
    "dimidium": "51 Peg b",
    "osiris": "HD 209458 b",
    "bellerophon": "51 Peg b",
    "methuselah": "PSR B1620-26 b",
    "poltergeist": "PSR B1257+12 c",
    "phobetor": "PSR B1257+12 d",
    "draugr": "PSR B1257+12 b",
    "galileo": "HD 23079 b",
    "quijote": "mu Ara b",
    "amateru": "eps Tau b",
    "arion": "HD 102956 b",
    "tadmor": "gam Cep b",
    "smertrios": "HD 149026 b",
    "janssen": "55 Cnc e",
    "galileo-55cnc": "55 Cnc b",
    "brahe": "55 Cnc b",
    "lipperhey": "55 Cnc d",
    "harriot": "55 Cnc f",
    "aegir": "eps Tau b",
    "dagon": "Fomalhaut b",
    "halla": "8 UMi b",
}

# Star-catalogue prefix synonyms. The press writes "Gliese 1214 b"; the Archive writes
# "GJ 1214 b". Applied to the *normalised* form, so spacing is already gone.
PREFIX_SYNONYMS: tuple[tuple[str, str], ...] = (
    ("gliese", "gj"),
    ("gl", "gj"),
    ("wolf", "wolf"),      # kept verbatim; listed so the intent is on the record
    ("ross", "ross"),
    ("bd", "bd"),
    ("2mass", "2m"),
    ("betapic", "betpic"),
    ("betapictoris", "betpic"),
    ("upsilonandromedae", "upsand"),
    ("upsilonand", "upsand"),
)

# Greek-letter names the press spells out but the Archive abbreviates. Normalised forms.
GREEK_LONG_TO_SHORT = {
    "alpha": "alf", "beta": "bet", "gamma": "gam", "delta": "del", "epsilon": "eps",
    "zeta": "zet", "theta": "tet", "iota": "iot", "kappa": "kap", "lambda": "lam",
    "xi": "ksi", "omicron": "omi", "sigma": "sig", "upsilon": "ups", "omega": "ome",
    "mu": "mu", "nu": "nu", "pi": "pi", "rho": "rho", "tau": "tau", "chi": "chi",
    "psi": "psi", "phi": "phi", "eta": "eta",
}

# Constellation genitives the press spells out. "51 Pegasi b" -> "51 Peg b". Used in BOTH
# directions: the Archive stores the abbreviation, so we have to generate the long form the
# press actually prints.
CONSTELLATION_LONG_TO_SHORT = {
    "andromedae": "and", "antliae": "ant", "apodis": "aps", "aquarii": "aqr",
    "aquilae": "aql", "arae": "ara", "arietis": "ari", "aurigae": "aur", "bootis": "boo",
    "caeli": "cae", "camelopardalis": "cam", "cancri": "cnc", "canumvenaticorum": "cvn",
    "canismajoris": "cma", "canisminoris": "cmi", "capricorni": "cap", "carinae": "car",
    "cassiopeiae": "cas", "centauri": "cen", "cephei": "cep", "ceti": "cet",
    "chamaeleontis": "cha", "circini": "cir", "columbae": "col", "comaeberenices": "com",
    "coronaeaustralis": "cra", "coronaeborealis": "crb", "corvi": "crv", "crateris": "crt",
    "crucis": "cru", "cygni": "cyg", "delphini": "del", "doradus": "dor", "draconis": "dra",
    "equulei": "equ", "eridani": "eri", "fornacis": "for", "geminorum": "gem", "gruis": "gru",
    "herculis": "her", "horologii": "hor", "hydrae": "hya", "hydri": "hyi", "indi": "ind",
    "lacertae": "lac", "leonis": "leo", "leonisminoris": "lmi", "leporis": "lep",
    "librae": "lib", "lupi": "lup", "lyncis": "lyn", "lyrae": "lyr", "mensae": "men",
    "microscopii": "mic", "monocerotis": "mon", "muscae": "mus", "normae": "nor",
    "octantis": "oct", "ophiuchi": "oph", "orionis": "ori", "pavonis": "pav", "pegasi": "peg",
    "persei": "per", "phoenicis": "phe", "pictoris": "pic", "piscium": "psc",
    "piscisaustrini": "psa", "puppis": "pup", "pyxidis": "pyx", "reticuli": "ret",
    "sagittae": "sge", "sagittarii": "sgr", "scorpii": "sco", "sculptoris": "scl",
    "scuti": "sct", "serpentis": "ser", "sextantis": "sex", "tauri": "tau",
    "telescopii": "tel", "trianguli": "tri", "trianguliaustralis": "tra", "tucanae": "tuc",
    "ursaemajoris": "uma", "ursaeminoris": "umi", "velorum": "vel", "virginis": "vir",
    "volantis": "vol", "vulpeculae": "vul",
}

_SHORT_TO_LONG = {
    **{v: k for k, v in CONSTELLATION_LONG_TO_SHORT.items()},
    **{v: k for k, v in GREEK_LONG_TO_SHORT.items()},
}
_LONG_TO_SHORT = {**CONSTELLATION_LONG_TO_SHORT, **GREEK_LONG_TO_SHORT}

MAX_SURFACED_PER_DAY = 3
MAX_PLANETS_PER_ITEM = 3       # more than this and it's a catalogue paper, not a story
SUPPRESS_DAYS = 30             # paper, press release and aggregator are one story, thrice
MAX_AGE_DAYS = 7               # a three-week-old press release is not a newsjack
MAX_ITEMS_PER_FEED = 60        # aasnova serves 600; we only ever want the recent end


# --------------------------------------------------------------------------
# normalisation + alias table
# --------------------------------------------------------------------------

def normalise(text: str) -> str:
    """Lowercase, strip accents, drop every space, hyphen, underscore and dot.

    This is the whole matching trick: `TRAPPIST-1e`, `TRAPPIST-1 e` and `Trappist 1 e` all
    collapse to `trappist1e`, so the press's spelling and the Archive's become the same
    string. A regex over designations is where this tool would die instead.
    """
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[\s\-_.'’‐-―]+", "", t)
    return t


# A designation shorter than this is not safe to match in prose. Empirically the shortest
# real form in the Archive is 5 characters (`futau`, `muleo`, `pztel`), and NONE of the 355
# digit-free forms collides with a 234k-entry system dictionary — checked 2026-08-05. So a
# digit is NOT required, and requiring one (the obvious first guard) silently discards every
# Greek-letter and variable-star planet: bet Pic b, AU Mic b, eps Eri b, Barnard b.
MIN_ALIAS_LEN = 5


def _english_words() -> set[str]:
    """The system word list, if there is one — used to drop any alias that is also an
    ordinary English word. Empty on hosts without it (Linux CI); the check then no-ops
    and `build_aliases` says so rather than pretending it ran."""
    for p in (Path("/usr/share/dict/words"), Path("/usr/dict/words")):
        if p.exists():
            return {line.strip().lower() for line in p.read_text().splitlines()}
    return set()


def _expand_word_forms(name: str) -> set[str]:
    """Normalised spellings of one Archive name that the press might plausibly use.

    Both directions matter and only one is obvious. The Archive stores `51 Peg b` and
    `bet Pic b`; the press prints `51 Pegasi b` and `beta Pictoris b`. Expanding only
    long->short (the first thing you write) matches nothing, because the input we hold is
    already short. So every word contributes its own variants and we take the product.
    """
    words = name.lower().split()
    per_word: list[list[str]] = []
    for w in words:
        key = re.sub(r"[^a-z]", "", w)
        variants = [w]
        if key and key in _LONG_TO_SHORT:
            variants.append(w.replace(key, _LONG_TO_SHORT[key]))
        if key and key in _SHORT_TO_LONG:
            variants.append(w.replace(key, _SHORT_TO_LONG[key]))
        per_word.append(list(dict.fromkeys(variants)))

    forms: set[str] = set()
    combos: list[list[str]] = [[]]
    for variants in per_word:
        if len(combos) * len(variants) > 32:       # runaway guard; names are 2–4 words
            combos = [c + [variants[0]] for c in combos]
            continue
        combos = [c + [v] for c in combos for v in variants]
    for combo in combos:
        forms.add(normalise(" ".join(combo)))

    n = normalise(name)
    for long, short in PREFIX_SYNONYMS:
        if n.startswith(short) and long != short:
            forms.add(long + n[len(short):])
        if n.startswith(long) and long != short:
            forms.add(short + n[len(long):])
    return {f for f in forms if f}


def _tap(query: str, *, timeout: int = 180) -> list[dict]:
    params = urllib.parse.urlencode(
        {"request": "doQuery", "lang": "ADQL", "format": "json", "query": query}
    )
    req = urllib.request.Request(f"{TAP}?{params}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted host)
        return json.loads(resp.read().decode())


def build_aliases(*, verbose: bool = True) -> dict:
    """One TAP pull -> the normalised name lookup.

    Pulls `pl_name`, `hostname`, `pl_letter` and the cross-catalogue ids (`hd_name`,
    `hip_name`, `tic_id`) from `pscomppars`. Note `gaia_id` is NOT a pscomppars column
    (TAP returns HTTP 400) — checked 2026-08-05, don't add it back.
    """
    if verbose:
        print("Pulling names from pscomppars …", file=sys.stderr)
    rows = _tap(
        "select pl_name,hostname,pl_letter,hd_name,hip_name,tic_id from pscomppars"
    )
    planets: dict[str, str] = {}   # normalised form -> canonical pl_name
    hosts: dict[str, str] = {}     # normalised form -> hostname
    ambiguous: set[str] = set()

    def add(table: dict[str, str], key: str, value: str) -> None:
        if len(key) < MIN_ALIAS_LEN:
            return
        prior = table.get(key)
        if prior is not None and prior != value:
            ambiguous.add(key)
            return
        table[key] = value

    for r in rows:
        pl = r.get("pl_name")
        host = r.get("hostname")
        letter = (r.get("pl_letter") or "").strip()
        if pl:
            for f in _expand_word_forms(pl):
                add(planets, f, pl)
        if host:
            for f in _expand_word_forms(host):
                add(hosts, f, host)
            # Cross-catalogue ids, with the planet letter appended so "HD 189733b" resolves
            # to the planet and bare "HD 189733" resolves to the host.
            for col in ("hd_name", "hip_name", "tic_id"):
                alt = r.get(col)
                if not alt:
                    continue
                for f in _expand_word_forms(alt):
                    add(hosts, f, host)
                    if letter and pl:
                        add(planets, f + letter.lower(), pl)

    for k in ambiguous:
        planets.pop(k, None)
        hosts.pop(k, None)

    # Anything that is also an ordinary English word would fire on prose forever.
    dictionary = _english_words()
    collisions = sorted((set(planets) | set(hosts)) & dictionary)
    for k in collisions:
        planets.pop(k, None)
        hosts.pop(k, None)

    for alias, target in HAND_ALIASES.items():
        planets[normalise(alias)] = target

    table = {
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source": "NASA Exoplanet Archive pscomppars via TAP",
        "n_rows": len(rows),
        "planets": planets,
        "hosts": hosts,
        "dropped_ambiguous": sorted(ambiguous)[:200],
        "dropped_dictionary_words": collisions,
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    ALIAS_FILE.write_text(json.dumps(table, indent=1, sort_keys=True))
    if verbose:
        dict_note = (
            f"{len(collisions)} English-word collisions dropped" if dictionary
            else "NO system word list on this host — the English-word guard did NOT run"
        )
        print(
            f"Wrote {ALIAS_FILE.relative_to(REPO)}: {len(rows)} Archive rows -> "
            f"{len(planets)} planet spellings, {len(hosts)} host spellings "
            f"({len(ambiguous)} ambiguous forms dropped, {dict_note}).",
            file=sys.stderr,
        )
    return table


def load_aliases(*, allow_build: bool = True) -> dict:
    if ALIAS_FILE.exists():
        return json.loads(ALIAS_FILE.read_text())
    if not allow_build:
        sys.exit(
            f"No alias table at {ALIAS_FILE.relative_to(REPO)}.\n"
            f"Build it with:  python3 tools/newswatch.py aliases"
        )
    return build_aliases()


_WORD = re.compile(r"[A-Za-z0-9+][A-Za-z0-9+\-]*")


def find_planets(text: str, aliases: dict) -> tuple[list[str], list[str]]:
    """Return (planet pl_names, host names) mentioned in `text`.

    Slides a 1–4 word window over the text and looks the normalised join up in the table.
    Sixty lookups on a headline; exact, and no regex to get wrong.
    """
    words = _WORD.findall(text)
    pl_tab, host_tab = aliases["planets"], aliases["hosts"]
    found_pl: dict[str, None] = {}
    found_host: dict[str, None] = {}
    matched_spans: set[int] = set()

    for size in (4, 3, 2, 1):           # longest first: "TRAPPIST 1 e" beats "TRAPPIST 1"
        for i in range(len(words) - size + 1):
            if any(j in matched_spans for j in range(i, i + size)):
                continue
            key = normalise("".join(words[i:i + size]))
            if key in pl_tab:
                found_pl.setdefault(pl_tab[key], None)
                matched_spans.update(range(i, i + size))
            elif key in host_tab:
                found_host.setdefault(host_tab[key], None)
                matched_spans.update(range(i, i + size))
    return list(found_pl), list(found_host)


# --------------------------------------------------------------------------
# feeds
# --------------------------------------------------------------------------

ARXIV_NS = "{http://arxiv.org/schemas/atom}"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


@dataclass
class Item:
    feed: Feed
    uid: str
    title: str
    link: str
    summary: str
    published: datetime | None
    announce_type: str | None = None
    planets: list[str] = field(default_factory=list)
    hosts: list[str] = field(default_factory=list)
    score: int = 0
    reasons: list[str] = field(default_factory=list)


def _text(el, *tags: str) -> str:
    for t in tags:
        found = el.find(t)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def fetch_feed(feed: Feed, *, fixture: Path | None, timeout: int = 45) -> bytes:
    if fixture is not None:
        path = fixture / f"{feed.id}.xml"
        if not path.exists():
            raise FileNotFoundError(f"fixture missing: {path}")
        return path.read_bytes()
    req = urllib.request.Request(feed.url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (pinned feeds)
        return resp.read()


def trim_feed(body: bytes, keep: int) -> bytes:
    """Keep the first `keep` entries and drop the rest, in place.

    So the parsing tests can be a committed fixture that CI actually runs. A raw snapshot is
    4.4 MB — AAS Nova alone serves 600 items of full post HTML — which is not something to
    put in the repo, and the alternative (gitignore it) leaves eight tests permanently
    skipped, which is worse than not having them.
    """
    root = ET.fromstring(body)
    for parent in root.iter():
        children = [c for c in parent if c.tag in ("item", f"{ATOM_NS}entry")]
        for extra in children[keep:]:
            parent.remove(extra)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def parse_feed(feed: Feed, body: bytes) -> list[Item]:
    root = ET.fromstring(body)
    nodes = root.findall(".//item") or root.findall(f".//{ATOM_NS}entry")
    items: list[Item] = []
    for node in nodes[:MAX_ITEMS_PER_FEED]:
        title = _text(node, "title", f"{ATOM_NS}title")
        link = _text(node, "link", f"{ATOM_NS}id")
        if not link:
            le = node.find(f"{ATOM_NS}link")
            link = le.get("href", "") if le is not None else ""
        summary = _text(node, "description", "summary", f"{ATOM_NS}summary")
        summary = re.sub(r"<[^>]+>", " ", summary)
        summary = re.sub(r"\s+", " ", summary).strip()
        uid = _text(node, "guid", f"{ATOM_NS}id") or link or title
        raw_date = _text(node, "pubDate", "published", "updated", f"{ATOM_NS}published")
        published = None
        if raw_date:
            try:
                published = parsedate_to_datetime(raw_date)
            except (TypeError, ValueError):
                try:
                    published = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except ValueError:
                    published = None
        if published is not None and published.tzinfo is None:
            published = published.replace(tzinfo=UTC)
        at = node.find(f"{ARXIV_NS}announce_type")
        items.append(Item(
            feed=feed, uid=uid, title=title, link=link, summary=summary,
            published=published,
            announce_type=at.text.strip() if at is not None and at.text else None,
        ))
    return items


def collect_items(
    *, fixture: Path | None, only: set[str] | None = None
) -> tuple[list[Item], list[str]]:
    items: list[Item] = []
    errors: list[str] = []
    for feed in FEEDS:
        if only and feed.id not in only:
            continue
        try:
            items.extend(parse_feed(feed, fetch_feed(feed, fixture=fixture)))
        except (urllib.error.URLError, ET.ParseError, FileNotFoundError,
                TimeoutError, OSError) as e:
            errors.append(f"{feed.id}: {type(e).__name__}: {e}")
    return items, errors


# --------------------------------------------------------------------------
# state (seen ids + 30-day per-planet suppression + missed-day detection)
# --------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen": {}, "planet_last_surfaced": {}, "last_poll": None}


def save_state(state: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cutoff = (datetime.now(UTC) - timedelta(days=120)).isoformat()
    state["seen"] = {k: v for k, v in state["seen"].items() if v >= cutoff}
    STATE_FILE.write_text(json.dumps(state, indent=1, sort_keys=True))


# --------------------------------------------------------------------------
# ranking
# --------------------------------------------------------------------------

def score_item(item: Item, catalogue: dict) -> None:
    """Rank per 01-newsjacking.md: press presence, one named planet, in our catalogue,
    travel-noun. Press presence first — it is the best single predictor a story travels."""
    s, why = 0, []
    if item.feed.kind == "press":
        s += 40
        why.append("press release (a big press office is behind it)")
    elif item.feed.kind == "editorial":
        s += 25
        why.append("editorially chosen (AAS Nova)")
    elif item.feed.kind == "aggregator":
        s += 20
        why.append("aggregator picked it up — Reddit is usually next")
    else:
        s += 5
        why.append("preprint only — stock, not news (see the lead-time note)")

    title_planets, _ = find_planets(item.title, _ALIASES)
    if len(title_planets) == 1:
        s += 25
        why.append(f"exactly one planet named in the title ({title_planets[0]})")
    elif len(title_planets) > 1:
        s += 5
        why.append(f"{len(title_planets)} planets in the title")

    in_cat = [p for p in item.planets if p in catalogue]
    if in_cat:
        s += 20
        why.append(f"in our catalogue: {', '.join(in_cat[:3])}")
    elif item.planets:
        s += 10
        why.append("NOT in our catalogue — a data task, and the most valuable output here")

    nouns = [n for n in TRAVEL_NOUNS if n in item.title.lower()]
    if nouns:
        s += 10 + 2 * len(nouns)
        why.append(f"travel-noun in the title: {', '.join(nouns[:4])}")

    item.score, item.reasons = s, why


def rank(
    items: list[Item], catalogue: Catalogue, state: dict, *, now: datetime,
    max_age_days: int = MAX_AGE_DAYS,
) -> tuple[list[Item], dict[str, int]]:
    """Filter hard, then rank. The counts are returned so the run can say what it dropped —
    a silent cap reads as 'nothing else happened', which is a lie."""
    dropped = {"seen": 0, "stale": 0, "replace": 0, "no_planet": 0,
               "too_many_planets": 0, "suppressed": 0}
    kept: list[Item] = []
    suppress_cutoff = now - timedelta(days=SUPPRESS_DAYS)
    age_cutoff = now - timedelta(days=max_age_days)

    for it in items:
        if it.uid in state["seen"]:
            dropped["seen"] += 1
            continue
        if it.published is not None and it.published < age_cutoff:
            # Feeds do not all move at the same speed. ESO's holds ten items and can serve a
            # three-week-old release as its newest; without this the tool confidently ranks
            # stale news top, which is the opposite of the job. Undated items are kept — every
            # feed we poll dates its items, so an undated one is a parsing surprise, not a
            # deliberate omission, and silently dropping it would hide the bug.
            dropped["stale"] += 1
            continue
        if it.announce_type == "replace":
            # Without this every v2 of a preprint re-alerts on the same planet forever.
            dropped["replace"] += 1
            continue
        it.planets, it.hosts = find_planets(f"{it.title} {it.summary}", _ALIASES)
        if not it.planets and not it.hosts:
            dropped["no_planet"] += 1
            continue
        if len(it.planets) > MAX_PLANETS_PER_ITEM:
            # A TOI catalogue paper is not a news story.
            dropped["too_many_planets"] += 1
            continue
        recent = False
        for p in it.planets:
            last = state["planet_last_surfaced"].get(p)
            if last and datetime.fromisoformat(last) > suppress_cutoff:
                recent = True
        if recent:
            dropped["suppressed"] += 1
            continue
        score_item(it, catalogue)
        kept.append(it)

    kept.sort(key=lambda i: (-i.score, i.published or datetime.min.replace(tzinfo=UTC)))
    return kept, dropped


# --------------------------------------------------------------------------
# the catalogue
# --------------------------------------------------------------------------

def slug(name: str) -> str:
    """The same slug `pipeline/catalog.py` applies to an Archive `pl_name` to make a record id."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


class Catalogue:
    """Lookup by whatever spelling you hold.

    The trap this exists for: records are keyed by the *display* name, which expands the
    Archive's abbreviations — `bet Pic b` is stored as `beta Pictoris b`. The alias table
    returns Archive `pl_name`s. Joining those two by string equality silently reports
    cataloguued planets as missing, which is the one output of this tool nobody would
    double-check. So the join goes through the id slug, exactly as roman_board.py joins
    the target board: by an explicit id, never by slugging a display name.
    """

    def __init__(self, records: list[dict]) -> None:
        self.records = records
        self._by_id = {r["id"]: r for r in records}
        self._by_name = {r["name"]: r for r in records}

    def get(self, name: str) -> dict | None:
        return self._by_id.get(slug(name)) or self._by_name.get(name)

    def __contains__(self, name: str) -> bool:
        return self.get(name) is not None

    def __len__(self) -> int:
        return len(self.records)

    def by_id(self, pid: str) -> dict | None:
        return self._by_id.get(pid)

    def by_host(self, hostname: str) -> dict | None:
        return next((r for r in self.records
                     if slug(r["host_star"]["name"] or "") == slug(hostname)), None)


def load_catalogue(path: Path | None = None) -> tuple[dict, Catalogue]:
    path = path or PLANETS
    if not path.exists():
        sys.exit(
            f"{path} is missing — it ships as a GitHub Release asset, not in the repo.\n"
            f"Fetch it first:\n"
            f"    python3 scripts/fetch_data.py\n"
            f"(release tag: {release_tag()})"
        )
    doc = json.loads(path.read_text())
    return doc, Catalogue(doc["planets"])


def release_tag() -> str:
    return RELEASE_FILE.read_text().strip() if RELEASE_FILE.exists() else "unknown"


def roman_is_stale(rec: dict) -> tuple[bool, str]:
    """Is this record's Roman view built from the flight band configuration?

    The single most dangerous number this tool can print. `pipeline/config.py` was corrected
    to the three flight bands (575/10%, 730/15%, 825/10%); every shipped release before that
    correction carries four bands including a 660 and an 835 that trace to no primary source.
    Publishing 'as Roman would see it' against a wrong band model, to an audience that
    contains the CGI team, is the one unrecoverable error available to this project.
    """
    views = rec.get("instrument_views") or []
    if not views:
        return True, "no Roman view in this record"
    got = tuple(s["band_id"] for s in views[0]["band_samples"]["samples"])
    if got != FLIGHT_BANDS:
        return True, f"data has {'/'.join(got)}; flight config is {'/'.join(FLIGHT_BANDS)}"
    return False, ""


# --------------------------------------------------------------------------
# plain-English colour naming (for alt text — a blind reader must get the finding,
# and the finding IS the colour)
# --------------------------------------------------------------------------

_HUES = (
    (15, "red"), (40, "orange"), (65, "yellow"), (90, "yellow-green"), (150, "green"),
    (185, "teal"), (210, "cyan-blue"), (250, "blue"), (280, "violet"), (320, "magenta"),
    (360, "red"),
)


def colour_name(hex_str: str) -> str:
    r, g, b = (int(hex_str[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, light, sat = colorsys.rgb_to_hls(r, g, b)
    deg = h * 360
    hue = next(name for bound, name in _HUES if deg <= bound)
    if sat < 0.08:
        base = "grey"
    elif sat < 0.22:
        base = f"muted {hue}"
    else:
        base = hue
    if light > 0.82:
        return f"very pale {base}"
    if light > 0.62:
        return f"pale {base}"
    if light < 0.2:
        return f"near-black {base}"
    if light < 0.38:
        return f"dark {base}"
    return base


# --------------------------------------------------------------------------
# the briefing
# --------------------------------------------------------------------------

RULE = "─" * 78


def site_url(base: str) -> str:
    return base.rstrip("/") if base else "<SITE_URL>"


def utm(url: str, source: str, campaign: str) -> str:
    return f"{url}?utm_source={source}&utm_medium=newsjack&utm_campaign={campaign}"


STANDING_INFRARED = (
    "The standing infrared answer (write it once, reuse it — never improvise it at 23:40):\n"
    "  \"That measurement is infrared. It tells you what the atmosphere is MADE of, not what\n"
    "   the planet looks like — those are different wavelengths and different physics. Which\n"
    "   is the interesting part: composition is exactly what a visible-light albedo model\n"
    "   needs as input, so this result constrains the colour rather than reporting it.\"\n"
    "  Boundary to get right, or a scientist will correct you in public: optical SECONDARY-\n"
    "  ECLIPSE photometry (TESS, CHEOPS, Kepler) DOES constrain geometric albedo at ~0.6–0.8 µm.\n"
    "  \"Infrared tells us nothing about colour\" is true. \"Space telescopes tell us nothing\n"
    "  about colour\" is false."
)

CHECKLIST = (
    "1. Open the PAPER, not the press release. Copy out its radius, mass, T_eq, host T_eff.",
    "2. Diff those four against ours below. >10% radius/mass or >100 K on either temperature",
    "   => our swatch used superseded numbers. Post the CHANGE, not the swatch. Better story.",
    "3. Provenance flag goes in the POST TEXT, not just on the page.",
    "4. Say the release date out loud if it predates the paper.",
    "5. Name the assumption you trust least. Can't name one? You don't know this planet.",
    "6. State the wavelength the news is about (see the infrared paragraph above).",
    "7. Sleep-on-it triggers: contradicts the paper · says habitable/not habitable · names a",
    "   person. Those wait until morning. No exceptions, ever.",
    "8. Have the correction sentence written BEFORE you post (drafted for you below).",
)


def _wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, width=76, initial_indent=indent, subsequent_indent=indent)


def _fmt(value, unit: str = "", nd: int = 2) -> str:
    if value is None:
        return "— (missing)"
    if isinstance(value, float):
        return f"{value:,.{nd}f}{unit}"
    return f"{value}{unit}"


def brief_missing(name: str, out: list[str], base: str) -> None:
    """The commonest newsjack case: the planet in the news is not in our release."""
    out.append(RULE)
    out.append(f"  {name}  —  NOT IN OUR CATALOGUE")
    out.append(RULE)
    out.append("")
    out.append(_wrap(
        f"This release ({release_tag()}) is a dated offline snapshot, so newly confirmed "
        f"planets are missing by construction. This is the MAJORITY case on a "
        f"'new planet discovered' story, not an edge case."
    ))
    out.append("")
    out.append("  THE FIVE-MINUTE FIX — the one-planet fast path:")
    out.append(f'      uv run python -m pipeline build --planet "{name}" \\')
    out.append("          --out data/newsjack.json --no-cache")
    out.append(f'      python3 tools/newswatch.py brief "{name}" --planets data/newsjack.json')
    out.append("")
    out.append(_wrap(
        "If that fails for want of a radius, a mass or a host T_eff, the honest output is a "
        "post in itself: \"we can't compute a colour for this one yet, and here is exactly "
        "which number is missing.\" That beats a guess, and it beats silence."
    ))
    out.append("")


def brief_planet(rec: dict, out: list[str], base: str, *, headline: str | None = None,
                 source: str | None = None, link: str | None = None) -> None:
    pid = rec["id"]
    name = rec["name"]
    params = rec["params"]
    star = rec["host_star"]
    tc = rec["true_colour"]
    page = f"{site_url(base)}/planet/{pid}"
    stale, stale_why = roman_is_stale(rec)
    views = rec.get("instrument_views") or []
    roman = views[0] if views else None

    out.append(RULE)
    out.append(f"  {name}   {tc['hex']}   {colour_name(tc['hex'])}")
    out.append(RULE)
    if headline:
        out.append("")
        out.append("  WHY YOU ARE SEEING THIS")
        out.append(_wrap(headline, "    "))
        if source:
            out.append(f"    source : {source}")
        if link:
            out.append(f"    link   : {link}")

    # -- our numbers ------------------------------------------------------
    out.append("")
    built = rec["meta"]["generated_at"][:10]
    out.append(f"  OUR NUMBERS   (release {release_tag()}, built {built})")
    out.append(f"    page          {page}")
    out.append(f"    true colour   {tc['hex']}  — {colour_name(tc['hex'])}"
               f"  (confidence: {tc['confidence']})")
    out.append(f"    palette       {' '.join(s['hex'] for s in tc['palette'])}")
    out.append(f"    provenance    {rec['provenance']}"
               + ("" if rec.get("is_light_isolable", True)
                  else "   ⚠ MODEL-ONLY: no light from this planet has ever been received"))
    out.append(f"    luminance     Y={tc['luminance_y']:.3f} as computed; every base swatch is "
               f"normalised to Y=0.60 for display")
    if tc.get("out_of_gamut"):
        out.append("    ⚠ out of sRGB gamut — the swatch is a clamp, say so if you show it")

    if roman:
        de = roman["reconstruction_error"]["delta_e2000"]
        bands = "/".join(s["band_id"] for s in roman["band_samples"]["samples"])
        if stale:
            out.append("")
            out.append(f"    ⛔ ROMAN VIEW WITHHELD — {stale_why}")
            out.append(_wrap(
                "Do NOT publish an 'as Roman would see it' number from this release. Publishing "
                "it against a wrong band model, to an audience that contains the CGI team, is "
                "the one unrecoverable error available to this project. Re-emit the catalogue "
                "with the corrected config first.", "       "))
            out.append(f"       (for your eyes only: {roman['colour']['hex']}, ΔE2000 {de:.1f}, "
                       f"bands {bands})")
        else:
            out.append(f"    roman view    {roman['colour']['hex']}  ΔE2000 {de:.1f}  "
                       f"bands {bands}  ({roman['band_samples']['source']})")

    # -- the four numbers to diff ----------------------------------------
    src = params.get("sources", {})
    out.append("")
    out.append("  THE FOUR NUMBERS TO DIFF AGAINST THE PAPER"
               "   ← checklist step 2, 80% of the value")
    out.append(f"    radius        {_fmt(params.get('radius_r_earth'), ' R⊕')}"
               f"        [{src.get('radius_r_earth', '?')}]     tolerance ±10%")
    out.append(f"    mass          {_fmt(params.get('mass_m_earth'), ' M⊕')}"
               f"        [{src.get('mass_m_earth', '?')}]     tolerance ±10%")
    out.append(f"    T_eq          {_fmt(params.get('equilibrium_temp_k'), ' K', 0)}"
               f"          [{src.get('equilibrium_temp_k', '?')}]     tolerance ±100 K")
    out.append(f"    host T_eff    {_fmt(star.get('teff_k'), ' K', 0)}"
               f"          [{src.get('star_teff_k', '?')}]     tolerance ±100 K")
    out.append(f"    (also: a = {_fmt(params.get('semi_major_axis_au'), ' AU', 4)},  "
               f"d = {_fmt(params.get('distance_pc'), ' pc', 1)},  host {star.get('name')} "
               f"{star.get('spectral_type') or ''})")
    out.append("    Any one outside tolerance -> post the COLOUR CHANGE, not the swatch.")

    # -- assumptions ------------------------------------------------------
    out.append("")
    out.append("  ASSUMPTIONS   ← checklist step 5: name the one you trust least, in the post")
    out.append(f"    cloud state   {params.get('assumed_cloud_state')}   "
               f"[{src.get('cloud_state', '?')}]")
    out.append(f"    metallicity   {_fmt(params.get('assumed_metallicity'), '× solar', 1)}   "
               f"[{src.get('metallicity', '?')}]")
    out.append(f"    phase angle   {_fmt(params.get('assumed_phase_angle_deg'), '°', 0)}   "
               f"[{src.get('phase_angle_deg', '?')}]")
    out.append(f"    spectrum      {params.get('spectrum_source')} engine")
    assumed = [k for k, v in src.items() if v == "assumed"]
    if assumed:
        out.append(f"    -> the assumed (not measured) inputs here are: {', '.join(assumed)}")

    hab = rec.get("habitability")
    if hab and hab.get("is_candidate"):
        out.append("")
        out.append(f"  HABITABLE-ZONE LENS   zone={hab['zone']}  surface={hab['surface']}  "
                   f"insolation={hab['insolation_earth']:.2f}×Earth")
        for c in hab.get("caveats", [])[:2]:
            out.append(_wrap(c, "    "))
        out.append(_wrap(
            "If the story is a 'potentially habitable planet' story, this is where a quiet, "
            "well-sourced DISAGREEMENT with a hype cycle is the most shareable thing this "
            "project can produce. Only make that argument when you are certain.", "    "))

    obs = rec.get("real_observations") or []
    if obs:
        out.append("")
        out.append("  WE HAVE REAL OBSERVATIONS FOR THIS ONE — lead with that, it is the armour")
        for o in obs[:3]:
            out.append(f"    {o.get('telescope')} ({o.get('year')}): {o.get('band')} — "
                       f"{o.get('credit')}")

    sysd = rec.get("system") or {}
    if sysd.get("member_count", 0) > 1:
        sibs = ", ".join(s["name"] for s in sysd.get("siblings", [])[:6])
        out.append("")
        out.append(f"  SYSTEM   {sysd['hostname']} has {sysd['member_count']} "
                   f"known planets: {sibs}")
        out.append("    (a system story is a chance to post the whole family as one image)")


def brief_where(out: list[str], name: str, base: str, slug: str) -> None:
    q = urllib.parse.quote(name)
    out.append("")
    out.append("  WHERE TO GO — reply, don't post. This is the whole tactic.")
    out.append("    Tier 1, within ~2 hours (the only hard clock):")
    out.append(f"      Bluesky   https://bsky.app/search?q={q}")
    out.append("        -> reply to / quote-post the RESEARCHER or JOURNALIST who announced it.")
    out.append("           Astronomers engage back; this is how 13-credit-the-scientists starts.")
    out.append("    Tier 1b, same evening or next morning"
               " (threads form 6–18 h later, not at min 40):")
    out.append(f"      Reddit    https://www.reddit.com/search/?q={q}&sort=new")
    out.append(f"      r/space   https://www.reddit.com/r/space/search/?q={q}&restrict_sr=1&sort=new")
    out.append(f"      HN        https://hn.algolia.com/?query={q}&sort=byDate")
    out.append("        -> a comment on a 4-comment thread is worth nothing; on a climbing")
    out.append("           2-hour-old thread it is worth a lot. Check, don't rush.")
    out.append("    Tier 2: your own Bluesky + Mastodon post (home turf, costs nothing).")
    out.append("    Tier 3, within the week and NEVER in a hurry: the dated note on the planet")
    out.append(f"      page ({site_url(base)}/planet/{slug}). The only part still earning")
    out.append("      traffic in six months. Last thing to write, not first.")
    out.append("")
    out.append("    NEVER pitch a journalist about their own published story. Two standing")
    out.append("    exceptions they actively want: a CORRECTION (\"the radius in para 4 is the")
    out.append("    2023 value\"), and answering one who publicly asked what colour something is.")


def brief_copy(rec: dict, out: list[str], base: str) -> None:
    """Scaffolds, not copy. Every ⟨…⟩ is a blank you fill by hand."""
    pid, name = rec["id"], rec["name"]
    tc = rec["true_colour"]
    hexv, cname = tc["hex"], colour_name(tc["hex"])
    prov = rec["provenance"]
    honesty = {
        "measured-albedo": "Computed from a MEASURED spectrum — one of the few we can check.",
        "measured-cgi": "Built from real Roman coronagraph photometry.",
        "simulated-cgi": "Simulated Roman observation, not a measurement.",
        "model-microlensing": ("MODEL-ONLY, permanently: we have never received a single photon "
                               "from this planet."),
    }.get(prov, "Modelled, not photographed. No exoplanet has ever had its visible colour "
                "measured directly.")

    out.append("")
    out.append("  COPY SCAFFOLDS   ⟨angle brackets are YOUR words⟩")
    out.append(_wrap(
        "Deliberately not ready-to-post. A templated caption is the exact thing that kills the "
        "account (11-bluesky-mastodon.md) — the one sentence of physics is the only part of the "
        "post with any value, and it has to be yours. Everything else is filled in.", "    "))

    bsky_url = utm(f"{site_url(base)}/planet/{pid}", "bluesky", pid)
    fixed = (f"{name} is {cname} ({hexv}). ⟨⟩ {honesty} " + bsky_url + " 🔭 #exoplanet")
    budget = 300 - len(fixed) + 2
    out.append("")
    out.append(f"  ── Bluesky (300 graphemes; you have ~{budget} for the physics sentence) ──")
    out.append(f"    {name} is {cname} ({hexv}).")
    out.append("    ⟨ONE sentence of physics — why THIS colour. Not a summary of the news:")
    out.append("      'why is this one blue' beats 'scientists discover'.⟩")
    out.append(f"    {honesty}")
    out.append(f"    {bsky_url} 🔭 #exoplanet #astronomy")
    out.append("    Attach the 1200×1200 disc image. A post cannot have both an image and a")
    out.append("    link card, and the image is the product — so the URL sits as plain text.")

    out.append("")
    out.append("  ── Mastodon (500; same body, room to breathe. Post unlisted if automated) ──")
    out.append(f"    Same as above + ⟨one extra clause on the assumption you trust least⟩ + "
               f"{utm(f'{site_url(base)}/planet/{pid}', 'mastodon', pid)}")

    out.append("")
    out.append("  ── Alt text (~250 chars; a blind reader must get the FINDING, and the")
    out.append("     finding IS the colour. Never write 'image of a planet') ──")
    out.append(_wrap(
        f"A rendered disc of {name}, coloured {cname} ({hexv}), on a dark background. "
        f"⟨one clause on the visible feature — e.g. 'the disc is uniformly lit with no "
        f"banding'⟩. The colour is computed from a model albedo spectrum, not photographed.",
        "    "))

    out.append("")
    out.append("  ── Reddit / HN comment (top-level, in the thread that already exists) ──")
    out.append(_wrap(
        f"⟨Lead with the caveat — if your first job is saying what the model can't do, nobody "
        f"minds the link.⟩ If you're curious what {name} would actually look like: {hexv}, "
        f"{cname}, computed from its albedo model times the host star's spectrum, through the "
        f"CIE 1931 colour-matching functions. ⟨the one physics sentence⟩ {honesty} "
        f"Assumptions (cloud state, metallicity, phase angle) are on the page: "
        f"{utm(f'{site_url(base)}/planet/{pid}', 'reddit', pid)}. Corrections welcome — "
        f"particularly on the cloud-deck assumption.", "    "))
    out.append("    One link. No pitch. Do this only with a real comment history (10-reddit.md).")

    out.append("")
    out.append("  ── Planet-page dated note (Tier 3 — write this LAST, within the week) ──")
    out.append(_wrap(
        f"In the news, {datetime.now(UTC):%-d %b %Y}: ⟨the result, one sentence⟩. ⟨What that "
        f"does or does not change about the colour we compute — including 'nothing, because "
        f"the measurement is infrared', if that is the honest answer.⟩", "    "))

    out.append("")
    out.append("  ── The correction, pre-written (checklist 8 — a wire desk's speed comes from")
    out.append("     the retraction path existing in advance, not from being sure) ──")
    out.append(_wrap(
        f"I got {name} wrong above: ⟨what⟩. The corrected value is ⟨x⟩, from ⟨source⟩. The "
        f"page is updated.", "    "))

    out.append("")
    out.append("  ── The standing counter-story (one link, no new claims, no new risk) ──")
    out.append(_wrap(
        "The picture on that article is an artist's impression. This one is computed from "
        "physics, and the site tells you exactly where the model ends and the measurement "
        "begins.", "    "))


def render_brief(rec: dict | None, name: str, base: str, *, headline: str | None = None,
                 source: str | None = None, link: str | None = None,
                 with_checklist: bool = True) -> str:
    out: list[str] = []
    if rec is None:
        brief_missing(name, out, base)
        out.append(RULE)
        return "\n".join(out)
    brief_planet(rec, out, base, headline=headline, source=source, link=link)
    brief_where(out, rec["name"], base, rec["id"])
    brief_copy(rec, out, base)
    if with_checklist:
        out.append("")
        out.append("  ACCURACY CHECKLIST — five minutes, every time, no exceptions")
        for line in CHECKLIST:
            out.append(f"    {line}")
        out.append("")
        for line in STANDING_INFRARED.splitlines():
            out.append(f"  {line}")
        out.append("")
        out.append("  Then set a 24-hour reminder to re-check the Archive for this planet.")
        out.append("  If our colour moves, update the page AND reply to your own post. That one")
        out.append("  habit converts the biggest risk here into the most credible thing we do.")
    out.append("")
    out.append(RULE)
    return "\n".join(out)


# --------------------------------------------------------------------------
# log
# --------------------------------------------------------------------------

def log_path(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    notes = REPO / "docs" / "notes" / "marketing"
    if notes.exists():
        return notes / "newsjack-log.md"
    return REPO / "docs" / "marketing" / "newsjack-log.md"


def append_log(path: Path, items: list[Item], catalogue: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# Newsjack log\n\n"
            "Appended by `tools/newswatch.py poll`, so the tracking is a side effect of the\n"
            "tool rather than a discipline anyone has to maintain. Fill the last two columns\n"
            "by hand after the event — the metric is NOT visits, it is the fraction who open\n"
            "a SECOND planet page (99-tracking.md).\n\n"
            "| date | planet | headline | source | in catalogue | posted? "
            "| sessions | 2nd-page % |\n"
            "|---|---|---|---|---|---|---|---|\n"
        )
    rows = []
    for it in items:
        planet = it.planets[0] if it.planets else (it.hosts[0] if it.hosts else "—")
        in_cat = "yes" if planet in catalogue else "**NO — data task**"
        title = it.title.replace("|", "\\|")[:110]
        rows.append(
            f"| {datetime.now(UTC):%Y-%m-%d} | {planet} | [{title}]({it.link}) | "
            f"{it.feed.id} | {in_cat} | | | |"
        )
    if rows:
        with path.open("a") as fh:
            fh.write("\n".join(rows) + "\n")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

_ALIASES: dict = {"planets": {}, "hosts": {}}


def cmd_feeds(args: argparse.Namespace) -> None:
    save = Path(args.save_fixture) if args.save_fixture else None
    if save:
        save.mkdir(parents=True, exist_ok=True)
    ok = True
    for feed in FEEDS:
        try:
            body = fetch_feed(feed, fixture=None)
            items = parse_feed(feed, body)
            newest = max((i.published for i in items if i.published), default=None)
            age = f"newest {(datetime.now(UTC) - newest).days}d old" if newest else "no dates"
            print(f"  ok    {feed.id:14} {feed.kind:11} {len(items):3} items  {age}")
            if save:
                (save / f"{feed.id}.xml").write_bytes(
                    body if args.trim <= 0 else trim_feed(body, args.trim)
                )
        except Exception as e:  # noqa: BLE001 — a health check reports, never raises
            ok = False
            print(f"  FAIL  {feed.id:14} {feed.kind:11} {type(e).__name__}: {str(e)[:60]}")
    if save:
        print(f"\nSnapshotted to {save} — replay with:  poll --fixture {save}")
    print("\nNo feed exists for these; check them by hand:")
    for name, note in MANUAL_SOURCES:
        print(f"  · {name}\n      {note}")
    print("\nSkip Google Alerts: slow, noisy, always behind the sources above.")
    sys.exit(0 if ok else 1)


def cmd_aliases(args: argparse.Namespace) -> None:
    t = build_aliases()
    for probe in ("K2-18b", "TRAPPIST-1e", "HD189733b", "Gliese 1214 b", "51 Pegasi b",
                  "beta Pictoris b", "Osiris", "TOI-700 d"):
        pl, ho = find_planets(probe, t)
        print(f"  {probe:22} -> planets={pl or '—'}  hosts={ho or '—'}")


def cmd_poll(args: argparse.Namespace) -> None:
    global _ALIASES
    _ALIASES = load_aliases()
    _, catalogue = load_catalogue()
    state = load_state()
    now = datetime.now(UTC)

    last = state.get("last_poll")
    if last:
        gap = now - datetime.fromisoformat(last)
        if gap > timedelta(days=1, hours=6):
            print(f"⚠  LAST POLL WAS {gap.days}d {gap.seconds // 3600}h AGO. The arXiv feed "
                  f"carries ONE day of items and regenerates at midnight ET —\n"
                  f"   {gap.days} day(s) of preprints are gone and cannot be recovered from "
                  f"the feed.\n")

    fixture = Path(args.fixture) if args.fixture else None
    items, errors = collect_items(fixture=fixture)
    for e in errors:
        print(f"⚠  feed error — {e}")
    kept, dropped = rank(items, catalogue, state, now=now, max_age_days=args.max_age_days)

    surfaced = kept[:MAX_SURFACED_PER_DAY]
    print(f"{len(items)} items polled · {len(kept)} passed the filters · "
          f"showing the top {len(surfaced)} (hard cap {MAX_SURFACED_PER_DAY})")
    print("dropped: " + ", ".join(f"{v} {k}" for k, v in dropped.items() if v))
    if len(kept) > len(surfaced):
        overflow = REPO / "data" / "cache" / "newswatch-overflow.json"
        overflow.write_text(json.dumps(
            [{"title": i.title, "link": i.link, "feed": i.feed.id, "score": i.score,
              "planets": i.planets} for i in kept[len(surfaced):]], indent=1))
        print(f"the other {len(kept) - len(surfaced)} went to "
              f"{overflow.relative_to(REPO)} (a silent cap would read as 'nothing else "
              f"happened', which is a lie)")
    print()

    misses = [p for i in kept for p in i.planets if p not in catalogue]
    if misses:
        print("⚠  IN THE NEWS AND NOT IN OUR CATALOGUE — this is a data task, and the most")
        print(f"   valuable line this tool prints: {', '.join(sorted(set(misses))[:10])}")
        print()

    for it in surfaced:
        target = next((p for p in it.planets if p in catalogue), None) or \
            (it.planets[0] if it.planets else None)
        if target is None and it.hosts:
            sibling = catalogue.by_host(it.hosts[0])
            target = sibling["name"] if sibling else None
        why = f"score {it.score}: " + "; ".join(it.reasons)
        print(render_brief(
            catalogue.get(target) if target else None,
            target or (it.hosts[0] if it.hosts else "unknown"),
            args.base_url,
            headline=f"{it.title}\n\n{why}",
            source=f"{it.feed.name} ({it.feed.kind})",
            link=it.link,
        ))
        print()

    if not args.dry_run:
        for it in items:
            state["seen"][it.uid] = now.isoformat()
        for it in surfaced:
            for p in it.planets:
                state["planet_last_surfaced"][p] = now.isoformat()
        state["last_poll"] = now.isoformat()
        save_state(state)
        path = log_path(Path(args.log) if args.log else None)
        append_log(path, surfaced, catalogue)
        print(f"Logged {len(surfaced)} to {path}")
    else:
        print("--dry-run: state not advanced, nothing logged. Re-run gives the same answer.")


def cmd_brief(args: argparse.Namespace) -> None:
    global _ALIASES
    _, catalogue = load_catalogue(Path(args.planets) if args.planets else None)
    name = args.name
    rec = catalogue.get(name)
    if rec is None:
        # Try the alias table so "K2-18b" and "Gliese 1214 b" resolve.
        _ALIASES = load_aliases()
        pl, _ = find_planets(name, _ALIASES)
        if pl:
            rec = catalogue.get(pl[0])
            name = pl[0]
    print(render_brief(rec, name, args.base_url, with_checklist=not args.no_checklist))


def cmd_bench(args: argparse.Namespace) -> None:
    _, catalogue = load_catalogue()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    names = list(BENCH)
    targets = REPO / "data" / "roman-targets.json"
    if targets.exists():
        for t in json.loads(targets.read_text()).get("targets", []):
            cid = t.get("catalog_id")
            if cid:
                # Join by the EXPLICIT catalog_id, never by slugging the display name —
                # data/roman-targets.json says why: "pi Men b" is "HD 39091 b" in the Archive.
                rec = catalogue.by_id(cid)
                if rec and rec["name"] not in names:
                    names.append(rec["name"])
    written, missing = 0, []
    for name in names:
        rec = catalogue.get(name)
        if rec is None:
            missing.append(name)
            continue
        (outdir / f"{rec['id']}.md").write_text(
            f"# Newsjack bench — {rec['name']}\n\n"
            f"Written in daylight, with the checklist done, so a jack is a five-minute\n"
            f"publish instead of a sixty-minute scramble. Re-generate after every data\n"
            f"release: `python3 tools/newswatch.py bench`\n\n```\n"
            + render_brief(rec, rec["name"], args.base_url) + "\n```\n"
        )
        written += 1
    print(f"Wrote {written} bench briefings to {outdir}")
    if missing:
        print(f"NOT in this release ({release_tag()}): {', '.join(missing)}")
        print("  Each one is a gap on a planet that reliably makes headlines. Fix with the")
        print('  one-planet fast path: uv run python -m pipeline build --planet "<name>"')


def cmd_log(args: argparse.Namespace) -> None:
    path = log_path(Path(args.log) if args.log else None)
    if not path.exists():
        print(f"No log yet at {path}. It is created on the first `poll`.")
        return
    print(path.read_text())


def main() -> None:
    p = argparse.ArgumentParser(prog="newswatch", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    base_default = os.environ.get("SITE_BASE_URL", "")
    sub = p.add_subparsers(required=True)

    f = sub.add_parser("feeds", help="Check every source resolves; optionally snapshot them")
    f.add_argument("--save-fixture", metavar="DIR",
                   help="Write each feed's XML to DIR for offline replay")
    f.add_argument("--trim", type=int, default=8, metavar="N",
                   help="Keep only the first N entries per saved feed (0 = whole feed). "
                        "The default keeps the committed fixture small enough for CI.")
    f.set_defaults(func=cmd_feeds)

    a = sub.add_parser("aliases", help="Build the name lookup from the Archive (run weekly)")
    a.set_defaults(func=cmd_aliases)

    po = sub.add_parser("poll", help="Poll, rank, print at most 3 briefings")
    po.add_argument("--fixture", metavar="DIR", help="Replay saved feeds instead of the network")
    po.add_argument("--dry-run", action="store_true",
                    help="Don't advance state or log — re-running gives the same answer")
    po.add_argument("--log", metavar="PATH", help="Newsjack log path")
    po.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS, metavar="N",
                    help=f"Ignore items published more than N days ago (default {MAX_AGE_DAYS}). "
                         f"Feeds move at very different speeds — ESO's holds ten items and can "
                         f"serve a three-week-old release as its newest.")
    po.add_argument("--base-url", default=base_default, help="Site origin (or $SITE_BASE_URL)")
    po.set_defaults(func=cmd_poll)

    b = sub.add_parser("brief", help="Briefing for one planet, on demand")
    b.add_argument("name")
    b.add_argument("--planets", metavar="PATH", help="Alternative planets.json (fast-path output)")
    b.add_argument("--base-url", default=base_default)
    b.add_argument("--no-checklist", action="store_true")
    b.set_defaults(func=cmd_brief)

    be = sub.add_parser("bench", help="Pre-write the ~20 briefings that cover most headlines")
    be.add_argument("--out", default="docs/marketing/bench", metavar="DIR")
    be.add_argument("--base-url", default=base_default)
    be.set_defaults(func=cmd_bench)

    lg = sub.add_parser("log", help="Show the newsjack log")
    lg.add_argument("--log", metavar="PATH")
    lg.set_defaults(func=cmd_log)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
