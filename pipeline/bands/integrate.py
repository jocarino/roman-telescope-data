"""Simulate what an instrument would measure: integrate the model albedo through each
band's top-hat, star-weighted, to a scalar per band.

The value stored per band is the star-weighted mean geometric albedo in that band
    v_b = integral A(l) S(l) T_b(l) dl / integral S(l) T_b(l) dl
which is albedo-like (illuminant-normalised) and is the quantity a CGI contrast
measurement most directly constrains. This is the `source="simulated"` branch of the swap
seam; a `source="measured"` BandSampleSet has the same shape with real v_b values.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pipeline.config import Instrument
from pipeline.illuminant.base import Illuminant
from pipeline.spectrum.base import SpectrumProvider

# Fine grid resolution used to integrate within a band (nm).
_BAND_INTEGRATION_STEP_NM = 1.0


@dataclass(frozen=True)
class BandSample:
    band_id: str
    center_nm: float
    value: float
    uncertainty: float | None = None


@dataclass(frozen=True)
class BandSampleSet:
    instrument_id: str
    source: str  # "simulated" | "measured"
    epoch: str | None
    samples: tuple[BandSample, ...]

    @property
    def centers_nm(self) -> np.ndarray:
        return np.array([s.center_nm for s in self.samples])

    @property
    def values(self) -> np.ndarray:
        return np.array([s.value for s in self.samples])


def simulate_band_samples(
    provider: SpectrumProvider,
    illuminant: Illuminant,
    instrument: Instrument,
) -> BandSampleSet:
    samples: list[BandSample] = []
    for band in instrument.bands:
        step = _BAND_INTEGRATION_STEP_NM
        wl = np.arange(band.lo_nm, band.hi_nm + step / 2, step)
        albedo = provider.geometric_albedo(wl)
        star = illuminant.spectrum(wl)
        # Top-hat weighting is uniform across [lo, hi]; the star provides the weighting.
        denom = np.trapezoid(star, wl)
        value = float(np.trapezoid(albedo * star, wl) / denom) if denom > 0 else 0.0
        samples.append(BandSample(band_id=band.id, center_nm=band.center_nm, value=value))
    return BandSampleSet(
        instrument_id=instrument.id,
        source="simulated",
        epoch=None,
        samples=tuple(samples),
    )
