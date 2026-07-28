"""Index floats are rounded, and the rounding must not reorder the gallery's sorts.

Values used to reach the index at full float repr — distances like 0.00014630707286050534 pc,
luminances like 0.059143490457500454 — about 370 KB of digits that nothing reads. Every one is
either displayed hard-rounded (temperature as a whole number, radius to 1 dp) or used purely to
order a list, so the index now rounds them (web/build._r).

The risk is not visual, it is ordering: round too hard and planets that were distinct become
ties, and a sort silently shuffles. These tests pin both ends — enough precision that the sorts
survive, little enough that the digits actually go.
"""

from __future__ import annotations

import gzip
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
def _records() -> tuple:
    return tuple(PlanetsFile.model_validate_json(PLANETS_JSON.read_text()).planets)


@lru_cache(maxsize=1)
def _entries() -> tuple:
    return tuple(_index_entry(r) for r in _records())


def _decimals(value: float) -> int:
    text = repr(value)
    return len(text.split(".")[1]) if "." in text and "e" not in text else 0


# Field -> the precision the index promises. Anything finer is digits on the wire.
_INDEX_PRECISION = {"temp": 2, "dist": 8, "lum": 7, "de": 4, "radius": 4, "dist_ly": 1}
_EXTRA_PRECISION = {"starTeff": 1, "metal": 3, "mass": 4, "sma": 6, "ra": 2, "dec": 2}


@pytest.mark.parametrize("field", sorted(_INDEX_PRECISION))
def test_index_floats_are_rounded(field: str) -> None:
    limit = _INDEX_PRECISION[field]
    for entry in _entries():
        value = entry.get(field)
        if isinstance(value, float):
            assert _decimals(value) <= limit, f"{entry['id']}.{field} = {value!r}"


@pytest.mark.parametrize("field", sorted(_EXTRA_PRECISION))
def test_extra_floats_are_rounded(field: str) -> None:
    limit = _EXTRA_PRECISION[field]
    for rec in _records():
        value = _extra_entry(rec).get(field)
        if isinstance(value, float):
            assert _decimals(value) <= limit, f"{rec.id}.{field} = {value!r}"


@pytest.mark.parametrize(
    ("field", "reverse", "raw"),
    [
        ("temp", True, lambda r: r.params.equilibrium_temp_k),
        ("lum", True, lambda r: r.true_colour.luminance_y),
        ("dist", False, lambda r: r.params.distance_pc),
    ],
)
def test_rounding_preserves_the_sort_order(field: str, reverse: bool, raw) -> None:
    """Sorting on the rounded value must give the same order as the unrounded value.

    A handful of genuine ties are tolerated — planets whose values agree to the promised
    precision really are indistinguishable on that axis — but a wholesale reshuffle means the
    precision was cut too far.
    """
    recs = _records()
    entries = _entries()
    miss = -1e18 if reverse else 1e18

    def order(key):
        idx = sorted(range(len(recs)), key=lambda i: (key(i) if key(i) is not None else miss),
                     reverse=reverse)
        return [recs[i].id for i in idx]

    exact = order(lambda i: raw(recs[i]))
    rounded = order(lambda i: entries[i].get(field))
    moved = sum(1 for a, b in zip(exact, rounded, strict=True) if a != b)
    assert moved < len(recs) * 0.02, f"{field}: {moved} of {len(recs)} positions moved"


def test_rounding_actually_shrinks_the_index_on_the_wire() -> None:
    """The whole point. Measured gzipped, because that is what a visitor downloads."""
    rounded = list(_entries())
    unrounded = [
        {**e,
         "lum": r.true_colour.luminance_y,
         "dist": r.params.distance_pc,
         "temp": r.params.equilibrium_temp_k,
         "radius": r.params.radius_r_earth,
         "de": (r.instrument_views[0].reconstruction_error.delta_e2000
                if r.instrument_views[0].reconstruction_error else 0.0)}
        for e, r in zip(rounded, _records(), strict=True)
    ]

    def wire(rows: list[dict]) -> int:
        return len(gzip.compress(json.dumps(rows, separators=(",", ":")).encode(), 6))

    assert wire(rounded) < wire(unrounded) * 0.85
