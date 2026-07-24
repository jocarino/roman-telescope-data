"""Measured full-disk albedo spectra — the solar system anchors.

Unlike every other provider, this one holds a real measured curve (see
data/measured_albedo/README.md for provenance) and just interpolates it onto the requested
wavelengths. It satisfies the same SpectrumProvider protocol, so the whole pipeline —
CIE conversion, palette, Roman band view, phase colours — runs byte-identically on a
measurement as on a model. That is the point: where we can check the pipeline against a
photographed planet, we do.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from pipeline.spectrum.base import ProviderUnavailable

MEASURED_DIR = Path("data/measured_albedo")
_KARKOSCHKA_FILE = "karkoschka1998_low.tab"
_EARTH_FILE = "earth_payne2026.csv"

# Column index (0-based) of each planet's albedo in the Karkoschka table, per its PDS
# label: [vacuum nm, air nm, CH4 coeff, Jupiter, Saturn, Uranus, Neptune, Titan].
_KARKOSCHKA_COLUMNS = {"jupiter": 3, "saturn": 4, "uranus": 5, "neptune": 6, "titan": 7}


@dataclass(frozen=True)
class MeasuredAlbedo:
    """A measured albedo curve, interpolated to any requested wavelengths. Outside the
    measured range the edge value is held (constant extrapolation) — only relevant beyond
    1050 nm for Karkoschka, past every band we integrate."""

    wavelengths_nm: np.ndarray = field(repr=False)
    albedo: np.ndarray = field(repr=False)
    source: str  # short engine tag recorded in params.spectrum_source

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        return np.interp(wl, self.wavelengths_nm, self.albedo)


def karkoschka1998(planet: str, data_dir: Path = MEASURED_DIR) -> MeasuredAlbedo:
    """One planet's full-disk albedo from Karkoschka's 1995 ESO spectra (300-1050 nm)."""
    path = data_dir / _KARKOSCHKA_FILE
    if not path.exists():
        raise ProviderUnavailable(f"Karkoschka table missing: {path}")
    col = _KARKOSCHKA_COLUMNS[planet]
    table = np.loadtxt(path)
    # Air wavelength (column 1) is the appropriate axis for ground-based CCD data; the
    # air-vacuum offset (~0.3 nm) is far below anything colour can perceive anyway.
    return MeasuredAlbedo(
        wavelengths_nm=table[:, 1], albedo=table[:, col], source="karkoschka1998"
    )


def payne2026_earth(data_dir: Path = MEASURED_DIR) -> MeasuredAlbedo:
    """Earth's geometric albedo from the Payne et al. 2026 calibrated composite (µm -> nm)."""
    path = data_dir / _EARTH_FILE
    if not path.exists():
        raise ProviderUnavailable(f"Earth albedo file missing: {path}")
    table = np.loadtxt(path, delimiter=",", skiprows=1)
    return MeasuredAlbedo(
        wavelengths_nm=table[:, 0] * 1000.0, albedo=table[:, 1], source="payne2026"
    )
