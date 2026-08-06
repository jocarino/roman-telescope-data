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
    notify    Send a test message, to prove the Telegram channel works.
    log       Show the newsjack log.

Testing it without waiting for news
    python3 tools/newswatch.py brief "K2-18 b"          # the whole output, right now
    python3 tools/newswatch.py feeds --save-fixture tests/fixtures/feeds
    python3 tools/newswatch.py poll --fixture tests/fixtures/feeds --dry-run

Unattended (see .github/workflows/newswatch.yml)
    poll --notify --quiet     push to Telegram; keep the briefing OUT of the public log

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

# Words a non-astronomer already owns. Question one of "will it travel" — stories travel on
# these, not on results. Superlatives earn their place beside the nouns: "faintest planet ever
# imaged" is a civilian hook doing exactly the same work as "nearest", and an earlier version
# of this list scored that headline 0 for lack of one.
TRAVEL_NOUNS = (
    "earth-like", "earthlike", "habitable", "life", "biosignature", "nearest", "closest",
    "first", "water", "ocean", "diamond", "rain", "seven planets", "twin", "super-earth",
    "atmosphere", "clouds", "colour", "color", "blue", "goldilocks", "alien", "signs of",
    "faintest", "smallest", "largest", "biggest", "oldest", "youngest", "brightest",
    "darkest", "hottest", "coldest", "fastest", "strangest", "ever seen", "ever imaged",
)

# The flight configuration of Roman's coronagraph, per pipeline/config.py:ROMAN_CGI.
# Repeated here (rather than imported) to keep this file stdlib-only; tests/test_newswatch.py
# pins the two together, so a change in config.py fails CI rather than silently un-gating
# the most dangerous number this tool prints.
FLIGHT_BANDS = ("cgi-575", "cgi-730", "cgi-825")

# The pre-built bench — which planets we write briefings for in advance — is an editorial
# choice, so it lives in the playbook (see the note further down), not here.

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

MAX_ACT_PER_RUN = 3            # full message + attachment each; the real attention budget
MAX_STOCK_PER_RUN = 5          # one line each inside a single digest, so cheaper to carry
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
    has_image: bool = False
    planets: list[str] = field(default_factory=list)
    hosts: list[str] = field(default_factory=list)
    score: int = 0
    reasons: list[str] = field(default_factory=list)


# The "will it travel" test, which the runbook used to ask you to do by hand in sixty seconds.
# All four questions are answerable from the feed item, so the tool answers them. It reports
# the verdict; it does not act on it — a 1/4 story you happen to know is a big deal is still
# yours to jack, and a 4/4 one you don't fancy is still yours to skip.
TRAVEL_TESTS = (
    ("civilian noun", "a word a non-astronomer already owns"),
    ("picture", "an institution-supplied image — what our swatch argues with"),
    ("press office", "NASA/ESA/ESO and the like, not a preprint"),
    ("one planet", "one named world, not a population result"),
)


def travel_test(item: Item) -> tuple[list[bool], list[str]]:
    """Returns (four booleans in TRAVEL_TESTS order, the evidence for each)."""
    title = item.title.lower()
    nouns = [n for n in TRAVEL_NOUNS if n in title]
    title_planets, _ = find_planets(item.title, _ALIASES)
    results = [
        bool(nouns),
        item.has_image,
        item.feed.kind in ("press", "editorial"),
        len(title_planets) == 1,
    ]
    evidence = [
        ", ".join(nouns[:3]) if nouns else "none in the headline",
        "yes" if item.has_image else "none in the feed item",
        item.feed.name if results[2] else f"{item.feed.name} — no press office",
        title_planets[0] if results[3] else (
            f"{len(title_planets)} in the title" if title_planets else "none in the title"),
    ]
    return results, evidence


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


MEDIA_NS = "{http://search.yahoo.com/mrss/}"


def _has_image(node, raw_summary: str) -> bool:
    """Does this item ship an illustration?

    Part of the "will it travel" test, and the only one of its four questions that needed a
    new input. A story with an institution-supplied artist's impression travels several times
    further than one without — and that picture is precisely what our swatch argues with, so
    it doubles as our relevance test.
    """
    for tag in (f"{MEDIA_NS}content", f"{MEDIA_NS}thumbnail", "enclosure", "image"):
        for el in node.iter(tag):
            mime = (el.get("type") or el.get("medium") or "").lower()
            url = (el.get("url") or "").lower()
            if mime.startswith("image") or mime == "image" or re.search(
                r"\.(jpg|jpeg|png|webp|gif)(\?|$)", url
            ):
                return True
    return "<img" in raw_summary.lower()


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
        raw_summary = _text(node, "description", "summary", f"{ATOM_NS}summary")
        has_image = _has_image(node, raw_summary)
        summary = re.sub(r"<[^>]+>", " ", raw_summary)
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
            published=published, has_image=has_image,
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


# --------------------------------------------------------------------------
# the playbook — the editorial half, which does NOT live in this repository
# --------------------------------------------------------------------------
#
# Everything above this line is mechanism: feeds, name matching, ranking, the numbers, the
# band gate. It is engineering, it is worth testing in CI, and none of it is sensitive.
#
# Everything a *marketer* would recognise — where to post, in what order, the copy scaffolds,
# the accuracy checklist's wording, the standing infrared answer, which planets we pre-write
# for — lives in the PRIVATE notes repo and is loaded at run time. This repository is public;
# publishing the playbook would hand over the one part of the plan that took judgement, and
# would also mean a public workflow log could leak it.
#
# Same pattern as data/tours.json and data/roman-targets.json, which CLAUDE.md describes as
# "the WORDS live here and the data is re-joined against the catalogue of the moment".
#
# With no playbook the tool still works and still alerts — it prints the facts, states that
# the editorial half is missing, and says where it should be. That is the honest failure:
# a facts briefing is useful, and silently omitting the copy would look like a bug.

PLAYBOOK_ENV = "NEWSWATCH_PLAYBOOK"
PLAYBOOK_DEFAULT = REPO / "docs" / "notes" / "marketing" / "newswatch-playbook.json"


class _Fields(dict):
    """Leave an unknown {placeholder} alone instead of raising.

    The playbook is prose edited by hand in another repository. A typo in it must not be able
    to crash the alert that a story is breaking — a briefing with one literal `{hxe}` in it is
    recoverable at 23:40; a traceback is not.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass
class Playbook:
    path: Path
    data: dict

    def section(self, key: str) -> list[str]:
        val = self.data.get(key)
        if val is None:
            return []
        return list(val) if isinstance(val, list) else [val]

    def render(self, key: str, fields: dict) -> list[str]:
        return [line.format_map(_Fields(fields)) for line in self.section(key)]

    @property
    def bench(self) -> list[str]:
        return list(self.data.get("bench", []))

    def honesty(self, provenance: str) -> str:
        table = self.data.get("honesty_by_provenance", {})
        return table.get(provenance) or table.get("_default", "")


def load_playbook(explicit: Path | None = None) -> Playbook | None:
    # Note `Path("")` is `Path(".")`, which exists and is truthy — so an unset env var must be
    # filtered as a *string* before it ever becomes a Path, or this reads the repo root.
    env = os.environ.get(PLAYBOOK_ENV, "").strip()
    path = explicit or (Path(env) if env else PLAYBOOK_DEFAULT)
    if not path.is_file():
        return None
    return Playbook(path, json.loads(path.read_text()))


def _playbook_missing(out: list[str]) -> None:
    out.append("")
    out.append("  EDITORIAL HALF NOT LOADED — facts only.")
    out.append(_wrap(
        "The checklist, the where-to-post tiers and the copy scaffolds live in the private "
        "notes repo, not in this one. Point the tool at them with --playbook PATH or "
        f"${PLAYBOOK_ENV}; the default location is a symlink at "
        f"{PLAYBOOK_DEFAULT.relative_to(REPO)}. Recreate it with: "
        "ln -sfn ~/Documents/Dev/<notes-checkout> docs/notes", "    "))


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

    obs = rec.get("real_observations") or []
    if obs:
        out.append("")
        out.append("  REAL OBSERVATIONS EXIST FOR THIS ONE")
        for o in obs[:3]:
            out.append(f"    {o.get('telescope')} ({o.get('year')}): {o.get('band')} — "
                       f"{o.get('credit')}")

    sysd = rec.get("system") or {}
    if sysd.get("member_count", 0) > 1:
        sibs = ", ".join(s["name"] for s in sysd.get("siblings", [])[:6])
        out.append("")
        out.append(f"  SYSTEM   {sysd['hostname']} has {sysd['member_count']} "
                   f"known planets: {sibs}")


def brief_where(out: list[str], pb: Playbook | None, fields: dict) -> None:
    """Where to go, and in what order. The tactics are the playbook's; the SEARCH URLS stay
    here, because building a query string is mechanism, not editorial."""
    if pb is None:
        out.append("")
        out.append("  WHERE TO GO")
        for label, key in (("Bluesky", "search_bluesky"), ("Reddit", "search_reddit"),
                           ("r/space", "search_reddit_space"), ("HN", "search_hn")):
            out.append(f"    {label:9} {fields[key]}")
        return
    out.append("")
    out.extend(pb.render("where_to_go", fields))


def brief_copy(out: list[str], pb: Playbook | None, fields: dict) -> None:
    """Scaffolds, not copy — and not from this repository. See the playbook note above."""
    if pb is None:
        return
    out.append("")
    out.extend(pb.render("copy_header", fields))
    for block in pb.data.get("scaffolds", []):
        title = str(block.get("title", "")).format_map(_Fields(fields))
        out.append("")
        out.append(f"  \u2500\u2500 {title} \u2500\u2500")
        for line in block.get("lines", []):
            out.append(line.format_map(_Fields(fields)))


def brief_fields(rec: dict, name: str, base: str, pb: Playbook | None) -> dict:
    """Everything a playbook line may interpolate, in one place — so adding a scaffold in the
    notes repo never needs a code change here. That is the whole point of the split."""
    pid = rec["id"]
    tc = rec["true_colour"]
    hexv = tc["hex"]
    cname = colour_name(hexv)
    honesty = pb.honesty(rec["provenance"]) if pb else ""
    page = f"{site_url(base)}/planet/{pid}"
    q = urllib.parse.quote(name)

    # What a Bluesky post costs before the physics sentence exists, so the one sentence that
    # matters is written to a real budget instead of trimmed afterwards. The *shape* of that
    # fixed text is copy, so its template comes from the playbook; only the arithmetic is
    # ours. Without a playbook the budget is unknowable, so it is reported as 0 rather than
    # guessed — a made-up budget is worse than none.
    budget = 0
    if pb is not None:
        tpl = pb.data.get("bluesky_budget_template", "")
        fixed = tpl.format_map(_Fields({
            "name": name, "colour_name": cname, "hex": hexv, "honesty": honesty,
            "url_bluesky": utm(page, "bluesky", pid),
        }))
        budget = max(0, int(pb.data.get("bluesky_limit", 300)) - len(fixed))
    return {
        "name": name,
        "id": pid,
        "hex": hexv,
        "colour_name": cname,
        "provenance": rec["provenance"],
        "confidence": tc["confidence"],
        "honesty": honesty,
        "page": page,
        "release": release_tag(),
        "url_bluesky": utm(page, "bluesky", pid),
        "url_mastodon": utm(page, "mastodon", pid),
        "url_reddit": utm(page, "reddit", pid),
        "url_hn": utm(page, "hn", pid),
        "search_bluesky": f"https://bsky.app/search?q={q}",
        "search_reddit": f"https://www.reddit.com/search/?q={q}&sort=new",
        "search_reddit_space":
            f"https://www.reddit.com/r/space/search/?q={q}&restrict_sr=1&sort=new",
        "search_hn": f"https://hn.algolia.com/?query={q}&sort=byDate",
        "today": f"{datetime.now(UTC):%-d %b %Y}",
        "bluesky_budget": budget,
    }


def render_brief(rec: dict | None, name: str, base: str, *, headline: str | None = None,
                 source: str | None = None, link: str | None = None,
                 with_checklist: bool = True, playbook: Playbook | None = None) -> str:
    out: list[str] = []
    if rec is None:
        brief_missing(name, out, base)
        out.append(RULE)
        return "\n".join(out)
    brief_planet(rec, out, base, headline=headline, source=source, link=link)
    fields = brief_fields(rec, rec["name"], base, playbook)
    brief_where(out, playbook, fields)
    brief_copy(out, playbook, fields)
    if playbook is None:
        _playbook_missing(out)
    elif with_checklist:
        for key in ("checklist", "standing_infrared", "closing"):
            lines = playbook.render(key, fields)
            if lines:
                out.append("")
                out.extend(lines)
    out.append("")
    out.append(RULE)
    return "\n".join(out)


# --------------------------------------------------------------------------
# notification — the alert that reaches a phone
# --------------------------------------------------------------------------
#
# Why a push at all: the plan dies in week two if checking is something you have to
# remember. Why Telegram specifically: the briefing is a *private* artifact. It carries
# where-to-post tactics and half-written copy, and this repository is public, so it must
# never reach a workflow log. The chat is the only place it goes.

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
TELEGRAM_LIMIT = 4096

# Two tiers, because "popping off" and "about to" need opposite responses. A press feed means
# the general-audience cycle has started and the reply window is ~2 hours wide. A preprint
# means no clock at all — the right move is to write the bench entry in daylight, which is the
# plan's "stock beats speed". Alerting both the same way would train you to ignore both.
TIER_ACT = "ACT NOW"
TIER_STOCK = "PRE-BUILD"


def tier_of(item: Item) -> str:
    return TIER_STOCK if item.feed.kind == "preprint" else TIER_ACT


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@dataclass
class Telegram:
    token: str
    chat_id: str

    @classmethod
    def from_env(cls) -> Telegram | None:
        token = os.environ.get("NEWSWATCH_TELEGRAM_TOKEN", "").strip()
        chat = os.environ.get("NEWSWATCH_TELEGRAM_CHAT_ID", "").strip()
        return cls(token, chat) if token and chat else None

    def _post(self, method: str, body: bytes, content_type: str) -> dict:
        req = urllib.request.Request(
            TELEGRAM_API.format(token=self.token, method=method),
            data=body, headers={"Content-Type": content_type, "User-Agent": UA},
        )
        with urllib.request.urlopen(req, timeout=45) as resp:  # noqa: S310 (telegram.org)
            return json.loads(resp.read().decode())

    def message(self, html: str) -> dict:
        # Telegram hard-caps a message at 4096 characters. Truncate rather than split: the
        # alert is a summary by design and the whole thing is attached as a file anyway.
        if len(html) > TELEGRAM_LIMIT:
            html = html[: TELEGRAM_LIMIT - 40] + "\n… (truncated; see attachment)"
        body = urllib.parse.urlencode({
            "chat_id": self.chat_id, "text": html, "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode()
        return self._post("sendMessage", body, "application/x-www-form-urlencoded")

    def document(self, filename: str, content: str, caption: str = "") -> dict:
        boundary = "----newswatch" + str(abs(hash(filename)) % 10**12)
        parts: list[bytes] = []

        def field(name: str, value: str) -> None:
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n".encode()
            )

        field("chat_id", self.chat_id)
        if caption:
            field("caption", caption[:1024])
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="document"; '
            f'filename="{filename}"\r\nContent-Type: text/markdown; charset=utf-8\r\n\r\n'
            .encode() + content.encode() + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        return self._post("sendDocument", b"".join(parts),
                          f"multipart/form-data; boundary={boundary}")


@dataclass
class Target:
    """What one news item is actually *about*, resolved once.

    This lived inline in three places and they drifted: one branch fell through to the string
    "unknown", which then rendered a Bluesky search for "unknown" and a fast-path command
    reading `--planet "unknown"`. Resolving it once, with an explicit `kind`, is what stops
    an alert from confidently telling you to build a planet that does not exist.
    """

    name: str            # what to SHOW — the display name when we have a record
    record: dict | None
    kind: str            # "planet" | "planet-missing" | "host" | "none"

    @property
    def archive_name(self) -> str:
        """What to pass to `pipeline build --planet`, which wants the Archive spelling."""
        return self.record["name"] if self.record else self.name


def resolve_target(item: Item, catalogue: Catalogue) -> Target:
    for p in item.planets:
        rec = catalogue.get(p)
        if rec is not None:
            return Target(rec["name"], rec, "planet")
    if item.planets:
        return Target(item.planets[0], None, "planet-missing")
    for h in item.hosts:
        sib = catalogue.by_host(h)
        if sib is not None:
            return Target(h, sib, "host")
        return Target(h, None, "host")
    return Target("unknown", None, "none")


GH_REPO = os.environ.get("GH_REPO", "jocarino/roman-telescope-data")


def data_pr_nudge(*, timeout: int = 15) -> str:
    """Is a catalogue-refresh PR sitting open, unmerged?

    The Thursday drift probe opens one and creates the release as a DRAFT, so nothing reaches
    the site until a human merges and publishes. A "not in our catalogue" alert is the exact
    moment that matters — the planet may already be built and waiting on you. Unauthenticated:
    the repo is public, and two runs a day is nowhere near the 60/hour anonymous limit.

    Best effort by design. If GitHub is unreachable this returns "" and the alert goes out
    without the nudge; failing an alert about a breaking story over a missing nicety would be
    the wrong trade.
    """
    url = (f"https://api.github.com/repos/{GH_REPO}/pulls"
           f"?state=open&per_page=20")
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (github.com)
            prs = json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001 — a nudge must never break an alert
        return ""
    data_prs = [p for p in prs
                if str(p.get("head", {}).get("ref", "")).startswith("data/refresh-")]
    if not data_prs:
        return ""
    p = data_prs[0]
    return (f"📦 <b>A data refresh PR is already open</b> — "
            f'<a href="{_esc(p["html_url"])}">#{p["number"]}</a>. '
            f"Merge it and publish its draft release and the catalogue moves without a manual "
            f"build. Check there before running the commands above.")


def _age(published: datetime | None, now: datetime) -> str:
    if published is None:
        return "undated"
    hours = (now - published).total_seconds() / 3600
    if hours < 1:
        return "just now"
    if hours < 48:
        return f"{int(hours)} h ago"
    return f"{int(hours // 24)} d ago"


# Whether to run the paper diff. Off unless --diff-paper is passed: it is the one part of
# newswatch that needs a network call to a third party and an SDK the poll path doesn't have.
DIFF_PAPER = False


def paper_diff_lines(item: Item, rec: dict) -> list[str]:
    """Checklist step 2, run for you — see tools/paper_diff.py for why a model only ever
    QUOTES here and Python does the comparing.

    Best effort in every direction. No `--diff-paper`, no SDK installed, no API key, no paper
    linked, no numbers in the abstract: the alert goes out unchanged. The one thing this must
    never do is make a missing diff look like a clean one, so it stays silent rather than
    reporting 'no differences found'.
    """
    if not DIFF_PAPER:
        return []
    try:
        from tools.paper_diff import diff_paper
    except ImportError:
        return ["", "<i>--diff-paper needs the SDK: uv sync --extra paperdiff</i>"]
    params, star = rec["params"], rec["host_star"]
    ours = {
        "radius": params.get("radius_r_earth"),
        "mass": params.get("mass_m_earth"),
        "equilibrium_temperature": params.get("equilibrium_temp_k"),
        "host_teff": star.get("teff_k"),
    }
    try:
        result = diff_paper(item.link, ours)
    except Exception as e:  # noqa: BLE001 — an alert must survive a broken diff
        return ["", f"<i>paper diff failed ({type(e).__name__}) — do step 2 by hand</i>"]
    if not result:
        return []

    superseded = [c for c in result["comparisons"] if c.superseded]
    head = ("⚠️ <b>THE PAPER MOVED OUR NUMBERS</b>" if superseded
            else "📄 <b>Paper agrees within tolerance</b>")
    lines = ["", head, f"<i>from the abstract of arXiv:{_esc(result['arxiv_id'])}</i>"]
    for c in result["comparisons"]:
        mark = "⚠️" if c.superseded else "·"
        ours_txt = "—" if c.ours is None else f"{c.ours:,.2f}"
        theirs_txt = "—" if c.theirs is None else f"{c.theirs:,.2f}"
        lines.append(f"{mark} {c.quantity}: ours {ours_txt} vs paper {theirs_txt} "
                     f"({_esc(c.unit_printed)}) — {_esc(c.detail)}")
    if superseded:
        lines.append("Post the <b>colour change</b>, not the swatch.")
    lines.append("<i>Abstract only, not the parameter table — still open the paper.</i>")
    return lines


def alert_text(item: Item, target: Target, base: str, *, now: datetime,
               playbook: Playbook | None = None) -> str:
    """The message that lands on the phone. Its only job is to answer 'do I care right now',
    in the time it takes to read a notification. Everything else is in the attachment."""
    tier = tier_of(item)
    head = "🔴" if tier == TIER_ACT else "🔵"
    name, rec = target.name, target.record
    label = name if target.kind != "host" else f"{name} (system — no planet named)"
    lines = [
        f"{head} <b>{tier}</b> · {_esc(label)}",
        f"<b>{_esc(item.title)}</b>",
        f"{_esc(item.feed.name)} · {item.feed.kind} · {_age(item.published, now)}",
        "",
    ]

    # Branch on `kind`, never on `rec is None`. Branching on the record is what produced
    # `--planet "TRAPPIST-1"` — an instruction to build a *star* as a planet, in the one
    # message you would act on without checking.
    if target.kind == "host":
        if rec is not None:
            n = rec["system"]["member_count"] if rec.get("system") else 1
            lines += [
                f"The story names the <b>host</b>, not a planet. We have {n} planet(s) "
                f"there — nearest match <code>{rec['true_colour']['hex']}</code> "
                f"{_esc(rec['name'])}.",
            ]
        else:
            lines.append(
                "The story names a <b>host star</b> we have no planets for, and names no "
                "planet. There is nothing to colour yet."
            )
        lines.append(
            "Read the story first: a system story is often about a planet we lack, and the "
            "planet's name may not be in the headline."
        )
    elif target.kind == "planet-missing":
        lines += [
            "⚠️ <b>NOT IN OUR CATALOGUE</b> — we cannot post a colour for this one yet.",
            "This is the majority case on a 'new planet discovered' story.",
            "",
            "<b>Build it and put it on the site</b> — merging is what the site actually",
            "reads; a briefing alone leaves your own link 404ing:",
            f"<pre>uv run python -m pipeline build --planet \"{_esc(target.archive_name)}\" \\\n"
            f"    --merge-into data/planets.json --no-cache\n"
            f"scripts/release-data.sh\n"
            "git add data/RELEASE &amp;&amp; git commit -m 'Data release' "
            "&amp;&amp; git push</pre>",
            "If the gate rejects it, the missing number is itself the post.",
        ]
        nudge = data_pr_nudge()
        if nudge:
            lines += ["", nudge]
    else:
        tc = rec["true_colour"]
        stale, stale_why = roman_is_stale(rec)
        params, star = rec["params"], rec["host_star"]
        lines += [
            f"<code>{tc['hex']}</code> — {colour_name(tc['hex'])} "
            f"({rec['provenance']}, confidence {tc['confidence']})",
        ]
        if stale:
            lines.append(f"⛔ Roman view withheld — {_esc(stale_why)}")
        else:
            view = rec["instrument_views"][0]
            lines.append(
                f"<code>{view['colour']['hex']}</code> — as Roman would see it, "
                f"ΔE2000 {view['reconstruction_error']['delta_e2000']:.1f}"
            )
        lines += [
            f"release {release_tag()} · {site_url(base)}/planet/{rec['id']}",
            "",
            "<b>Diff these four against the paper before you post</b>",
            f"<pre>R {_fmt(params.get('radius_r_earth'), ' R⊕')}   "
            f"M {_fmt(params.get('mass_m_earth'), ' M⊕')}\n"
            f"T_eq {_fmt(params.get('equilibrium_temp_k'), ' K', 0)}   "
            f"host {_fmt(star.get('teff_k'), ' K', 0)}</pre>",
            ">10% on R/M or >100 K on either ⇒ post the <i>change</i>, not the swatch.",
        ]
        lines += paper_diff_lines(item, rec)

    # Step 1 of the runbook, answered rather than asked. All four questions are answerable
    # from the feed item, so there is no reason to make a human do it at 60 seconds a time.
    passed, evidence = travel_test(item)
    marks = "".join("✅" if p else "▫️" for p in passed)
    lines += [
        "",
        f"<b>Will it travel? {marks} {sum(passed)}/4</b>",
        *[f"  {'✅' if p else '▫️'} {label} — {_esc(ev)}"
          for (label, _), p, ev in zip(TRAVEL_TESTS, passed, evidence, strict=True)],
    ]
    if sum(passed) < 2:
        lines.append("<i>Under 2/4 — stories travel on nouns and pictures, not results. "
                     "Skipping this is free.</i>")

    q = urllib.parse.quote(name)
    lines += [
        "",
        f'<a href="https://bsky.app/search?q={q}">Bluesky</a> · '
        f'<a href="https://www.reddit.com/search/?q={q}&amp;sort=new">Reddit</a> · '
        f'<a href="https://hn.algolia.com/?query={q}&amp;sort=byDate">HN</a>',
    ]
    # What to DO with those links is editorial, so it comes from the playbook. Without one
    # the alert is still complete and actionable — it just doesn't tell you the tactics.
    if playbook is not None:
        advice = playbook.render(
            "alert_act_now" if tier == TIER_ACT else "alert_stock",
            {"name": _esc(name), "archive_name": _esc(target.archive_name)},
        )
        if advice:
            lines += ["", *advice]
    if item.link:
        lines += ["", f'<a href="{_esc(item.link)}">the story</a>']
    return "\n".join(lines)


def notify_items(tg: Telegram, surfaced: list[Item], catalogue: Catalogue, base: str,
                 *, now: datetime, attach: bool = True,
                 playbook: Playbook | None = None) -> int:
    """Two very different messages, because the two tiers are two different jobs.

    ACT NOW gets the full alert plus the briefing as an attachment: there is a clock, and you
    need everything to hand. PRE-BUILD gets ONE line inside ONE digest for the whole run, and
    no attachment at all — a preprint has no clock, so a briefing you didn't ask for is just
    noise, and noise is what makes a person mute the channel. The briefing is a command away
    on the rare occasion you want it.
    """
    act = [it for it in surfaced if tier_of(it) == TIER_ACT]
    stock = [it for it in surfaced if tier_of(it) != TIER_ACT]
    sent = 0

    for it in act:
        target = resolve_target(it, catalogue)
        tg.message(alert_text(it, target, base, now=now, playbook=playbook))
        if attach:
            body = render_brief(target.record, target.name, base, headline=it.title,
                                source=f"{it.feed.name} ({it.feed.kind})", link=it.link,
                                playbook=playbook)
            fname = f"{slug(target.name) or 'briefing'}-{now:%Y%m%d}.md"
            caption = ("Full briefing — facts, checklist and copy scaffolds." if playbook
                       else "Full briefing — FACTS ONLY, no playbook loaded.")
            tg.document(fname, f"```\n{body}\n```\n", caption=caption)
        sent += 1

    if stock:
        tg.message(digest_text(stock, catalogue, now=now))
        sent += 1
    return sent


def digest_text(stock: list[Item], catalogue: Catalogue, *, now: datetime) -> str:
    """One line per preprint, one message per run, nothing attached.

    Its only job is to let you notice a planet you might want on the bench before its press
    wave. Nothing here is actionable today, and the message says so, so it can be read in two
    seconds and dismissed without guilt.
    """
    lines = [f"🔵 <b>PRE-BUILD</b> · {len(stock)} preprint{'s' if len(stock) > 1 else ''}"]
    for it in stock:
        target = resolve_target(it, catalogue)
        mark = "" if target.record is not None else " ⚠️ not in catalogue"
        lines.append(
            f'· <a href="{_esc(it.link)}">{_esc(target.name)}</a>{mark} — '
            f"{_esc(it.title[:70])}{'…' if len(it.title) > 70 else ''}"
        )
    lines.append("")
    lines.append("<i>No clock on any of these. Ignore unless a name is one you want ready.</i>")
    return "\n".join(lines)


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
    if args.if_older_than and ALIAS_FILE.exists():
        built = json.loads(ALIAS_FILE.read_text()).get("built_at")
        if built:
            age = (datetime.now(UTC) - datetime.fromisoformat(built)).total_seconds() / 86400
            if age < args.if_older_than:
                print(f"Alias table is {age:.1f} d old (< {args.if_older_than}); not rebuilding.")
                return
    t = build_aliases()
    for probe in ("K2-18b", "TRAPPIST-1e", "HD189733b", "Gliese 1214 b", "51 Pegasi b",
                  "beta Pictoris b", "Osiris", "TOI-700 d"):
        pl, ho = find_planets(probe, t)
        print(f"  {probe:22} -> planets={pl or '—'}  hosts={ho or '—'}")


def cmd_poll(args: argparse.Namespace) -> None:
    global _ALIASES, DIFF_PAPER
    DIFF_PAPER = args.diff_paper
    _ALIASES = load_aliases()
    _, catalogue = load_catalogue()
    playbook = load_playbook(_playbook_arg(args))
    state = load_state()
    now = datetime.now(UTC)
    if playbook is None:
        print("note: no playbook — briefings will be facts only. See --playbook.")

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

    # The cap is per tier, because the two cost very different amounts of attention. An ACT
    # NOW is a full message plus an attachment; a PRE-BUILD is one line inside a shared
    # digest. Capping the mixed list at three would spend the whole budget on preprints on a
    # day when a press release also broke — which is exactly backwards.
    act = [i for i in kept if tier_of(i) == TIER_ACT][:MAX_ACT_PER_RUN]
    stock = [i for i in kept if tier_of(i) != TIER_ACT][:MAX_STOCK_PER_RUN]
    surfaced = act + stock
    print(f"{len(items)} items polled · {len(kept)} passed the filters · "
          f"showing {len(act)} act-now (cap {MAX_ACT_PER_RUN}) + "
          f"{len(stock)} pre-build (cap {MAX_STOCK_PER_RUN})")
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

    if args.quiet:
        # The briefing carries where-to-post tactics and half-written copy. This repository is
        # public, so in CI it must never reach stdout — a workflow log is world-readable. One
        # line per item is enough to see the run worked; the substance goes to the chat.
        for it in surfaced:
            where = it.planets[0] if it.planets else (it.hosts[0] if it.hosts else "?")
            print(f"  {tier_of(it):9} {it.score:3}  {it.feed.id:14} {where}")
    else:
        for it in surfaced:
            target = resolve_target(it, catalogue)
            why = f"score {it.score}: " + "; ".join(it.reasons)
            print(render_brief(
                target.record, target.name, args.base_url,
                headline=f"{it.title}\n\n{why}",
                source=f"{it.feed.name} ({it.feed.kind})",
                link=it.link, playbook=playbook,
            ))
            print()

    if args.notify:
        tg = Telegram.from_env()
        if tg is None:
            sys.exit(
                "--notify was asked for but NEWSWATCH_TELEGRAM_TOKEN / "
                "NEWSWATCH_TELEGRAM_CHAT_ID are not set.\n"
                "Failing loudly on purpose: a notifier that quietly does nothing is worse "
                "than no notifier — you would trust it and hear nothing."
            )
        if surfaced:
            n = notify_items(tg, surfaced, catalogue, args.base_url, now=now,
                             attach=not args.no_attach, playbook=playbook)
            state["last_alert"] = now.isoformat()
            print(f"Sent {n} message(s) to Telegram.")
        else:
            # Deliberately silent. Silence still has to be distinguishable from breakage, but
            # the failure ping in the workflow does that job — it fires on a broken run, which
            # is the case that matters. A periodic "still alive" message is a notification you
            # can do nothing with, and those are what train a person to stop reading the ones
            # they can.
            print("Nothing to alert. No message sent.")

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


def cmd_notify(args: argparse.Namespace) -> None:
    """Prove the channel works before anything depends on it."""
    tg = Telegram.from_env()
    if tg is None:
        sys.exit(
            "Set both:\n"
            "  export NEWSWATCH_TELEGRAM_TOKEN=<from @BotFather>\n"
            "  export NEWSWATCH_TELEGRAM_CHAT_ID=<your chat id>\n\n"
            "To get the chat id: message your new bot once, then open\n"
            "  https://api.telegram.org/bot<TOKEN>/getUpdates\n"
            "and read result[0].message.chat.id (a personal chat id is a positive integer)."
        )
    resp = tg.message(
        "🔭 <b>newswatch</b> — channel test.\n"
        "If you can read this, the bot, the token and the chat id all work.\n"
        f"<pre>release {release_tag()}</pre>"
    )
    if args.attach:
        tg.document("newswatch-test.md", "# newswatch\n\nAttachment delivery works.\n",
                    caption="Attachment test — full briefings arrive like this.")
    print("ok" if resp.get("ok") else json.dumps(resp, indent=1))


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
    print(render_brief(rec, name, args.base_url, with_checklist=not args.no_checklist,
                       playbook=load_playbook(_playbook_arg(args))))


def _playbook_arg(args: argparse.Namespace) -> Path | None:
    p = getattr(args, "playbook", None)
    return Path(p) if p else None


def cmd_bench(args: argparse.Namespace) -> None:
    playbook = load_playbook(_playbook_arg(args))
    if playbook is None or not playbook.bench:
        sys.exit(
            "The bench list is editorial — which planets are worth pre-writing — so it lives "
            "in the playbook, not\nin this repository. Point at it with --playbook PATH or "
            f"${PLAYBOOK_ENV}\n(default: {PLAYBOOK_DEFAULT.relative_to(REPO)})."
        )
    _, catalogue = load_catalogue()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    names = list(playbook.bench)
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
            + render_brief(rec, rec["name"], args.base_url, playbook=playbook) + "\n```\n"
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

    def playbook_arg(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--playbook", metavar="PATH", default=None,
            help="The editorial half — checklist, where-to-post tiers, copy scaffolds, bench "
                 f"list — which lives in the PRIVATE notes repo, not here. Or ${PLAYBOOK_ENV}. "
                 f"Default: {PLAYBOOK_DEFAULT.relative_to(REPO)} (a gitignored symlink). "
                 "Without it the tool still runs and still alerts, with facts only.",
        )

    f = sub.add_parser("feeds", help="Check every source resolves; optionally snapshot them")
    f.add_argument("--save-fixture", metavar="DIR",
                   help="Write each feed's XML to DIR for offline replay")
    f.add_argument("--trim", type=int, default=8, metavar="N",
                   help="Keep only the first N entries per saved feed (0 = whole feed). "
                        "The default keeps the committed fixture small enough for CI.")
    f.set_defaults(func=cmd_feeds)

    a = sub.add_parser("aliases", help="Build the name lookup from the Archive (run weekly)")
    a.add_argument("--if-older-than", type=float, default=0.0, metavar="DAYS",
                   help="Only rebuild when the cached table is older than DAYS. For a cron "
                        "that runs twice a day but should pull the Archive once a week.")
    a.set_defaults(func=cmd_aliases)

    po = sub.add_parser("poll", help="Poll, rank, print at most 3 briefings")
    po.add_argument("--fixture", metavar="DIR", help="Replay saved feeds instead of the network")
    po.add_argument("--dry-run", action="store_true",
                    help="Don't advance state or log — re-running gives the same answer")
    po.add_argument("--log", metavar="PATH", help="Newsjack log path")
    po.add_argument("--notify", action="store_true",
                    help="Push each surfaced item to Telegram (needs NEWSWATCH_TELEGRAM_TOKEN "
                         "and NEWSWATCH_TELEGRAM_CHAT_ID). Exits non-zero if they are unset.")
    po.add_argument("--no-attach", action="store_true",
                    help="Alert only; don't attach the full briefing as a document")
    po.add_argument("--diff-paper", action="store_true",
                    help="Run checklist step 2 for you: find the linked paper, quote its "
                         "stated radius/mass/T_eq/host T_eff, and diff them against ours. "
                         "Needs ANTHROPIC_API_KEY and `uv sync --extra paperdiff`. Off by "
                         "default — it is the only part that calls a third party.")
    po.add_argument("--quiet", action="store_true",
                    help="Print one line per item instead of the briefings. Use this in CI: "
                         "this repository is public and a workflow log is world-readable.")
    po.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS, metavar="N",
                    help=f"Ignore items published more than N days ago (default {MAX_AGE_DAYS}). "
                         f"Feeds move at very different speeds — ESO's holds ten items and can "
                         f"serve a three-week-old release as its newest.")
    po.add_argument("--base-url", default=base_default, help="Site origin (or $SITE_BASE_URL)")
    playbook_arg(po)
    po.set_defaults(func=cmd_poll)

    b = sub.add_parser("brief", help="Briefing for one planet, on demand")
    b.add_argument("name")
    b.add_argument("--planets", metavar="PATH", help="Alternative planets.json (fast-path output)")
    b.add_argument("--base-url", default=base_default)
    b.add_argument("--no-checklist", action="store_true")
    playbook_arg(b)
    b.set_defaults(func=cmd_brief)

    be = sub.add_parser("bench", help="Pre-write the briefings that cover most headlines")
    be.add_argument("--out", default="docs/notes/marketing/bench", metavar="DIR",
                    help="Where to write them. Defaults inside the private notes repo, since "
                         "a bench briefing is finished copy.")
    be.add_argument("--base-url", default=base_default)
    playbook_arg(be)
    be.set_defaults(func=cmd_bench)

    nt = sub.add_parser("notify", help="Send a test message, to prove the channel works")
    nt.add_argument("--attach", action="store_true", help="Also send a test attachment")
    nt.set_defaults(func=cmd_notify)

    lg = sub.add_parser("log", help="Show the newsjack log")
    lg.add_argument("--log", metavar="PATH")
    lg.set_defaults(func=cmd_log)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
