"""Reconstruct an albedo curve on GRID_NM from a sparse BandSampleSet.

The honesty problem, stated in code: Roman's three supported bands span 575-825 nm. There is
ZERO information below 575 nm — exactly the blue/violet region where these planets are often
blue. So we interpolate a narrow yellow->red span and *extrapolate the entire blue half of
human vision*. Policy:

  - Anchor each band value at its centre wavelength.
  - PCHIP (shape-preserving, monotone between samples) between the outer anchors — never a
    natural cubic spline, which would invent absorption bumps between three sparse points.
  - Flat hold (clamped >= 0) outside the anchor span. Never linear-extrapolate.
  - Record where extrapolation begins so the UI can hatch the 'guessed' zone.

Three anchors, not four -- and, measured, that is BETTER than the four we had wrong. Over the
whole catalogue, correcting the band set to the flight configuration moved dE2000 against the
full spectrum DOWN for 5,363 of 5,764 planets (mean 17.96 -> 16.76); 401 got worse, the worst
by +1.0. 4,424 swatches changed colour.

Which is counter-intuitive, so the likely mechanism, stated as a hypothesis rather than a
result: the win is not the band count, it is Band 3 widening from 6% to 15%. The old 730/6%
anchor was a 44 nm slit, and the old top anchor at 835/15% integrated 772-898 nm -- mostly
near-IR, where albedo can diverge sharply from the visible red, yet it still dragged the
PCHIP curve across 730-780 nm, which IS visible. The corrected 730/15% band spans 675-785 nm,
so the red end of human vision is now anchored by a value that actually represents it.
Losing Band 2's 640-680 nm anchor costs less than that gains.

The top anchor is still weaker than it looks: 825 nm sits past the CIE cutoff, where the
colour-matching functions are ~0, so it shapes the curve but contributes almost nothing to
the colour directly. The visible reconstruction effectively leans on two samples.
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
