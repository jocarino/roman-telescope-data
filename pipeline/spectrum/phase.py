"""Per-phase albedo: how a planet's reflected spectrum changes with orbital phase angle
(0° = fully lit "full moon", 90° = half lit, 180° = backlit and dark).

Three tiers, honest about their provenance (recorded in the emitted `source` field):

- "cahoy-grid": the provider itself is phase-resolved (CahoyProvider) — real modelled
  phase spectra, colour change and dimming both from Cahoy et al. 2010.
- "cahoy-ratio": parametric/PICASO giants borrow the RATIO A(λ,α)/A(λ,0°) from the
  nearest Cahoy grid point (same nearest rule the router uses). The planet keeps its own
  0° colour identity; Cahoy contributes only how that colour bends and dims with phase.
- "lambert-grey": rocky worlds (no Cahoy analog) and any planet when the grid is absent:
  a Lambert sphere — brightness dims with phase, colour stays constant. The simplest
  honest assumption, clearly labelled.
"""

from __future__ import annotations

import math

import numpy as np

from pipeline.spectrum.base import ProviderUnavailable, SpectrumProvider
from pipeline.spectrum.cahoy_grid import make_cahoy

# The emitted phase sampling — matches the Cahoy grid's native 10° steps.
PHASE_ANGLES_DEG: tuple[int, ...] = tuple(range(0, 181, 10))


def lambert_phase(alpha_deg: float) -> float:
    """Lambert-sphere phase function Φ(α) = (sin α + (π − α) cos α) / π. 1 at full phase,
    0 at 180°. Grey: scales brightness, leaves colour untouched."""
    a = math.radians(min(max(alpha_deg, 0.0), 180.0))
    return (math.sin(a) + (math.pi - a) * math.cos(a)) / math.pi


class PhasedAlbedo:
    """Callable giving A(λ, α) for one planet, plus the provenance of its phase behaviour."""

    def __init__(self, provider: SpectrumProvider, *, semi_major_axis_au: float | None,
                 metallicity: float | None):
        self._provider = provider
        self.source = "lambert-grey"
        self._ref = None  # CahoyProvider used for the ratio tier
        if hasattr(provider, "albedo_at_phase"):
            self.source = "cahoy-grid"
        elif metallicity is not None:  # a giant/sub-Neptune: borrow Cahoy's phase behaviour
            try:
                self._ref = make_cahoy(
                    semi_major_axis_au=semi_major_axis_au, metallicity=metallicity
                )
                self.source = "cahoy-ratio"
            except ProviderUnavailable:
                pass  # grid not installed: fall through to lambert-grey

    def at(self, phase_deg: float) -> SpectrumProvider:
        """A SpectrumProvider view of this planet frozen at one phase angle — lets the
        band integrator (or anything provider-shaped) consume a phased spectrum."""

        class _AtPhase:
            def __init__(inner, parent: PhasedAlbedo, deg: float):
                inner._parent, inner._deg = parent, deg

            def geometric_albedo(inner, wavelengths_nm: np.ndarray) -> np.ndarray:
                return inner._parent(wavelengths_nm, inner._deg)

        return _AtPhase(self, phase_deg)

    def __call__(self, wavelengths_nm: np.ndarray, phase_deg: float) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        if self.source == "cahoy-grid":
            return self._provider.albedo_at_phase(wl, phase_deg)  # type: ignore[attr-defined]

        base = self._provider.geometric_albedo(wl)
        if self.source == "cahoy-ratio":
            ref0 = self._ref.albedo_at_phase(wl, 0.0)  # type: ignore[union-attr]
            ref_a = self._ref.albedo_at_phase(wl, phase_deg)  # type: ignore[union-attr]
            # Ratio is ill-defined where the reference goes ~black (deep absorption bands);
            # fill those channels with the spectral-mean ratio so no spikes leak through.
            valid = ref0 > 0.01
            if np.any(valid):
                mean_ratio = float(np.mean(ref_a[valid] / ref0[valid]))
                ratio = np.where(valid, ref_a / np.maximum(ref0, 1e-9), mean_ratio)
                return np.clip(base * ratio, 0.0, 1.0)
            # Degenerate reference (never happens with the real grid): grey fallback.
        return np.clip(base * lambert_phase(phase_deg), 0.0, 1.0)
