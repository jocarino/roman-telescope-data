"""The Illuminant seam: the host star's spectrum S(lambda), the light that lifts the
planet's albedo into a reflected flux. Blackbody for v1; PHOENIX/Kurucz later behind the
same Protocol.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Illuminant(Protocol):
    def spectrum(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        """Relative spectral flux density S(lambda) (arbitrary normalisation)."""
        ...
