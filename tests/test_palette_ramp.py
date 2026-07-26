"""The 5-stop ramp must be a usable lightness ramp for EVERY base colour.

Regression cover for the ramp inversion: the middle stop used to keep the base colour's own
lightness while the tints sat at fixed 0.72 / 0.88. Because every base swatch is pinned to
BASE_SWATCH_LUMINANCE_Y = 0.60 linear (HLS L ~ 0.80 for near-neutral colours), the middle stop
overshot the tints on 682 of 953 released planets, and some emitted the same hex twice.
"""

from __future__ import annotations

import colorsys

import pytest

from pipeline.colour.cie import ColourResult
from pipeline.palette.derive import derive_palette, derive_palette_from_hex

# Base colours that actually appear in released data, chosen to span the failure modes:
# the screenshot planet, the two that emitted duplicate stops, a saturated hot Jupiter blue,
# a dark world, and the extremes of the observed base-lightness range (L 0.50 .. 0.85).
REAL_BASES = [
    "#c4ccd9",  # TOI-6109 c / Kepler-192 b -- L 0.810, the reported inversion
    "#70bfff",  # HD 156279 b / Kepler-424 c -- used to emit this hex twice
    "#64b6ff",  # L 0.696: base and tint-1 collapsed to near-identical colours
    "#71caff",
    "#dadfe7",
    "#242c38",
    "#ffffff",  # achromatic extremes: saturation is 0, only lightness moves
    "#000000",
    "#ff0000",  # fully saturated primaries
    "#00ff00",
    "#0000ff",
]


def _lightness(hexcode: str) -> float:
    h = hexcode.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[1]


@pytest.mark.parametrize("base", REAL_BASES)
def test_ramp_lightness_is_strictly_increasing(base: str) -> None:
    stops = derive_palette_from_hex(base)
    lightness = [_lightness(s.hex) for s in stops]
    assert lightness == sorted(lightness), f"{base} -> {[s.hex for s in stops]}"
    assert all(b - a > 0.05 for a, b in zip(lightness, lightness[1:], strict=False)), (
        f"stops too close to be distinct: {base} -> {lightness}"
    )


@pytest.mark.parametrize("base", REAL_BASES)
def test_ramp_stops_are_distinct_colours(base: str) -> None:
    stops = derive_palette_from_hex(base)
    assert len({s.hex for s in stops}) == 5, f"{base} -> {[s.hex for s in stops]}"


@pytest.mark.parametrize("base", [b for b in REAL_BASES if b not in {"#ffffff", "#000000"}])
def test_ramp_preserves_the_planets_hue(base: str) -> None:
    """The whole point of the ramp is that it is the PLANET's colour family. Lightness is
    replaced; hue is not. (Achromatic bases are excluded: hue is undefined at zero chroma.)"""
    base_hue = _hue(base)
    for stop in derive_palette_from_hex(base):
        if _saturation(stop.hex) == 0:  # a stop can quantise to grey at the ramp extremes
            continue
        assert abs(_hue(stop.hex) - base_hue) < 0.02, f"{base} -> {stop.hex}"


def _hue(hexcode: str) -> float:
    h = hexcode.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[0]


def _saturation(hexcode: str) -> float:
    h = hexcode.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[2]


def test_no_stop_claims_to_be_the_planets_colour() -> None:
    """Honesty guard: the palette must not label a re-lightened stop "base". The planet's
    actual colour is shown separately as the swatch and its hex."""
    roles = [s.role for s in derive_palette_from_hex("#c4ccd9")]
    assert roles == ["shade-2", "shade-1", "mid", "tint-1", "tint-2"]


def test_derive_palette_matches_hex_entry_point() -> None:
    colour = ColourResult(
        method="full-spectrum",
        hex="#c4ccd9",
        srgb=(196, 204, 217),
        xyz=(0.57, 0.60, 0.72),
        luminance_y=0.31,
        out_of_gamut=False,
        confidence="high",
    )
    assert derive_palette(colour) == derive_palette_from_hex("#c4ccd9")
