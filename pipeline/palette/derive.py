"""Derive a designer palette from a base colour: a 5-stop lightness ramp around the base
hue, plus optional accents sampled from spectral features (e.g. the colour of the light in
a specific wavelength window, like the methane band edge).
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

import numpy as np

from pipeline.colour.cie import ColourResult, reflected_flux_to_colour
from pipeline.config import GRID_NM

# Five evenly spaced lightness stops across a fixed span. The ramp is a DERIVED design object:
# it carries the planet's hue and chroma, but not its lightness, and no stop claims to BE the
# planet's colour -- that lives in the base swatch and its hex, shown separately and exactly.
#
# It used to: keep the middle stop at the base colour's own lightness and place the others at
# fixed targets (0.18 / 0.34 / - / 0.72 / 0.88). That silently assumed the base landed between
# 0.34 and 0.72, but every base swatch is chromaticity-preserved and pinned to
# BASE_SWATCH_LUMINANCE_Y = 0.60 linear, which gamma-encodes to HLS L ~ 0.80 for near-neutral
# colours. So the base sat ABOVE tint-1 for 682 of 953 planets and the ramp ran
# 0.18 -> 0.34 -> 0.81 -> 0.72 -> 0.88: up, back down, then up. Some planets (HD 156279 b,
# Kepler-424 c) emitted the same hex twice, making a "5-stop" palette with 4 distinct colours.
_RAMP_L_MIN = 0.18
_RAMP_L_MAX = 0.88
_RAMP_ROLES = ("shade-2", "shade-1", "mid", "tint-1", "tint-2")
_RAMP: tuple[tuple[str, float], ...] = tuple(
    (role, _RAMP_L_MIN + (_RAMP_L_MAX - _RAMP_L_MIN) * i / (len(_RAMP_ROLES) - 1))
    for i, role in enumerate(_RAMP_ROLES)
)


@dataclass(frozen=True)
class PaletteStop:
    hex: str
    role: str
    source_nm: float | None = None


def _hex_to_rgb01(hexcode: str) -> tuple[float, float, float]:
    h = hexcode.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb01_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(round(c * 255)) for c in rgb))


def _with_lightness(hexcode: str, lightness: float) -> str:
    r, g, b = _hex_to_rgb01(hexcode)
    hue, _light, sat = colorsys.rgb_to_hls(r, g, b)
    return _rgb01_to_hex(colorsys.hls_to_rgb(hue, lightness, sat))


def spectral_accent(
    flux: np.ndarray, lo_nm: float, hi_nm: float, illuminant_flux: np.ndarray
) -> PaletteStop:
    """Colour of the reflected light restricted to a wavelength window — an accent that
    literally shows the hue of a spectral feature."""
    mask = (GRID_NM >= lo_nm) & (GRID_NM <= hi_nm)
    windowed = np.where(mask, flux, 0.0)
    colour = reflected_flux_to_colour(
        windowed, method="full-spectrum", illuminant_flux=illuminant_flux, confidence="low"
    )
    return PaletteStop(hex=colour.hex, role="accent", source_nm=float((lo_nm + hi_nm) / 2))


def derive_palette_from_hex(base_hex: str) -> list[PaletteStop]:
    """The ramp depends on nothing but the base colour, which is why palettes can be re-derived
    at site-build time from a stored hex without regenerating any spectra."""
    return [
        PaletteStop(hex=_with_lightness(base_hex, lightness), role=role)
        for role, lightness in _RAMP
    ]


def derive_palette(base: ColourResult) -> list[PaletteStop]:
    return derive_palette_from_hex(base.hex)
