"""Blackbody illuminant from stellar effective temperature (Planck's law).

v1 approximation of the host star's spectrum. Only the *shape* matters (it multiplies the
albedo before the CIE step and everything is normalised downstream), so absolute constants
are irrelevant — we use spectral radiance in SI and let normalisation handle scale.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Physical constants (SI)
_H = 6.62607015e-34  # Planck constant, J s
_C = 2.99792458e8  # speed of light, m/s
_KB = 1.380649e-23  # Boltzmann constant, J/K


@dataclass(frozen=True)
class BlackbodyStar:
    teff_k: float

    def spectrum(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl_m = np.asarray(wavelengths_nm, dtype=float) * 1e-9
        # Planck spectral radiance per unit wavelength, B_lambda(T).
        exponent = _H * _C / (wl_m * _KB * self.teff_k)
        # exp can overflow for very short wl / cool stars; np.expm1 keeps it stable.
        radiance = (2.0 * _H * _C**2) / (wl_m**5 * np.expm1(exponent))
        return radiance


# The Sun (~5772 K) as the default illuminant for Sun-like comparisons.
SUN = BlackbodyStar(teff_k=5772.0)
