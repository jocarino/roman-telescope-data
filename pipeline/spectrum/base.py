"""The SpectrumProvider seam.

A provider turns planet parameters into a geometric-albedo curve A(lambda). The rest of
the pipeline never cares *how* — synthetic (v1), Cahoy 2010 grid interpolation, or PICASO
all satisfy this one Protocol and are interchangeable.

Providers evaluate albedo at ARBITRARY wavelengths (not a fixed grid) so band integration
can reach into the near-IR (e.g. Roman's 835 nm band extends past the 780 nm CIE cutoff).
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class SpectrumProvider(Protocol):
    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        """Geometric albedo A(lambda) in [0, ~1] evaluated at the given wavelengths (nm)."""
        ...
