"""Spectrum-engine router: choose the best available albedo provider per planet.

Preference by planet type, each falling through to the next if its data/library is missing:

  rocky (< 2 R⊕)            -> parametric only (neither grid does terrestrial surfaces well)
  cool giant (Teq < 500 K)  -> Cahoy grid -> PICASO -> parametric
  hot / other giant         -> PICASO -> parametric
  everything else           -> parametric

The parametric provider is always available, so there is always an answer. The chosen engine
is recorded (`source`) so the UI can state honestly which engine produced each colour — a
run with no Cahoy/PICASO data simply reports "parametric" everywhere, never silently.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.spectrum.base import ProviderUnavailable, SpectrumProvider
from pipeline.spectrum.cahoy_grid import make_cahoy
from pipeline.spectrum.parametric import model_for
from pipeline.spectrum.picaso_model import make_picaso


@dataclass(frozen=True)
class ChosenModel:
    provider: SpectrumProvider
    cloud_state: str
    metallicity: float
    phase_angle_deg: float
    source: str  # "parametric" | "cahoy" | "picaso"


def _preferred(radius_r_earth: float, eq_temp_k: float) -> list[tuple[str, object]]:
    is_rocky = radius_r_earth < 2.0
    if is_rocky:
        return []
    if eq_temp_k < 500.0:
        return [("cahoy", make_cahoy), ("picaso", make_picaso)]
    return [("picaso", make_picaso)]


def choose_model(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    semi_major_axis_au: float | None,
    teff_k: float,
) -> ChosenModel:
    # The parametric model is always computed: it supplies the cloud-state / metallicity /
    # phase metadata AND is the final fallback provider.
    base = model_for(equilibrium_temp_k=equilibrium_temp_k, radius_r_earth=radius_r_earth)

    temp = equilibrium_temp_k if equilibrium_temp_k is not None else 300.0
    radius = radius_r_earth if radius_r_earth is not None else 8.0

    for label, factory in _preferred(radius, temp):
        try:
            provider = factory(
                equilibrium_temp_k=equilibrium_temp_k,
                radius_r_earth=radius_r_earth,
                mass_m_earth=mass_m_earth,
                semi_major_axis_au=semi_major_axis_au,
                teff_k=teff_k,
                metallicity=base.assumed_metallicity,
            )
            return ChosenModel(
                provider=provider,
                cloud_state=base.cloud_state,
                metallicity=base.assumed_metallicity,
                phase_angle_deg=base.phase_angle_deg,
                source=label,
            )
        except ProviderUnavailable:
            continue

    return ChosenModel(
        provider=base.albedo,
        cloud_state=base.cloud_state,
        metallicity=base.assumed_metallicity,
        phase_angle_deg=base.phase_angle_deg,
        source="parametric",
    )
