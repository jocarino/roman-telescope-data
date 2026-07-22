"""Reconstruct an albedo curve on GRID_NM from a sparse BandSampleSet.

The honesty problem, stated in code: Roman's four bands span 575-835 nm. There is ZERO
information below 575 nm — exactly the blue/violet region where these planets are often
blue. So we interpolate a narrow yellow->red span and *extrapolate the entire blue half of
human vision*. Policy:

  - Anchor each band value at its centre wavelength.
  - PCHIP (shape-preserving, monotone between samples) between the outer anchors — never a
    natural cubic spline, which would invent absorption bumps between four sparse points.
  - Flat hold (clamped >= 0) outside the anchor span. Never linear-extrapolate.
  - Record where extrapolation begins so the UI can hatch the 'guessed' zone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import PchipInterpolator

from pipeline.bands.integrate import BandSampleSet
from pipeline.config import GRID_ID, GRID_NM


@dataclass(frozen=True)
class ReconstructedCurve:
    grid_id: str
    values: np.ndarray  # reconstructed albedo on GRID_NM
    interpolant: str  # "pchip"
    extrapolated_below_nm: float
    extrapolated_above_nm: float


def reconstruct_curve(samples: BandSampleSet) -> ReconstructedCurve:
    centers = samples.centers_nm
    values = samples.values
    order = np.argsort(centers)
    centers = centers[order]
    values = values[order]

    lo, hi = float(centers[0]), float(centers[-1])
    pchip = PchipInterpolator(centers, values, extrapolate=False)

    grid = GRID_NM
    recon = pchip(grid)
    # Flat hold outside the anchor span (PchipInterpolator returns NaN there).
    recon = np.where(grid < lo, values[0], recon)
    recon = np.where(grid > hi, values[-1], recon)
    recon = np.clip(recon, 0.0, None)

    return ReconstructedCurve(
        grid_id=GRID_ID,
        values=recon,
        interpolant="pchip",
        extrapolated_below_nm=lo,
        extrapolated_above_nm=min(hi, float(grid[-1])),
    )
