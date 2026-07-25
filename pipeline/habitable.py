"""Habitable-zone lens: where a planet's orbit sits relative to the liquid-water zone.

This is ORBITAL GEOGRAPHY, not a habitability claim. Everything here follows from three
measured numbers — the host star's effective temperature, the host star's radius (which
with Teff gives its luminosity), and the planet's orbital distance. No atmosphere is
modelled, none is known, and nothing about the planet's surface is assumed.

The zone edges are the Kopparapu et al. (2014) climate-model limits, expressed as the
stellar flux S (in Earth units) a planet receives:

    S = (L / L_sun) / (a / AU)^2          L / L_sun = (R / R_sun)^2 (Teff / 5772 K)^4

Four boundaries, each a quartic in T* = Teff - 5780 K:

    Recent Venus  ── optimistic inner edge: Venus had no surface water by this point.
    Runaway Greenhouse ── conservative inner edge: oceans evaporate.
    Maximum Greenhouse ── conservative outer edge: CO2 clouds stop warming the surface.
    Early Mars    ── optimistic outer edge: Mars looks to have had surface water here.

Between the two conservative edges is the "conservative" zone; the strips out to the
optimistic edges are the "optimistic" zone. Both are standard in the literature, which is
why we report the zone rather than a bare yes/no.

Honest limits of this calculation, surfaced in `caveats` for the UI to display:
  - Being in the zone means the planet receives the right AMOUNT of starlight. Whether it
    holds liquid water depends on an atmosphere we have not measured for any of these
    planets.
  - The limits assume an Earth-like H2O/CO2/N2 atmosphere on a rocky planet. A gas giant
    in the zone has no surface to hold an ocean (a large moon of one might).
  - Eccentric orbits swing across the zone; we classify by the semi-major axis.
  - The climate models are calibrated for 2600-7200 K hosts. Outside that we clamp the
    polynomial and flag the result as extrapolated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Kopparapu et al. 2014 (ApJ 787, L29), Table 1 — coefficients for a 1 M_earth planet.
# S_eff = S_eff_sun + a T* + b T*^2 + c T*^3 + d T*^4,  T* = Teff - 5780 K.
_LIMITS: dict[str, tuple[float, float, float, float, float]] = {
    "recent_venus": (1.7763, 1.4335e-4, 3.3954e-9, -7.6364e-12, -1.1950e-15),
    "runaway_greenhouse": (1.0385, 1.2456e-4, 1.4612e-8, -7.6345e-12, -1.7511e-15),
    "maximum_greenhouse": (0.3507, 5.9578e-5, 1.6707e-9, -3.0058e-12, -5.1925e-16),
    "early_mars": (0.3207, 5.4471e-5, 1.5275e-9, -2.1709e-12, -3.8282e-16),
}

# Range over which the Kopparapu climate models were computed. Outside it we clamp the
# polynomial to the nearest edge (it diverges fast beyond) and mark the result extrapolated.
TEFF_MIN_K = 2600.0
TEFF_MAX_K = 7200.0
_TEFF_REF_K = 5780.0  # the polynomial's reference temperature, not the Sun's exact Teff
_TEFF_SUN_K = 5772.0  # IAU nominal solar Teff, for the luminosity ratio

# Radius cuts for "is there a surface for an ocean to sit on". The radius valley near
# 1.6-2.0 R_earth divides planets that kept a thick H/He envelope from those that did not;
# above ~2.4 R_earth a planet is essentially never a bare rock.
_ROCKY_MAX_R_EARTH = 1.6
_MAYBE_ROCKY_MAX_R_EARTH = 2.4
_ROCKY_MAX_M_EARTH = 2.0  # mass fallback when no radius is known
_MAYBE_ROCKY_MAX_M_EARTH = 10.0

# Eccentricity above which the "the orbit crosses the zone" caveat is worth showing.
_ECCENTRIC_ORBIT = 0.2

ZONE_LABELS = {
    "too-hot": "Too hot",
    "optimistic": "Optimistic zone",
    "conservative": "Habitable zone",
    "too-cold": "Too cold",
    "unknown": "Not computable",
}
# Gallery filter order: the interesting ones first.
ZONE_ORDER = ["conservative", "optimistic", "too-hot", "too-cold", "unknown"]


@dataclass(frozen=True)
class HabitableZone:
    """The star's zone edges, in both flux and distance."""

    recent_venus_au: float
    runaway_greenhouse_au: float
    maximum_greenhouse_au: float
    early_mars_au: float
    extrapolated: bool


def luminosity_lsun(teff_k: float | None, radius_r_sun: float | None) -> float | None:
    """Stellar luminosity from the Stefan-Boltzmann law: L/Lsun = (R/Rsun)^2 (T/Tsun)^4."""
    if teff_k is None or radius_r_sun is None or teff_k <= 0 or radius_r_sun <= 0:
        return None
    return (radius_r_sun**2) * (teff_k / _TEFF_SUN_K) ** 4


def insolation_earth(luminosity: float | None, semi_major_axis_au: float | None) -> float | None:
    """Starlight received relative to Earth's: S = (L/Lsun) / (a/AU)^2."""
    if luminosity is None or semi_major_axis_au is None or semi_major_axis_au <= 0:
        return None
    return luminosity / (semi_major_axis_au**2)


def _s_eff(limit: str, teff_k: float) -> float:
    s_sun, a, b, c, d = _LIMITS[limit]
    t = min(max(teff_k, TEFF_MIN_K), TEFF_MAX_K) - _TEFF_REF_K
    return s_sun + a * t + b * t**2 + c * t**3 + d * t**4


def habitable_zone(teff_k: float | None, luminosity: float | None) -> HabitableZone | None:
    """The four zone edges as orbital distances in AU. None if the star is uncharacterised."""
    if teff_k is None or luminosity is None or luminosity <= 0:
        return None

    def edge_au(limit: str) -> float:
        return math.sqrt(luminosity / _s_eff(limit, teff_k))

    return HabitableZone(
        recent_venus_au=edge_au("recent_venus"),
        runaway_greenhouse_au=edge_au("runaway_greenhouse"),
        maximum_greenhouse_au=edge_au("maximum_greenhouse"),
        early_mars_au=edge_au("early_mars"),
        extrapolated=not (TEFF_MIN_K <= teff_k <= TEFF_MAX_K),
    )


def zone_for(teff_k: float | None, insolation: float | None) -> str:
    """Which zone an insolation falls in: conservative / optimistic / too-hot / too-cold."""
    if teff_k is None or insolation is None or insolation <= 0:
        return "unknown"
    if insolation > _s_eff("recent_venus", teff_k):
        return "too-hot"
    if insolation >= _s_eff("runaway_greenhouse", teff_k):
        return "optimistic"
    if insolation >= _s_eff("maximum_greenhouse", teff_k):
        return "conservative"
    if insolation >= _s_eff("early_mars", teff_k):
        return "optimistic"
    return "too-cold"


def surface_class(radius_r_earth: float | None, mass_m_earth: float | None) -> str:
    """Could this planet have a solid surface for an ocean to sit on?

    "rocky"     — small enough that a bare rocky surface is the expected outcome.
    "uncertain" — in the radius valley; may be rock, may hold a thick envelope.
    "enveloped" — a Neptune or a giant: no surface, whatever the temperature.
    "unknown"   — neither radius nor mass measured.
    """
    if radius_r_earth is not None:
        if radius_r_earth < _ROCKY_MAX_R_EARTH:
            return "rocky"
        if radius_r_earth < _MAYBE_ROCKY_MAX_R_EARTH:
            return "uncertain"
        return "enveloped"
    if mass_m_earth is not None:
        if mass_m_earth < _ROCKY_MAX_M_EARTH:
            return "rocky"
        if mass_m_earth < _MAYBE_ROCKY_MAX_M_EARTH:
            return "uncertain"
        return "enveloped"
    return "unknown"


def _caveats(
    zone: str,
    surface: str,
    hz: HabitableZone | None,
    eccentricity: float | None,
    axis_source: str | None,
) -> list[str]:
    """Plain-English limits on this specific verdict, strongest first."""
    out: list[str] = []
    in_zone = zone in ("conservative", "optimistic")
    if in_zone:
        out.append(
            "In the zone means it receives about as much starlight as Earth does — not that "
            "it has water. No atmosphere has been measured for this planet."
        )
    if in_zone and surface == "enveloped":
        out.append(
            "Too large to have a solid surface: this is a Neptune or a gas giant, so there is "
            "nowhere for an ocean to sit. A large moon of it could still be a candidate."
        )
    elif in_zone and surface == "uncertain":
        out.append(
            "Its size sits in the gap where planets may be bare rock or may hold a thick "
            "hydrogen envelope — we cannot tell which from the radius alone."
        )
    elif in_zone and surface == "unknown":
        out.append("Neither radius nor mass is measured, so we cannot say if it has a surface.")
    if zone == "optimistic":
        out.append(
            "Optimistic edge: this relies on the evidence that Venus and Mars held surface "
            "water early on, which stretches the zone wider than climate models alone allow."
        )
    if eccentricity is not None and eccentricity >= _ECCENTRIC_ORBIT:
        out.append(
            f"An eccentric orbit (e = {eccentricity:.2f}) carries it in and out across the "
            "zone over a year; we classify by its average distance."
        )
    if hz is not None and hz.extrapolated:
        out.append(
            "The host star is hotter or cooler than the climate models cover (2,600-7,200 K), "
            "so the zone edges are extrapolated."
        )
    if axis_source is not None and axis_source != "measured":
        out.append("The orbital distance is not a direct measurement, so the zone is indicative.")
    return out


@dataclass(frozen=True)
class HabitabilityResult:
    """Everything the badge, the filter and the planet page need."""

    zone: str
    surface: str
    insolation_earth: float | None
    luminosity_lsun: float | None
    inner_au: float | None  # conservative inner edge (runaway greenhouse)
    outer_au: float | None  # conservative outer edge (maximum greenhouse)
    optimistic_inner_au: float | None  # recent Venus
    optimistic_outer_au: float | None  # early Mars
    extrapolated: bool
    caveats: list[str]

    @property
    def is_candidate(self) -> bool:
        """The badge-worthy case: in the zone AND plausibly has a surface."""
        return self.zone in ("conservative", "optimistic") and self.surface in (
            "rocky",
            "uncertain",
        )


def assess(
    *,
    teff_k: float | None,
    star_radius_r_sun: float | None,
    semi_major_axis_au: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    eccentricity: float | None = None,
    axis_source: str | None = None,
) -> HabitabilityResult:
    """The whole lens for one planet, from measured inputs only."""
    lum = luminosity_lsun(teff_k, star_radius_r_sun)
    insol = insolation_earth(lum, semi_major_axis_au)
    hz = habitable_zone(teff_k, lum)
    zone = zone_for(teff_k, insol)
    surface = surface_class(radius_r_earth, mass_m_earth)
    return HabitabilityResult(
        zone=zone,
        surface=surface,
        insolation_earth=insol,
        luminosity_lsun=lum,
        inner_au=hz.runaway_greenhouse_au if hz else None,
        outer_au=hz.maximum_greenhouse_au if hz else None,
        optimistic_inner_au=hz.recent_venus_au if hz else None,
        optimistic_outer_au=hz.early_mars_au if hz else None,
        extrapolated=hz.extrapolated if hz else False,
        caveats=_caveats(zone, surface, hz, eccentricity, axis_source),
    )
