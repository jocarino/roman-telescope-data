"""Model space: the same planet with one physical assumption changed.

`assumed_cloud_state`, `assumed_metallicity` and the planet's orbital distance are inputs the
pipeline is *forced* to pick. Elsewhere on the site they are a disclaimer. Here they become
axes you can move, so a reader can see for themselves how much of a swatch is measurement and
how much is the model's opinion. Three views, one mechanism:

- **migration track** — colour as a function of orbital distance. Methane freezes out, clouds
  condense, the colour walks across the spectrum. This is the site's thesis made draggable.
- **what-if variants** — the same planet with the clouds stripped, the cloud deck closed, or
  the metallicity forced to the ends of its plausible range.
- **colour year** — for an eccentric orbit, the distance track resampled at r(t) over one
  period. Not a separate model: literally the migration track, indexed by time.

THE ANCHORING RULE (why every one of these agrees with the planet's published colour).
Each view is computed as the planet's OWN albedo multiplied by a model RESPONSE RATIO:

    A_view(λ) = A_planet(λ) × [ A_model(λ | changed) / A_model(λ | as published) ]

At the home position the ratio is exactly 1, so the slider starts on the planet's real colour
no matter which engine produced it — parametric, Cahoy grid, or a measured spectrum. The model
contributes only how the colour MOVES, never the identity it moves from. This is the same
idiom `pipeline.spectrum.phase` already uses for its "cahoy-ratio" tier, for the same reason.

WHICH ENGINE DRIVES THE RESPONSE. The parametric model (pipeline.spectrum.parametric), always.
It is the only engine that is continuous and defined over the whole range these features need:
real orbits run from 0.008 AU to 240 AU, and an eccentric planet like HD 80606 b (e = 0.93)
sweeps 0.03 -> 0.89 AU within a single orbit. The Cahoy grid covers 0.8-10 AU only, so a
grid-driven track would flatline against its clamp across most of that motion, and switching
engines mid-track would put a seam in the middle of the slider that reads as a bug.

The grid is not wasted: `cahoy_reference_points` returns what Cahoy et al. 2010 actually says
at its own four distances, for the planets it covers, so the page can mark the reference grid
the Roman Coronagraph community uses right on the slider and let the two be compared.

HONESTY LIMITS, which the UI must carry:
- Equilibrium temperature is scaled as T ∝ r^(-1/2) from the planet's own published T_eq. That
  holds the Bond albedo and the star fixed, which is the standard first-order treatment and
  exactly reproduces the published temperature at the home position.
- Every stop is instantaneous radiative equilibrium. Real atmospheres have thermal inertia and
  lag; cloud decks and chemistry lag much more. The colour year is "where equilibrium points",
  not a forecast of what a telescope would see on a given night.
- Nothing here is a measurement. Moving a planet is a thought experiment about a model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from colour import XYZ_to_Lab, delta_E

from pipeline.colour.cie import ColourResult, reflected_flux_to_colour
from pipeline.config import GRID_NM
from pipeline.spectrum.base import ProviderUnavailable
from pipeline.spectrum.cahoy_grid import CAHOY_DISTANCES_AU, grid_albedo_at
from pipeline.spectrum.parametric import model_for

# --- The distance axis -------------------------------------------------------------------
# The slider is laid out in TEMPERATURE, not in orbital distance, and this matters.
#
# A range fixed in distance (say 1/32 to 32 times the real orbit) makes the feature dead for
# exactly the planets it should be best on: Neptune's own orbit is so cold that five octaves
# inward still only reaches 266 K, so its colour sits still for the whole slider. All the
# interesting chemistry — methane freezing out, water clouds condensing, alkali metals turning
# up — happens between roughly 100 K and 2000 K, and every planet should cross it.
#
# So the endpoints are temperatures, converted to distance per planet via r ∝ T^-2. The home
# position lands wherever the planet's real orbit falls in that range, which is itself worth
# seeing: it shows where this world sits among all the regimes it could have occupied.
_TEQ_LO_K = 40.0  # colder than Neptune: everything condensed, nothing left to change
_TEQ_HI_K = 2600.0  # hotter than KELT-9 b: cloud-free, alkali-soaked, very dark
# Always give the slider at least two octaves of travel either way, so planets already sitting
# at an extreme of that temperature range still have something to drag.
_MIN_RATIO_CEILING = 0.25
_MIN_RATIO_FLOOR = 4.0
N_STOPS = 25


def distance_ratios(eq_temp_k: float) -> tuple[tuple[float, ...], int]:
    """The slider's stops for one planet, as multiples of its real orbital distance, plus the
    index of the home position.

    Log-spaced across the distance range that spans `_TEQ_LO_K`-`_TEQ_HI_K`, with the exact
    home ratio 1.0 inserted so the slider has a stop that reproduces the published colour
    exactly rather than one that merely passes near it.
    """
    temp = max(eq_temp_k, 1.0)
    lo = min((temp / _TEQ_HI_K) ** 2, _MIN_RATIO_CEILING)
    hi = max((temp / _TEQ_LO_K) ** 2, _MIN_RATIO_FLOOR)
    spaced = [
        math.exp(math.log(lo) + (math.log(hi) - math.log(lo)) * i / (N_STOPS - 2))
        for i in range(N_STOPS - 1)
    ]
    home = sum(1 for r in spaced if r < 1.0)
    return tuple(spaced[:home] + [1.0] + spaced[home:]), home

# Samples around one orbit for the colour year, in EQUAL STEPS OF TIME (not of true anomaly).
# That distinction is the whole character of an eccentric orbit: the planet whips through
# periastron and loiters at apoastron, so the colour should sit cool for most of the loop and
# flash hot briefly. Sampling the angle uniformly would show the opposite and be a lie.
COLOUR_YEAR_SAMPLES = 48
# Below this eccentricity the loop is visually a still frame; not worth a control on the page.
COLOUR_YEAR_MIN_ECCENTRICITY = 0.1


@dataclass(frozen=True)
class TrackStop:
    """One position of the migration slider."""

    r_over_a: float  # orbital distance as a multiple of the planet's real one
    au: float | None  # absolute distance, when the real semi-major axis is known
    eq_temp_k: float  # equilibrium temperature there (T ∝ r^-1/2 from the published value)
    hex: str
    luminance_y: float  # true relative brightness, so "dark" survives the trip


@dataclass(frozen=True)
class CahoyPoint:
    """What the Cahoy et al. 2010 grid itself says at one of its four native distances,
    for planets it covers. The reference mark against the modelled track."""

    au: float
    r_over_a: float
    hex: str
    in_track_range: bool  # whether this distance falls within the slider's span


@dataclass(frozen=True)
class MigrationTrack:
    home_index: int
    stops: tuple[TrackStop, ...]
    # Real Cahoy grid colours at 0.8/2/5/10 AU, empty when the planet is outside what the
    # grid covers (rocky worlds, or no grid installed).
    cahoy_points: tuple[CahoyPoint, ...] = ()


@dataclass(frozen=True)
class WhatIfVariant:
    """The planet with exactly one modelling assumption changed."""

    id: str
    label: str  # plain English, self-explanatory without the site's vocabulary
    detail: str  # what was changed and what it means physically
    hex: str
    luminance_y: float
    delta_e2000: float  # perceptual distance from the planet's published colour


@dataclass(frozen=True)
class ColourYear:
    """One orbit of an eccentric planet, sampled at equal steps of time."""

    eccentricity: float
    period_days: float | None
    periastron_au: float | None
    apoastron_au: float | None
    # Index into MigrationTrack.stops (fractional — the client interpolates) for each sample.
    track_positions: tuple[float, ...]
    # Fraction of the orbit spent within one octave of periastron: the "flash" duty cycle.
    hot_fraction: float


# --- Response ratios ---------------------------------------------------------------------


def _safe_ratio(new: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """A_new / A_ref, guarded where the reference goes ~black (deep absorption bands), which
    would otherwise blow a spike through the ratio. Those channels take the spectral-mean
    ratio instead — the same guard `pipeline.spectrum.phase` uses, for the same reason."""
    valid = ref > 0.01
    if not np.any(valid):
        return np.ones_like(ref)
    mean_ratio = float(np.mean(new[valid] / ref[valid]))
    return np.where(valid, new / np.maximum(ref, 1e-9), mean_ratio)


def _param_albedo(
    *,
    eq_temp_k: float,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    metallicity: float | None = None,
    cloud_fraction: float | None = None,
) -> np.ndarray:
    """The parametric model's albedo under a given set of knobs, on GRID_NM."""
    model = model_for(
        equilibrium_temp_k=eq_temp_k,
        radius_r_earth=radius_r_earth,
        mass_m_earth=mass_m_earth,
        metallicity_override=metallicity,
    )
    albedo = model.albedo
    if cloud_fraction is not None:
        albedo = replace(albedo, cloud_fraction=cloud_fraction)
    return albedo.geometric_albedo(GRID_NM)


def eq_temp_at(eq_temp_k: float, r_over_a: float) -> float:
    """Equilibrium temperature at a multiple of the planet's real orbital distance.

    T_eq ∝ r^(-1/2) at fixed Bond albedo and stellar luminosity. Scaling the planet's OWN
    published T_eq (rather than recomputing it from stellar radius and Teff) is deliberate: it
    reproduces the published number exactly at r_over_a = 1, so the slider's home position can
    never disagree with the temperature printed elsewhere on the page.
    """
    return eq_temp_k / math.sqrt(max(r_over_a, 1e-9))


# --- The three views ---------------------------------------------------------------------


def _colour(albedo: np.ndarray, star_flux: np.ndarray) -> ColourResult:
    return reflected_flux_to_colour(
        np.clip(albedo, 0.0, 1.0) * star_flux,
        method="full-spectrum",
        illuminant_flux=star_flux,
        confidence="low",  # a thought experiment about a model, never a measurement
    )


def migration_track(
    *,
    base_albedo: np.ndarray,
    star_flux: np.ndarray,
    eq_temp_k: float,
    semi_major_axis_au: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    metallicity: float | None = None,
) -> MigrationTrack:
    """Colour as the planet is dragged in and out of its orbit.

    `base_albedo` is the planet's published albedo spectrum, whatever engine produced it; the
    parametric model supplies only the response ratio (see the module docstring).
    """
    ref = _param_albedo(
        eq_temp_k=eq_temp_k, radius_r_earth=radius_r_earth, mass_m_earth=mass_m_earth
    )
    base = np.clip(np.asarray(base_albedo, dtype=float), 0.0, 1.0)
    ratios, home_index = distance_ratios(eq_temp_k)

    stops: list[TrackStop] = []
    for ratio in ratios:
        temp = eq_temp_at(eq_temp_k, ratio)
        moved = _param_albedo(
            eq_temp_k=temp, radius_r_earth=radius_r_earth, mass_m_earth=mass_m_earth
        )
        colour = _colour(base * _safe_ratio(moved, ref), star_flux)
        stops.append(
            TrackStop(
                r_over_a=round(ratio, 5),
                au=round(semi_major_axis_au * ratio, 5) if semi_major_axis_au else None,
                eq_temp_k=round(temp, 1),
                hex=colour.hex,
                luminance_y=round(colour.luminance_y, 5),
            )
        )

    return MigrationTrack(
        home_index=home_index,
        stops=tuple(stops),
        cahoy_points=cahoy_reference_points(
            star_flux=star_flux,
            semi_major_axis_au=semi_major_axis_au,
            radius_r_earth=radius_r_earth,
            metallicity=metallicity,
            ratio_range=(ratios[0], ratios[-1]),
        ),
    )


def cahoy_reference_points(
    *,
    star_flux: np.ndarray,
    semi_major_axis_au: float | None,
    radius_r_earth: float | None,
    metallicity: float | None,
    ratio_range: tuple[float, float],
) -> tuple[CahoyPoint, ...]:
    """The Cahoy et al. 2010 grid's own answer at its four native distances, lit by this
    planet's star. Reference marks for the slider, so the modelled track can be read against
    the published grid rather than just asserted.

    Empty for rocky worlds (the grid is Jupiter/Neptune-class only), for planets with no known
    orbit, and whenever the grid is not installed — never a broken build.

    Note the grid is computed for a Sun-like host; its distances are used as published rather
    than rescaled by this star's luminosity, matching how `pipeline.spectrum.cahoy_grid` picks
    a grid point for the planet's own colour. The page says so.
    """
    if semi_major_axis_au is None or metallicity is None:
        return ()
    if radius_r_earth is not None and radius_r_earth < 2.0:
        return ()  # rocky: neither Cahoy class applies

    lo, hi = ratio_range
    points: list[CahoyPoint] = []
    for au in CAHOY_DISTANCES_AU:
        try:
            albedo = grid_albedo_at(GRID_NM, dist_au=au, metallicity=metallicity)
        except ProviderUnavailable:
            return ()
        ratio = au / semi_major_axis_au
        points.append(
            CahoyPoint(
                au=au,
                r_over_a=round(ratio, 5),
                hex=_colour(albedo, star_flux).hex,
                in_track_range=lo <= ratio <= hi,
            )
        )
    return tuple(points)


def what_if_variants(
    *,
    base_albedo: np.ndarray,
    star_flux: np.ndarray,
    base_colour_xyz: tuple[float, float, float],
    eq_temp_k: float,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    metallicity: float | None,
) -> tuple[WhatIfVariant, ...]:
    """The same planet under a handful of alternative modelling assumptions.

    Cloud variants apply to everything (even a rocky world has a cloud fraction). Metallicity
    variants are skipped where `metallicity` is None — rocky worlds have no H/He envelope, so
    the giant mass-metallicity relation is meaningless for them and the pipeline stores None.
    """
    ref = _param_albedo(
        eq_temp_k=eq_temp_k, radius_r_earth=radius_r_earth, mass_m_earth=mass_m_earth
    )
    base = np.clip(np.asarray(base_albedo, dtype=float), 0.0, 1.0)
    base_lab = XYZ_to_Lab(np.array(base_colour_xyz))

    specs: list[tuple[str, str, str, dict]] = [
        (
            "clouds-off",
            "No clouds at all",
            "Strip the cloud deck and you see straight down into the deep atmosphere: much "
            "darker, and bluer where Rayleigh scattering takes over.",
            {"cloud_fraction": 0.0},
        ),
        (
            "clouds-thick",
            "Solid cloud deck",
            "Close the cloud deck completely. Clouds are bright and fairly grey, so this "
            "pushes almost any planet toward a pale version of its star's own colour.",
            {"cloud_fraction": 1.0},
        ),
    ]
    if metallicity is not None:
        specs += [
            (
                "metal-poor",
                "Solar metallicity (1×)",
                "As few heavy elements as the Sun. Less methane to absorb the red end, so "
                "the colour drifts back toward the star's.",
                {"metallicity": 1.0},
            ),
            (
                "metal-rich",
                "Metal-rich (30×)",
                "Thirty times the Sun's heavy elements — Neptune territory. Deeper methane "
                "bands eat the red and the planet swings blue-green.",
                {"metallicity": 30.0},
            ),
        ]

    variants: list[WhatIfVariant] = []
    for vid, label, detail, knobs in specs:
        changed = _param_albedo(
            eq_temp_k=eq_temp_k,
            radius_r_earth=radius_r_earth,
            mass_m_earth=mass_m_earth,
            **knobs,
        )
        colour = _colour(base * _safe_ratio(changed, ref), star_flux)
        variants.append(
            WhatIfVariant(
                id=vid,
                label=label,
                detail=detail,
                hex=colour.hex,
                luminance_y=round(colour.luminance_y, 5),
                delta_e2000=round(
                    float(delta_E(base_lab, XYZ_to_Lab(np.array(colour.xyz)), method="CIE 2000")),
                    1,
                ),
            )
        )
    return tuple(variants)


# --- Colour year -------------------------------------------------------------------------


def _true_anomaly(mean_anomaly: float, e: float) -> float:
    """Solve Kepler's equation M = E - e sin E by Newton's method, then convert the eccentric
    anomaly E to the true anomaly ν. Converges in a handful of iterations for every archive
    eccentricity; the starting guess is the standard one that stays stable near e -> 1."""
    m = mean_anomaly
    ecc = min(max(e, 0.0), 0.999)
    guess = m if ecc < 0.8 else math.pi
    for _ in range(60):
        f = guess - ecc * math.sin(guess) - m
        fp = 1.0 - ecc * math.cos(guess)
        step = f / fp
        guess -= step
        if abs(step) < 1e-12:
            break
    return 2.0 * math.atan2(
        math.sqrt(1.0 + ecc) * math.sin(guess / 2.0),
        math.sqrt(1.0 - ecc) * math.cos(guess / 2.0),
    )


def colour_year(
    *,
    track: MigrationTrack,
    eccentricity: float | None,
    semi_major_axis_au: float | None,
    period_days: float | None = None,
    samples: int = COLOUR_YEAR_SAMPLES,
) -> ColourYear | None:
    """Where on the migration track the planet sits at each moment of one orbit.

    Returns None for orbits too circular to be worth animating. The output is positions on the
    track, not colours: the colours are the track's, which is what guarantees the loop and the
    slider can never disagree.
    """
    if eccentricity is None or eccentricity < COLOUR_YEAR_MIN_ECCENTRICITY:
        return None

    ecc = min(eccentricity, 0.999)
    log_ratios = [math.log(s.r_over_a) for s in track.stops]

    positions: list[float] = []
    near = 0
    for i in range(samples):
        nu = _true_anomaly(2.0 * math.pi * i / samples, ecc)
        r_over_a = (1.0 - ecc**2) / (1.0 + ecc * math.cos(nu))
        # Fractional index into the track. The stops are log-spaced but not perfectly evenly
        # (the exact home ratio is inserted among them), so interpolate on the real values.
        positions.append(
            round(float(np.interp(math.log(r_over_a), log_ratios, range(len(log_ratios)))), 3)
        )
        if r_over_a <= 2.0 * (1.0 - ecc):  # within one octave of periastron
            near += 1

    return ColourYear(
        eccentricity=round(eccentricity, 4),
        period_days=period_days,
        periastron_au=(
            round(semi_major_axis_au * (1.0 - ecc), 5) if semi_major_axis_au else None
        ),
        apoastron_au=(
            round(semi_major_axis_au * (1.0 + ecc), 5) if semi_major_axis_au else None
        ),
        track_positions=tuple(positions),
        hot_fraction=round(near / samples, 3),
    )
