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

# Target lightnesses for the ramp (shade-2 .. tint-2). The base swatch is separate.
_RAMP = (
    ("shade-2", 0.18),
    ("shade-1", 0.34),
    ("base", None),  # keep the base colour's own lightness
    ("tint-1", 0.72),
    ("tint-2", 0.88),
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


def _with_lightness(hexcode: str, lightness: float | None) -> str:
    r, g, b = _hex_to_rgb01(hexcode)
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    if lightness is not None:
        light = lightness
    return _rgb01_to_hex(colorsys.hls_to_rgb(hue, light, sat))


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


def derive_palette(base: ColourResult) -> list[PaletteStop]:
    return [
        PaletteStop(hex=_with_lightness(base.hex, lightness), role=role)
        for role, lightness in _RAMP
    ]
