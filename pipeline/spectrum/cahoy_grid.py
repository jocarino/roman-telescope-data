"""Cahoy et al. 2010 albedo-grid provider.

The Cahoy grid is a set of precomputed geometric-albedo spectra for Jupiter/Neptune-class
planets over a small parameter space: star-planet distance (≈0.8, 2, 5, 10 AU) × metallicity
(Jupiters at 1, 3× solar; Neptunes at 10, 30×), each PHASE-RESOLVED from 0° (full) to 180°
(new) in 10° steps. These are the reference spectra the Roman Coronagraph community uses.

This provider is ACTIVATED by populating `data/cahoy_grid/` with the grid files plus a
`manifest.json` (see `cahoy_ingest.py`); until then `make_cahoy()` raises ProviderUnavailable
and the router falls back. No grid files ship with the upstream distribution's licence bundle.

Expected layout (`data/cahoy_grid/manifest.json`):
    {
      "points": [
        {"dist_au": 2.0, "metallicity": 1.0, "cloud": "cahoy", "planet": "Jupiter",
         "phase_files": {"0": "Jupiter_1x_2AU_000deg.csv", "10": ..., ..., "180": ...}},
        ...
      ]
    }
Each referenced file is CSV with two columns: wavelength_nm, albedo (phase-resolved — the
non-zero-phase files include the brightness fall-off, not just a spectral shape).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from pipeline.config import CAHOY_GRID_DIR
from pipeline.spectrum.base import ProviderUnavailable


@dataclass(frozen=True)
class _GridPoint:
    dist_au: float
    metallicity: float
    cloud: str
    # phase angle (deg, ascending) -> (wavelengths_nm, albedo)
    phases: dict[int, tuple[np.ndarray, np.ndarray]]


@lru_cache(maxsize=4)  # the grid is ~300 files; load it once per process, not once per planet
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
        phase_files = p.get("phase_files")
        if not phase_files or "0" not in phase_files:
            continue  # a point without a full-phase spectrum is unusable
        phases: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        for deg_str, fname in phase_files.items():
            arr = np.loadtxt(grid_dir / fname, delimiter=",")
            phases[int(deg_str)] = (arr[:, 0], arr[:, 1])
        points.append(
            _GridPoint(
                dist_au=float(p["dist_au"]),
                metallicity=float(p["metallicity"]),
                cloud=str(p.get("cloud", "cahoy")),
                phases=phases,
            )
        )
    if not points:
        raise ProviderUnavailable(f"Cahoy manifest at {grid_dir} lists no usable points.")
    return points


class CahoyProvider:
    """Nearest-point (in log-distance, log-metallicity) Cahoy albedo, interpolated onto the
    requested wavelength grid. Phase-resolved: `albedo_at_phase` linearly interpolates
    between the two bracketing phase spectra of the same grid point."""

    def __init__(self, point: _GridPoint):
        self._point = point
        self._degs = sorted(point.phases.keys())

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        return self.albedo_at_phase(wavelengths_nm, 0.0)

    def albedo_at_phase(self, wavelengths_nm: np.ndarray, phase_deg: float) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        degs = self._degs
        a = np.clip(phase_deg, degs[0], degs[-1])
        hi_i = int(np.searchsorted(degs, a))
        if degs[min(hi_i, len(degs) - 1)] == a or hi_i == 0:
            deg = degs[min(hi_i, len(degs) - 1)]
            wl_g, alb_g = self._point.phases[deg]
            return np.clip(np.interp(wl, wl_g, alb_g), 0.0, 1.0)
        lo, hi = degs[hi_i - 1], degs[hi_i]
        w = (a - lo) / (hi - lo)
        wl_lo, alb_lo = self._point.phases[lo]
        wl_hi, alb_hi = self._point.phases[hi]
        alb = (1.0 - w) * np.interp(wl, wl_lo, alb_lo) + w * np.interp(wl, wl_hi, alb_hi)
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
