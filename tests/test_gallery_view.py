"""The gallery's "seen from Roman" view: the index fields it filters and sorts on.

The whole point of the view is that every colour-derived control (the colour-family chips, the
brightness sort, the similar-colour sort) re-keys onto Roman's band-view colour. That only holds
if the index carries the Roman colour *as its own* family/brightness/palette — deriving either
of them from the full-spectrum colour by accident would leave the filters quietly lying.
"""

from __future__ import annotations

from pipeline.colour.family import colour_family
from pipeline.palette.derive import derive_palette_from_hex
from tests.test_tours import make_record
from web.build import _index_entry, _stats

# Deliberately far apart in hue: a full-spectrum blue that Roman's red-weighted bands turn warm.
_TRUE_SRGB = (90, 120, 210)
_ROMAN_SRGB = (205, 120, 60)


def _record(pid: str = "test-1b", *, roman_srgb: tuple[int, int, int] = _ROMAN_SRGB):
    """A record whose two views land in different colour families."""
    rec = make_record(pid, hex_="#5a78d2", roman_hex="#cd783c")
    rec.true_colour.srgb = list(_TRUE_SRGB)
    rv = rec.instrument_views[0].colour
    rv.srgb = list(roman_srgb)
    rv.luminance_y = 0.123456789
    rv.palette = [
        s.model_copy(update={"hex": h})
        for s, h in zip(
            rv.palette * 5,
            ["#1a0f07", "#5c3a1d", "#9c6534", "#cd783c", "#e6b58f"],
            strict=False,
        )
    ]
    return rec


def test_index_entry_carries_the_roman_colour_separately():
    e = _index_entry(_record())
    assert e["hex"] == "#5a78d2"
    assert e["rhex"] == "#cd783c"
    # The 5-stop ramps are no longer shipped in the index — they are a pure function of these
    # two hexes and the browser derives them (PlanetRender.ramp; parity pinned by
    # tests/test_palette_ramp_js.py). Both hexes are here, so both ramps stay recoverable.
    assert "rpal" not in e and "palette" not in e
    assert [s.hex for s in derive_palette_from_hex(e["rhex"])] == [
        "#492913", "#905125", "#ce7b40", "#e0ac87", "#f3ddce"
    ]
    assert derive_palette_from_hex(e["rhex"]) != derive_palette_from_hex(e["hex"])


def test_roman_family_comes_from_the_roman_colour():
    e = _index_entry(_record())
    assert e["family"] == colour_family(_TRUE_SRGB)
    assert e["rfam"] == colour_family(_ROMAN_SRGB)
    # The filter is only meaningful if flipping the view can actually move a planet.
    assert e["rfam"] != e["family"]


def test_roman_brightness_is_the_roman_luminance():
    e = _index_entry(_record())
    assert e["rlum"] == 0.12346  # rounded for index size, still 5 dp of ordering
    assert e["rlum"] != e["lum"]


def test_family_shift_pct_counts_planets_that_change_family():
    shifts = _record("shifts-b")
    stays = _record("stays-b", roman_srgb=_TRUE_SRGB)
    assert _stats([shifts, stays])["family_shift_pct"] == 50
    assert _stats([stays])["family_shift_pct"] == 0
    assert _stats([])["family_shift_pct"] == 0
