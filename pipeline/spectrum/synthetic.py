"""Parametric synthetic albedo — the v1 stand-in for the Cahoy 2010 grid / PICASO.

This is NOT a stand-in for the *colour pipeline* (that is real): it is a physically
motivated, analytic albedo model whose knobs (cloud fraction, methane band depth, Rayleigh
slope, sodium absorption) reproduce the qualitative behaviour the Milestone-1 sanity gate
checks:

  - cloudy Jupiter analog  -> bright, flat-ish continuum          -> warm off-white/cream
  - deep-methane Neptune-like -> red/near-IR eaten by CH4 bands   -> blue-green
  - cloud-free + no methane -> dark, sodium eats the yellow       -> dark / muted

A real Cahoy/PICASO provider slots in behind SpectrumProvider without touching anything
downstream. Everything here is deterministic — no network, no data files.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Approximate visible/near-IR methane (CH4) absorption band centres (nm) and relative
# strengths. Real CH4 has a forest of bands; these capture the dominant visible ones that
# drive the blue-green of the ice giants (the strong 619, 725, 790, 890 nm complexes).
_CH4_BANDS_NM = np.array([543.0, 619.0, 665.0, 705.0, 725.0, 790.0, 862.0, 890.0])
_CH4_STRENGTHS = np.array([0.10, 0.35, 0.15, 0.20, 0.55, 0.65, 0.45, 0.85])
_CH4_WIDTHS_NM = np.array([12.0, 18.0, 12.0, 15.0, 22.0, 28.0, 25.0, 35.0])

# Sodium (Na D) doublet ~589 nm — the yellow-eater in cloud-free hot Jupiters.
_NA_CENTER_NM = 589.0
_NA_WIDTH_NM = 30.0


@dataclass(frozen=True)
class SyntheticAlbedo:
    """Analytic geometric-albedo model.

    Parameters
    ----------
    cloud_albedo:
        Grey continuum reflectivity of the cloud deck (0..1). High = bright cloudy world.
    cloud_fraction:
        0 = cloud-free (dark, deep atmosphere), 1 = fully cloudy (bright continuum).
    methane:
        Methane abundance knob (0..~2). Scales the depth of the CH4 absorption bands that
        carve out the red/near-IR and push the colour blue-green.
    rayleigh:
        Strength of the blue-boosting Rayleigh slope (~lambda^-4), visible when clouds are
        thin/absent.
    sodium:
        Strength of the Na absorption trough near 589 nm (yellow-eater).
    deep_albedo:
        Reflectivity of the cloud-free deep atmosphere / dark continuum (small).
    """

    cloud_albedo: float = 0.6
    cloud_fraction: float = 0.9
    methane: float = 0.3
    rayleigh: float = 0.5
    sodium: float = 0.0
    deep_albedo: float = 0.08

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)

        # Rayleigh scattering ~ lambda^-4, normalised at 500 nm; only matters where light
        # penetrates below the clouds, so it is weighted toward the cloud-free fraction.
        rayleigh = self.rayleigh * (500.0 / wl) ** 4

        # Base continuum: a mix of a bright grey cloud deck and a darker deep atmosphere
        # that the Rayleigh slope rides on.
        clear_continuum = self.deep_albedo + 0.15 * rayleigh
        continuum = (
            self.cloud_fraction * self.cloud_albedo
            + (1.0 - self.cloud_fraction) * clear_continuum
        )
        base = np.full_like(wl, 0.0) + continuum

        # Methane absorption: multiplicative Gaussian troughs. Deeper toward the red/IR,
        # which is exactly why methane worlds go blue-green.
        ch4 = np.ones_like(wl)
        for c, s, w in zip(_CH4_BANDS_NM, _CH4_STRENGTHS, _CH4_WIDTHS_NM, strict=True):
            depth = np.clip(self.methane * s, 0.0, 0.98)
            ch4 *= 1.0 - depth * np.exp(-0.5 * ((wl - c) / w) ** 2)

        # Sodium trough near 589 nm.
        na = 1.0 - np.clip(self.sodium, 0.0, 0.98) * np.exp(
            -0.5 * ((wl - _NA_CENTER_NM) / _NA_WIDTH_NM) ** 2
        )

        albedo = base * ch4 * na
        return np.clip(albedo, 0.0, 1.0)


# --- Named presets for the Milestone-1 sanity gate ---------------------------------------

CLOUDY_JUPITER = SyntheticAlbedo(
    cloud_albedo=0.62, cloud_fraction=0.95, methane=0.25, rayleigh=0.4, sodium=0.0,
)
"""Cloudy Jupiter analog -> should render warm off-white / cream."""

METHANE_NEPTUNE = SyntheticAlbedo(
    cloud_albedo=0.55, cloud_fraction=0.7, methane=1.6, rayleigh=0.9, sodium=0.0,
)
"""Deep-methane Neptune-like -> should render blue-green."""

CLOUDFREE_HOT_JUPITER = SyntheticAlbedo(
    cloud_albedo=0.5, cloud_fraction=0.0, methane=0.0, rayleigh=0.6, sodium=0.9,
    deep_albedo=0.05,
)
"""Cloud-free, no methane, sodium eating the yellow -> should render dark."""
