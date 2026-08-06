"""Step 2 of the newsjack checklist, mechanised: what does the PAPER say, versus what do we?

The checklist's most valuable step is diffing four numbers — radius, mass, equilibrium
temperature, host T_eff — against the paper being reported, because a swatch computed from
superseded parameters is the one mistake this project cannot afford. It is also five minutes
of tedium per alert, which is exactly the kind of thing that stops happening.

THE DESIGN CONSTRAINT, and the reason this file is shaped the way it is: a model must never
decide whether our numbers are superseded. It only ever *quotes* — it pulls the sentence a
number appears in, the number as printed, and the unit as printed. Python converts the units
and applies the tolerance. So the failure mode of a bad extraction is an unhelpful quote you
can see is wrong next to its source, never a confident wrong verdict in the one place the
checklist exists to protect. That is what makes automating this step safe at all.

It reads the ABSTRACT, not the parameter table, because that is what a feed gives us. Papers
often quote their headline numbers there and often don't. So this front-loads the diff; it
does not retire the checklist step, and every output says so.

Optional dependency: `uv sync --extra paperdiff` (or `pip install anthropic`). The rest of
newswatch is stdlib-only so the scheduled workflow runs on bare python3.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

UA = "newswatch-paperdiff/1.0 (exoplanet-palette)"
ARXIV_API = "http://export.arxiv.org/api/query"

# Claude reads a short abstract and quotes from it. Thinking is on by default on this model
# and `max_tokens` caps thinking plus text together, so the budget is generous for the size
# of the answer.
MODEL = "claude-opus-5"
MAX_TOKENS = 8000

Quantity = Literal["radius", "mass", "equilibrium_temperature", "host_teff"]

# Unit conversion is arithmetic, so it is ours. Asking the model to normalise units would put
# a silent R_Jup -> R_Earth slip inside the one number the checklist is protecting.
_TO_R_EARTH = {
    "r_earth": 1.0, "rearth": 1.0, "re": 1.0, "r_e": 1.0, "r⊕": 1.0, "earthradii": 1.0,
    "r_jup": 11.2089, "rjup": 11.2089, "rj": 11.2089, "r_j": 11.2089, "jupiterradii": 11.2089,
    "r_sun": 109.076, "rsun": 109.076, "r_s": 109.076,
}
_TO_M_EARTH = {
    "m_earth": 1.0, "mearth": 1.0, "me": 1.0, "m_e": 1.0, "m⊕": 1.0, "earthmasses": 1.0,
    "m_jup": 317.828, "mjup": 317.828, "mj": 317.828, "m_j": 317.828, "jupitermasses": 317.828,
    "m_sun": 332946.0, "msun": 332946.0, "m_s": 332946.0,
}
_TO_KELVIN = {"k": 1.0, "kelvin": 1.0}

_UNIT_TABLES: dict[str, dict[str, float]] = {
    "radius": _TO_R_EARTH,
    "mass": _TO_M_EARTH,
    "equilibrium_temperature": _TO_KELVIN,
    "host_teff": _TO_KELVIN,
}

# The checklist's own tolerances.
TOLERANCE_FRACTION = 0.10      # radius, mass
TOLERANCE_KELVIN = 100.0       # T_eq, host T_eff


class Quote(BaseModel):
    """One parameter, exactly as the paper prints it."""

    quantity: Quantity
    value: float = Field(description="The central value as printed. No unit conversion.")
    unit: str = Field(
        description="The unit token exactly as printed, e.g. 'R_Earth', 'M_Jup', 'K'."
    )
    sentence: str = Field(description="The sentence this came from, copied verbatim.")


class Extraction(BaseModel):
    quotes: list[Quote] = Field(
        description="One entry per parameter actually stated. Omit anything not stated."
    )
    planet: str = Field(description="The planet the numbers describe, as the text names it.")
    note: str = Field(description="One sentence: anything that makes these numbers ambiguous.")


SYSTEM = """\
You extract stated parameter values from astronomy abstracts. You are a quoting tool, not an \
analyst.

Rules:
- Only report a value the text states outright. Never infer, convert, average, or compute one.
- Report the number exactly as printed and the unit exactly as printed. Do not convert units.
- For a value with an uncertainty ("2.61 +0.09 -0.08"), report the central value only.
- Copy the source sentence verbatim so a human can check you.
- If the text states none of these parameters, return an empty list. An empty answer is a \
correct answer and is far better than a guess.
- If the abstract describes several planets, extract only the one it is chiefly about, and \
name it in `planet`."""


@dataclass
class Comparison:
    quantity: str
    ours: float | None
    theirs: float | None
    unit_printed: str
    sentence: str
    superseded: bool
    detail: str


# Abstracts print units as LaTeX. `R_\oplus`, `$R_{\rm Jup}$` and `M_\odot` all have to land
# on the same keys as `R_Earth` — an unrecognised unit means no comparison, so a normaliser
# that gives up on LaTeX quietly disables the diff on most real papers.
_SYMBOLS = (
    (r"\oplus", "earth"), (r"\odot", "sun"), (r"\Earth", "earth"), (r"\Sun", "sun"),
    ("⊕", "earth"), ("☉", "sun"),
)
_LATEX_FONT = re.compile(r"\\(?:rm|mathrm|text|textrm|bf|it|mathit|mbox)\b")


def _norm_unit(unit: str) -> str:
    s = unit
    for token, word in _SYMBOLS:
        s = s.replace(token, word)
    s = _LATEX_FONT.sub("", s)
    s = re.sub(r"[\s${}\\,~]+", "", s)
    return s.strip().lower().rstrip(".")


def to_canonical(quantity: str, value: float, unit: str) -> float | None:
    """Convert a printed value into our units (R⊕, M⊕, K). None if the unit is unrecognised —
    an unknown unit must not silently pass through as though it were ours."""
    table = _UNIT_TABLES.get(quantity)
    if table is None:
        return None
    factor = table.get(_norm_unit(unit))
    return None if factor is None else value * factor


def compare(ours: dict[str, float | None], extraction: Extraction) -> list[Comparison]:
    """The verdict, computed in Python. No model input reaches this function except numbers
    and unit strings it already quoted."""
    out: list[Comparison] = []
    for q in extraction.quotes:
        theirs = to_canonical(q.quantity, q.value, q.unit)
        mine = ours.get(q.quantity)
        if theirs is None:
            detail, superseded = f"unrecognised unit {q.unit!r} — compare by hand", False
        elif mine is None:
            detail, superseded = "we have no value for this", False
        elif q.quantity in ("equilibrium_temperature", "host_teff"):
            delta = abs(mine - theirs)
            superseded = delta > TOLERANCE_KELVIN
            detail = f"Δ {delta:,.0f} K (tolerance {TOLERANCE_KELVIN:.0f} K)"
        else:
            denom = theirs if theirs else None
            if denom is None:
                detail, superseded = "paper value is zero — compare by hand", False
            else:
                frac = abs(mine - theirs) / abs(denom)
                superseded = frac > TOLERANCE_FRACTION
                detail = f"Δ {frac * 100:.1f}% (tolerance {TOLERANCE_FRACTION * 100:.0f}%)"
        out.append(Comparison(
            quantity=q.quantity, ours=mine, theirs=theirs, unit_printed=q.unit,
            sentence=q.sentence, superseded=superseded, detail=detail,
        ))
    return out


# --- getting the abstract --------------------------------------------------

_ARXIV_ID = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})")


def arxiv_id_from(url: str, *, timeout: int = 20) -> str | None:
    """The arXiv id for a story URL — direct if it is an arXiv link, else by looking for one on
    the page. Press releases routinely link the paper; when they don't, we simply have no
    abstract, and the caller says so rather than inventing one."""
    direct = _ARXIV_ID.search(url or "")
    if direct:
        return direct.group(1)
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (feed link)
            body = resp.read(400_000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 — best effort; no abstract is a valid outcome
        return None
    found = _ARXIV_ID.search(body)
    return found.group(1) if found else None


def fetch_abstract(arxiv_id: str, *, timeout: int = 30) -> tuple[str, str] | None:
    """(title, abstract) from the arXiv API, or None."""
    url = f"{ARXIV_API}?{urllib.parse.urlencode({'id_list': arxiv_id, 'max_results': 1})}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (arxiv.org)
            root = ET.fromstring(resp.read())
    except Exception:  # noqa: BLE001
        return None
    ns = "{http://www.w3.org/2005/Atom}"
    entry = root.find(f"{ns}entry")
    if entry is None:
        return None
    title = (entry.findtext(f"{ns}title") or "").strip()
    summary = (entry.findtext(f"{ns}summary") or "").strip()
    return (re.sub(r"\s+", " ", title), re.sub(r"\s+", " ", summary)) if summary else None


# --- the model call --------------------------------------------------------

def extract(abstract: str, *, title: str = "", model: str = MODEL) -> Extraction | None:
    """Quote the stated parameters out of an abstract. None on refusal or a missing key."""
    import anthropic  # imported here so the stdlib-only poll path never needs the SDK

    try:
        client = anthropic.Anthropic()
    except Exception:  # noqa: BLE001 — no resolvable credentials; a missing diff, not a crash
        return None
    try:
        response = client.messages.parse(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            output_config={"effort": "low"},
            messages=[{
                "role": "user",
                "content": (
                    f"Title: {title}\n\nAbstract:\n{abstract}\n\n"
                    "Quote every stated value for: planet radius, planet mass, planet "
                    "equilibrium temperature, host star effective temperature."
                ),
            }],
            output_format=Extraction,
        )
    except anthropic.AuthenticationError:
        return None
    except anthropic.NotFoundError:
        raise  # a bad model id is a bug in this file, not a transient — surface it
    except anthropic.RateLimitError:
        return None
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        return None
    except TypeError:
        # The SDK raises TypeError, not an APIError, when it cannot resolve any credential.
        return None
    if response.stop_reason == "refusal":
        return None
    return response.parsed_output


def diff_paper(story_url: str, ours: dict[str, float | None]) -> dict | None:
    """The whole chain: story URL -> arXiv id -> abstract -> quotes -> Python's verdict.

    Returns None whenever any link is missing — no paper linked, no abstract, no key, nothing
    stated. A missing diff is a normal outcome and must never look like a clean diff.
    """
    # No ANTHROPIC_API_KEY check here on purpose: an unset key does NOT mean there are no
    # credentials — the SDK also resolves ANTHROPIC_AUTH_TOKEN, an `ant auth login` profile,
    # and workload identity. Gating on the env var would silently skip the diff for anyone
    # authenticated any other way. Let the SDK resolve and treat a failure as "no diff".
    arxiv_id = arxiv_id_from(story_url)
    if arxiv_id is None:
        return None
    fetched = fetch_abstract(arxiv_id)
    if fetched is None:
        return None
    title, abstract = fetched
    extraction = extract(abstract, title=title)
    if extraction is None or not extraction.quotes:
        return None
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "planet": extraction.planet,
        "note": extraction.note,
        "comparisons": compare(ours, extraction),
    }
