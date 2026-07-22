"""Cahoy et al. 2010 albedo-grid provider.

The Cahoy grid is a set of precomputed geometric-albedo spectra for Jupiter/Neptune-class
planets over a small parameter space: star-planet distance (≈0.8, 2, 5, 10 AU) × metallicity
(1, 3, 10, 30× solar), cloudy and cloud-free. These are the reference spectra the Roman
Coronagraph community uses, so they are an excellent validated source for cool giants.

This provider is ACTIVATED by populating `data/cahoy_grid/` with the grid files plus a
`manifest.json`; until then `make_cahoy()` raises ProviderUnavailable and the router falls
back. No grid files ship with the repo (licensing / size).

Expected layout (`data/cahoy_grid/manifest.json`):
    {
      "points": [
        {"dist_au": 2.0, "metallicity": 1.0, "cloud": "cloudy", "file": "d2_m1_cloudy.csv"},
        ...
      ]
    }
Each referenced file is CSV with two columns: wavelength_nm, geometric_albedo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pipeline.config import CAHOY_GRID_DIR
from pipeline.spectrum.base import ProviderUnavailable


@dataclass(frozen=True)
class _GridPoint:
    dist_au: float
    metallicity: float
    cloud: str
    wavelengths_nm: np.ndarray
    albedo: np.ndarray


def _load_manifest(grid_dir: Path) -> list[_GridPoint]:
    manifest = grid_dir / "manifest.json"
    if not grid_dir.exists() or not manifest.exists():
        raise ProviderUnavailable(
            f"Cahoy grid not found at {grid_dir} (no manifest.json). "
            "Populate it to activate the CahoyProvider; see docs."
        )
    spec = json.loads(manifest.read_text())
    points: list[_GridPoint] = []
    for p in spec.get("points", []):
        arr = np.loadtxt(grid_dir / p["file"], delimiter=",")
        points.append(
            _GridPoint(
                dist_au=float(p["dist_au"]),
                metallicity=float(p["metallicity"]),
                cloud=str(p.get("cloud", "cloudy")),
                wavelengths_nm=arr[:, 0],
                albedo=arr[:, 1],
            )
        )
    if not points:
        raise ProviderUnavailable(f"Cahoy manifest at {grid_dir} lists no points.")
    return points


class CahoyProvider:
    """Nearest-point (in log-distance, log-metallicity) Cahoy albedo, interpolated onto the
    requested wavelength grid. v1 uses nearest neighbour; bilinear interpolation across the
    four surrounding grid points is a straightforward upgrade."""

    def __init__(self, point: _GridPoint):
        self._point = point

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        alb = np.interp(wl, self._point.wavelengths_nm, self._point.albedo)
        return np.clip(alb, 0.0, 1.0)


def _nearest(points: list[_GridPoint], dist_au: float, metallicity: float) -> _GridPoint:
    def cost(p: _GridPoint) -> float:
        return (np.log10(p.dist_au) - np.log10(max(dist_au, 0.1))) ** 2 + (
            np.log10(p.metallicity) - np.log10(max(metallicity, 0.1))
        ) ** 2

    return min(points, key=cost)


def make_cahoy(
    *,
    semi_major_axis_au: float | None,
    metallicity: float,
    grid_dir: Path = CAHOY_GRID_DIR,
    **_ignored,
) -> CahoyProvider:
    """Factory for the router. Raises ProviderUnavailable if the grid is not installed."""
    points = _load_manifest(grid_dir)  # raises ProviderUnavailable if absent
    dist = semi_major_axis_au if semi_major_axis_au is not None else 2.0
    return CahoyProvider(_nearest(points, dist, metallicity))
