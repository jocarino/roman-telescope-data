"""Map real planet parameters -> synthetic-albedo knobs via documented physical heuristics.

This is NOT radiative transfer. It is a transparent, honest rule set that places a planet
into a cloud/chemistry regime from its equilibrium temperature and size, then hands the
resulting albedo model to the same pipeline. It is the v1 stand-in for a real grid
(Cahoy 2010) or model (PICASO), both of which slot in behind SpectrumProvider unchanged.

Regimes (by equilibrium temperature), grounded in the domain background in CLAUDE.md:
  - cold ice giants / jovians  -> thick clouds + methane      -> blue-green / cream
  - temperate                  -> water/ammonia clouds        -> bright, pale
  - warm                       -> partial cloud / haze        -> muted
  - hot                        -> cloud-free, alkali (Na)      -> dark, sodium-blue
  - ultra-hot                  -> cloud-free, very dark
  - small rocky                -> grey, moderate-low albedo
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.spectrum.synthetic import SyntheticAlbedo


@dataclass(frozen=True)
class AlbedoModel:
    albedo: SyntheticAlbedo
    cloud_state: str
    assumed_metallicity: float
    phase_angle_deg: float


def model_for(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
) -> AlbedoModel:
    t = equilibrium_temp_k if equilibrium_temp_k is not None else 300.0
    radius = radius_r_earth if radius_r_earth is not None else 8.0
    is_ice_giant = 2.0 <= radius < 6.0
    is_rocky = radius < 2.0

    if is_rocky:
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.25, cloud_fraction=0.3, methane=0.0, rayleigh=0.2,
                sodium=0.0, deep_albedo=0.12,
            ),
            cloud_state="rocky / thin atmosphere (grey)",
            assumed_metallicity=1.0,
            phase_angle_deg=0.0,
        )

    if t < 150:
        methane = 1.5 if is_ice_giant else 0.4
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.62, cloud_fraction=0.92, methane=methane, rayleigh=0.6,
                sodium=0.0, deep_albedo=0.08,
            ),
            cloud_state="cold, thick clouds"
            + (" + deep methane (ice giant)" if is_ice_giant else " (ammonia)"),
            assumed_metallicity=10.0 if is_ice_giant else 1.0,
            phase_angle_deg=0.0,
        )

    if t < 350:
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.60, cloud_fraction=0.85, methane=0.4, rayleigh=0.55,
                sodium=0.0, deep_albedo=0.08,
            ),
            cloud_state="temperate, water/ammonia clouds",
            assumed_metallicity=3.0,
            phase_angle_deg=0.0,
        )

    if t < 800:
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.45, cloud_fraction=0.5, methane=0.1, rayleigh=0.5,
                sodium=0.2, deep_albedo=0.07,
            ),
            cloud_state="warm, partial cloud / haze",
            assumed_metallicity=1.0,
            phase_angle_deg=0.0,
        )

    if t < 1500:
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.30, cloud_fraction=0.1, methane=0.0, rayleigh=0.6,
                sodium=0.85, deep_albedo=0.05,
            ),
            cloud_state="hot, cloud-free, alkali (sodium) absorption",
            assumed_metallicity=1.0,
            phase_angle_deg=0.0,
        )

    return AlbedoModel(
        albedo=SyntheticAlbedo(
            cloud_albedo=0.22, cloud_fraction=0.05, methane=0.0, rayleigh=0.4,
            sodium=0.9, deep_albedo=0.04,
        ),
        cloud_state="ultra-hot, cloud-free, very dark",
        assumed_metallicity=1.0,
        phase_angle_deg=0.0,
    )
