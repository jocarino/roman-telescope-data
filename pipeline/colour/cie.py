"""The one codepath: reflected flux F(lambda) on GRID_NM -> perceptual colour.

Both the "true colour" (dense model spectrum) and the "Roman view" (reconstructed from
four bands) funnel through `reflected_flux_to_colour`. Nothing here branches on data
source — that is the whole architectural point.

Conventions (documented, consistent):
  - We do NOT white-balance to the host star. The reflected light keeps the star's tint,
    so a flat-albedo planet around the warm (5772 K) Sun reads cream, not pure white.
  - The swatch `hex` is a COLOUR IDENTITY: chromaticity rendered at a fixed display
    luminance (config.BASE_SWATCH_LUMINANCE_Y) so low-albedo worlds don't render near-black.
  - True brightness is reported separately as `luminance_y`: the planet's luminance
    relative to a perfect-white (albedo=1) planet under the same star, in [0, 1]. This is
    where "dark" lives.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from colour import MSDS_CMFS, SpectralDistribution, XYZ_to_sRGB, sd_to_XYZ

from pipeline.config import BASE_SWATCH_LUMINANCE_Y, GRID_ID, GRID_NM

_CMFS = MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]


@dataclass(frozen=True)
class ColourResult:
    method: str  # "full-spectrum" | "band-reconstruction"
    hex: str
    srgb: tuple[int, int, int]  # 0-255, gamma-encoded, clamped
    xyz: tuple[float, float, float]  # normalised to the display luminance
    luminance_y: float  # TRUE relative brightness in [0,1] (planet / white planet)
    out_of_gamut: bool
    confidence: str  # "high" | "medium" | "low"


def _flux_to_xyz(flux: np.ndarray) -> np.ndarray:
    """Absolute (arbitrary-scale) XYZ of a reflected-flux SPD on GRID_NM."""
    sd = SpectralDistribution(dict(zip(GRID_NM, np.asarray(flux, dtype=float), strict=True)))
    # illuminant=None -> treat F as the SPD of a light source (emission), which is exactly
    # what reflected planetary light is. method='Integration' handles our 5 nm grid.
    return np.asarray(sd_to_XYZ(sd, cmfs=_CMFS, illuminant=None, method="Integration"))


def reflectance_luminance(flux_planet: np.ndarray, flux_white: np.ndarray) -> float:
    """Luminance of the planet's reflected light relative to a perfect-white planet under
    the same star. The luminance-weighted mean albedo — the honest 'how bright'."""
    y_planet = _flux_to_xyz(flux_planet)[1]
    y_white = _flux_to_xyz(flux_white)[1]
    if y_white <= 0:
        return 0.0
    return float(np.clip(y_planet / y_white, 0.0, 1.0))


def reflected_flux_to_colour(
    flux: np.ndarray,
    *,
    method: str,
    illuminant_flux: np.ndarray | None = None,
    confidence: str = "high",
    grid_id: str = GRID_ID,
) -> ColourResult:
    """Convert a reflected-flux curve to a ColourResult.

    Parameters
    ----------
    flux:
        F(lambda) = A(lambda) * S(lambda) on GRID_NM.
    method:
        Provenance of the curve ("full-spectrum" or "band-reconstruction").
    illuminant_flux:
        The star's spectrum S(lambda) on GRID_NM (i.e. the flux of an albedo=1 planet).
        Used to compute the true relative luminance. If None, luminance_y falls back to the
        normalised display luminance (less meaningful).
    confidence:
        Capped to "low" for band-reconstruction by callers.
    """
    if grid_id != GRID_ID:
        raise ValueError(f"flux is on grid {grid_id!r}, expected {GRID_ID!r}")

    xyz_abs = _flux_to_xyz(flux)
    y_abs = xyz_abs[1]

    # Colour identity: preserve chromaticity, set luminance to the display convention.
    if y_abs > 0:
        xyz_norm = xyz_abs / y_abs * BASE_SWATCH_LUMINANCE_Y
    else:
        xyz_norm = np.zeros(3)

    # XYZ -> gamma-encoded sRGB (D65). Out-of-gamut shows up as channels outside [0,1].
    rgb = np.asarray(XYZ_to_sRGB(xyz_norm))
    out_of_gamut = bool(np.any(rgb < -1e-6) or np.any(rgb > 1.0 + 1e-6))
    rgb_clamped = np.clip(rgb, 0.0, 1.0)
    srgb_255 = tuple(int(round(c * 255)) for c in rgb_clamped)
    hex_code = "#{:02x}{:02x}{:02x}".format(*srgb_255)

    if illuminant_flux is not None:
        lum_y = reflectance_luminance(flux, illuminant_flux)
    else:
        lum_y = float(BASE_SWATCH_LUMINANCE_Y)

    return ColourResult(
        method=method,
        hex=hex_code,
        srgb=srgb_255,  # type: ignore[arg-type]
        xyz=tuple(float(v) for v in xyz_norm),  # type: ignore[arg-type]
        luminance_y=lum_y,
        out_of_gamut=out_of_gamut,
        confidence=confidence,
    )
