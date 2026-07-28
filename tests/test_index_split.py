"""The gallery index and its companion extras file are zipped by position, not by id.

Every page that shows planets pays for the index on first load, so it carries only what the
grid needs. The star/orbit numbers (compare) and sky coordinates ("your sky tonight") live in
planets.extra.<build>.json, and the consumers merge the two arrays index by index — so the
alignment is load-bearing and pinned here.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pytest

from pipeline.models import PlanetsFile
from web.build import _extra_entry, _index_entry

PLANETS_JSON = Path("data/planets.json")

pytestmark = pytest.mark.skipif(
    not PLANETS_JSON.exists(), reason="needs a fetched data release"
)


@lru_cache(maxsize=1)
def _sample() -> tuple:
    """A slice of real records — enough to cover missing sky positions and null star fields."""
    doc = PlanetsFile.model_validate_json(PLANETS_JSON.read_text())
    return tuple(doc.planets[:40])

# Fields the split moved out of the index, and the ones that must have stayed.
_MOVED = {"starTeff", "starType", "metal", "mass", "sma", "year", "ra", "dec", "vmag"}
_DERIVED_CLIENT_SIDE = {"palette", "rpal"}
_GRID_NEEDS = {"id", "name", "host", "hex", "rhex", "family", "rfam", "lum", "rlum",
               "temp", "dist", "dist_ly", "de", "prov", "ptype", "disc", "hz", "srf",
               "radius", "cloud"}


def test_index_keeps_what_the_grid_needs() -> None:
    for rec in _sample():
        keys = set(_index_entry(rec))
        assert _GRID_NEEDS <= keys, f"{rec.id} lost {_GRID_NEEDS - keys}"


def test_index_no_longer_carries_the_split_out_fields() -> None:
    for rec in _sample():
        assert not (_MOVED & set(_index_entry(rec)))


def test_index_no_longer_carries_derivable_ramps() -> None:
    """The 5-stop ramps are a pure function of the base hex; the browser derives them.

    See tests/test_palette_ramp_js.py for the parity check that makes this safe.
    """
    for rec in _sample():
        assert not (_DERIVED_CLIENT_SIDE & set(_index_entry(rec)))


def test_extras_hold_the_moved_fields_and_nothing_else() -> None:
    for rec in _sample():
        assert set(_extra_entry(rec)) <= _MOVED


def test_extras_are_positionally_aligned_with_the_index() -> None:
    """The consumers zip by position, so the arrays must be the same length and order."""
    recs = _sample()
    index = [_index_entry(r) for r in recs]
    extra = [_extra_entry(r) for r in recs]
    assert len(index) == len(extra)
    for rec, i, e in zip(recs, index, extra, strict=True):
        merged = {**i, **e}
        assert merged["id"] == rec.id
        if rec.sky:
            assert merged["ra"] == round(rec.sky.ra_deg, 2)
        if rec.host_star.teff_k is not None:
            assert merged["starTeff"] == rec.host_star.teff_k


def test_both_files_are_json_serialisable() -> None:
    recs = _sample()
    assert json.loads(json.dumps([_index_entry(r) for r in recs]))
    assert json.loads(json.dumps([_extra_entry(r) for r in recs]))
