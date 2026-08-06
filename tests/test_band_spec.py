"""The Roman CGI band set, pinned to its published source — and to the data we ship.

This project once shipped four bands (575/10%, 660/6%, 730/6%, 835/15%) through its signature
feature. Three of those numbers appear in no primary CGI source; they were our own invention.
Correcting `pipeline/config.py` was the easy half. The hard half is that the spec is *written
down* in a dozen places — prose, a diagram, glossary entries, the emitted data — and two of
them (`how.html`'s calculations fold and the `spectroscopy` glossary entry) still described the
four-band set months after the code was right.

So these tests guard three separate failure modes:

1. the band tuple drifting from the Primer's own table;
2. user-visible copy describing a band set the pipeline does not use;
3. `data/planets.json` carrying colours computed through a *different* band set than the code
   describes — the worst one, because the page reads as correct while every Roman swatch on it
   was integrated through the wrong filters, and nothing on screen says so.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pipeline.config import INSTRUMENTS, ROMAN_CGI

_ROOT = Path(__file__).resolve().parents[1]
_PLANETS = _ROOT / "data" / "planets.json"

# Roman Coronagraph Primer, Community Participation Program, 8 January 2025, p.5 — the mode
# table, verbatim: band, central wavelength, bandwidth. Band 2 (660 nm) is on the filter wheel
# but is not in this table, because it is not a supported observing mode.
PRIMER_TABLE = (
    ("cgi-575", 575.0, 0.10),
    ("cgi-730", 730.0, 0.15),
    ("cgi-825", 825.0, 0.10),
)
PRIMER_URL = "https://roman.ipac.caltech.edu/docs/RomanCoronagraphPrimer_Current.pdf"


def test_the_band_set_is_the_primers_table():
    """If this fails, either the Primer was superseded — in which case cite the new document
    here — or someone reintroduced a number from nowhere."""
    got = tuple((b.id, b.center_nm, b.bandwidth_frac) for b in ROMAN_CGI.bands)
    assert got == PRIMER_TABLE, f"band set no longer matches {PRIMER_URL} p.5"


def test_no_band_is_named_660_or_835():
    """The two centres that came from nowhere. 835 nm was never a CGI band at all; 660 nm is
    real hardware but not a supported mode, so it must not be in the modelled set."""
    ids = {b.id for b in ROMAN_CGI.bands}
    assert "cgi-835" not in ids
    assert "cgi-660" not in ids


# ── the copy cannot describe a different instrument than the code uses ──────────────────

# Files that state the band set to a reader. Not an exhaustive list of the repo — it is the
# set of places a wrong number is actually visible to someone.
_COPY_GLOBS = ("web/templates/*.html", "web/templates/fragments/*.html", "web/static/*.js")
_COPY_FILES = ("data/glossary.json", "data/tours.json", "data/roman-targets.json")

# Phrasings that can only be true of the discredited four-band set. `660` alone is allowed:
# saying the filter exists but is untested is correct and worth saying.
_FORBIDDEN = (
    re.compile(r"835\s*(&nbsp;)?nm", re.I),
    re.compile(r"cgi-835|cgi-660"),
    re.compile(r"Roman'?s four (coronagraph )?(bands|filters)", re.I),
    re.compile(r"(four|4) (band )?samples", re.I),
)


def _copy_paths() -> list[Path]:
    paths: list[Path] = []
    for glob in _COPY_GLOBS:
        paths += sorted(_ROOT.glob(glob))
    paths += [_ROOT / f for f in _COPY_FILES if (_ROOT / f).exists()]
    return paths


@pytest.mark.parametrize("path", _copy_paths(), ids=lambda p: p.name)
def test_no_user_visible_copy_describes_the_old_band_set(path):
    text = path.read_text()
    for pattern in _FORBIDDEN:
        hit = pattern.search(text)
        assert not hit, (
            f"{path.relative_to(_ROOT)} still describes the pre-2026-08 band set "
            f"({hit.group(0)!r}). The supported set is 575/10%, 730/15%, 825/10%."
        )


def test_the_supported_widths_are_stated_where_they_are_claimed():
    """/how tells the reader the numbers; they have to be these numbers."""
    how = (_ROOT / "web" / "templates" / "how.html").read_text()
    assert "575" in how and "730" in how and "825" in how
    assert "15%" in how, "the 730 nm width is the one that was wrong for longest"


# ── the shipped data has to agree with the code ────────────────────────────────────────


@pytest.mark.skipif(not _PLANETS.exists(), reason="data/planets.json not on disk")
def test_the_emitted_data_uses_the_same_bands_as_the_code():
    """The trap this project actually fell into: `data/planets.json` is gitignored and fetched
    from a GitHub release, so a stale release quietly pairs three-band copy with four-band
    colours. Every Roman swatch is then wrong, and nothing on the page can tell you."""
    doc = json.loads(_PLANETS.read_text())
    expected = [b.id for b in ROMAN_CGI.bands]
    for rec in doc["planets"][:200]:
        for view in rec.get("instrument_views", []):
            if view["instrument_id"] != ROMAN_CGI.id:
                continue
            got = [s["band_id"] for s in view["band_samples"]["samples"]]
            assert got == expected, (
                f"{rec['id']}: data was built through {got}, code describes {expected} — "
                "re-emit the catalogue (`pipeline build --bulk 10000`) and publish a release"
            )


@pytest.mark.skipif(not _PLANETS.exists(), reason="data/planets.json not on disk")
def test_the_data_header_describes_every_instrument_it_used():
    """The header block exists so a reader can tell two releases apart without a version bump."""
    doc = json.loads(_PLANETS.read_text())
    named = {i["id"] for i in doc.get("instruments", [])}
    assert set(INSTRUMENTS) <= named, f"header names {named}, code has {set(INSTRUMENTS)}"
