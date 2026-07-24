"""Map real planet parameters -> synthetic-albedo knobs via documented physical heuristics.

This is NOT radiative transfer. It is a transparent, honest rule set that places a planet
into a cloud/chemistry regime from its parameters, then hands the resulting albedo to the
same pipeline. It is the v1 stand-in for a real grid (Cahoy 2010) or model (PICASO), both of
which slot in behind SpectrumProvider unchanged.

The knobs vary *continuously* with temperature, surface gravity, and metallicity (rather than
snapping to a handful of fixed buckets), so two planets that differ in mass/size/orbit get
different colours instead of collapsing onto an identical archetype. Everything here is still
an assumption (we hold no per-planet atmosphere data) — but a better-justified, continuous one.

Regime behaviour (still the CLAUDE.md domain background, now as smooth blends):
  - cold ice giants / jovians  -> thick clouds + methane      -> blue-green / cream
  - temperate / warm           -> water/ammonia cloud + haze  -> bright, pale, muted
  - hot                        -> cloud-free, alkali (Na)      -> dark, sodium-blue
  - ultra-hot                  -> cloud-free, very dark
  - small rocky                -> grey, moderate-low albedo

Metallicity follows the observed mass–metallicity relation (Thorngren et al. 2016: smaller
planets are more metal-rich), and feeds the methane/haze knobs, so it actually affects colour
instead of being a cosmetic label.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pipeline.spectrum.synthetic import SyntheticAlbedo

_M_EARTH_PER_M_JUP = 317.8


@dataclass(frozen=True)
class AlbedoModel:
    albedo: SyntheticAlbedo
    cloud_state: str
    assumed_metallicity: float
    phase_angle_deg: float


def _sigmoid(x: float, x0: float, w: float) -> float:
    """Smooth 0->1 ramp centred at x0 with width w. Replaces the old hard temperature cuts."""
    return 1.0 / (1.0 + math.exp(-(x - x0) / w))


def _metallicity(mass_m_earth: float | None, radius_r_earth: float | None) -> float:
    """Atmospheric metallicity (× solar) from the mass–metallicity relation. Smaller planets
    are more metal-rich; continuous, so it varies planet to planet. Clamped to a sane range.
    Falls back to a radius proxy when mass is unknown (small radius -> Neptune-like, metal-rich)."""
    if mass_m_earth and mass_m_earth > 0:
        m_jup = mass_m_earth / _M_EARTH_PER_M_JUP
        return max(1.0, min(60.0, 9.7 * m_jup**-0.45))
    if radius_r_earth and radius_r_earth > 0:
        return max(1.0, min(60.0, 9.7 * (radius_r_earth / 11.2) ** -0.9))
    return 3.0


def model_for(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None = None,
) -> AlbedoModel:
    t = equilibrium_temp_k if equilibrium_temp_k is not None else 300.0
    radius = radius_r_earth if radius_r_earth is not None else 8.0
    z_rel = _metallicity(mass_m_earth, radius_r_earth)

    if radius < 1.6:
        # Rocky: grey, but albedo + Rayleigh drift a little with temperature so terrestrial
        # worlds aren't all one colour.
        cool = _sigmoid(-t, -350, 180)  # 1 for cooler rocky worlds
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.25, cloud_fraction=0.20 + 0.15 * cool, methane=0.0,
                rayleigh=0.12 + 0.14 * cool, sodium=0.0, deep_albedo=0.10 + 0.05 * cool,
            ),
            cloud_state="rocky / thin atmosphere (grey)",
            assumed_metallicity=round(z_rel, 1),
            phase_angle_deg=0.0,
        )

    # Continuous giant / sub-Neptune model. Smooth temperature blends:
    hot = _sigmoid(t, 900, 130)     # cloud-free, sodium-bearing hot regime
    ultra = _sigmoid(t, 1600, 160)  # extra-dark ultra-hot
    warm = _sigmoid(t, 500, 120)    # methane starts dissociating above this
    ice_giant = 2.0 <= radius < 6.0

    # Surface gravity in Earth g's; high gravity compresses the atmosphere -> thinner clouds.
    gravity = (mass_m_earth / radius**2) if (mass_m_earth and radius) else 1.5
    grav_hi = _sigmoid(math.log10(max(gravity, 0.1)), 0.5, 0.4)

    z_factor = min(1.8, (z_rel / 9.7) ** 0.35)  # metallicity's pull on methane / haze depth

    cloud_fraction = 0.9 * (1.0 - hot) * (1.0 - 0.25 * grav_hi)
    cloud_albedo = 0.62 * (1.0 - hot) + 0.22 * hot
    methane = (1.4 if ice_giant else 0.5) * (1.0 - warm) * z_factor
    sodium = 0.9 * hot
    rayleigh = 0.35 + 0.35 * (1.0 - cloud_fraction) + 0.15 * (z_factor - 0.7)
    deep_albedo = 0.09 * (1.0 - hot) + 0.04 * hot - 0.02 * ultra

    if ultra > 0.5:
        label = "ultra-hot, cloud-free, very dark"
    elif hot > 0.5:
        label = "hot, cloud-free, alkali (sodium) absorption"
    elif t < 220:
        label = "cold, thick clouds + methane" + (" (ice giant)" if ice_giant else "")
    else:
        label = "temperate / warm, partial cloud + haze"

    return AlbedoModel(
        albedo=SyntheticAlbedo(
            cloud_albedo=cloud_albedo, cloud_fraction=max(0.0, cloud_fraction),
            methane=max(0.0, methane), rayleigh=max(0.1, rayleigh), sodium=sodium,
            deep_albedo=max(0.02, deep_albedo),
        ),
        cloud_state=label,
        assumed_metallicity=round(z_rel, 1),
        phase_angle_deg=0.0,
    )
