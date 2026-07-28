"""Model space: the migration track, the what-if knobs, and the colour year.

The load-bearing property, asserted first and for every engine, is the ANCHORING RULE: the
slider's home stop must reproduce the planet's published colour EXACTLY. If that ever drifts,
the page shows one colour in the swatch and a different one under a slider parked at its
default, which reads as a bug and undermines the honesty the whole site is built on.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline.colour.cie import reflected_flux_to_colour
from pipeline.config import GRID_NM
from pipeline.illuminant.blackbody import SUN, BlackbodyStar
from pipeline.modelspace import (
    COLOUR_YEAR_MIN_ECCENTRICITY,
    N_STOPS,
    colour_year,
    distance_ratios,
    eq_temp_at,
    migration_track,
    what_if_variants,
)
from pipeline.spectrum.synthetic import CLOUDY_JUPITER, METHANE_NEPTUNE

SUN_FLUX = SUN.spectrum(GRID_NM)


def _albedo(model) -> np.ndarray:
    return model.geometric_albedo(GRID_NM)


def _published(albedo: np.ndarray, star_flux: np.ndarray):
    """What the pipeline would emit for this albedo — the colour the page prints."""
    return reflected_flux_to_colour(
        albedo * star_flux, method="full-spectrum", illuminant_flux=star_flux, confidence="high"
    )


# --- The anchoring rule -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model", "eq_temp_k", "radius", "mass"),
    [
        (CLOUDY_JUPITER, 110.0, 11.2, 318.0),  # a cold jovian (Cahoy-class)
        (METHANE_NEPTUNE, 47.0, 3.9, 17.1),  # a cold ice giant
        (CLOUDY_JUPITER, 1209.0, 12.7, 363.0),  # a hot Jupiter
        (METHANE_NEPTUNE, 255.0, 1.0, 1.0),  # a rocky world (metallicity is None)
    ],
)
def test_home_stop_reproduces_the_published_colour_exactly(model, eq_temp_k, radius, mass):
    albedo = _albedo(model)
    track = migration_track(
        base_albedo=albedo,
        star_flux=SUN_FLUX,
        eq_temp_k=eq_temp_k,
        semi_major_axis_au=1.0,
        radius_r_earth=radius,
        mass_m_earth=mass,
    )
    home = track.stops[track.home_index]
    assert home.r_over_a == 1.0
    assert home.hex == _published(albedo, SUN_FLUX).hex
    assert home.eq_temp_k == pytest.approx(eq_temp_k, abs=0.05)


def test_anchoring_holds_for_a_measured_spectrum_the_model_never_produced():
    """Solar-system anchors carry a real measured albedo. The track must still start on it —
    that is the whole point of driving the slider with a ratio rather than an absolute model."""
    measured = np.clip(0.55 + 0.25 * np.sin(GRID_NM / 40.0), 0.0, 1.0)
    track = migration_track(
        base_albedo=measured,
        star_flux=SUN_FLUX,
        eq_temp_k=110.0,
        semi_major_axis_au=5.2,
        radius_r_earth=11.2,
        mass_m_earth=318.0,
    )
    assert track.stops[track.home_index].hex == _published(measured, SUN_FLUX).hex


# --- The distance axis --------------------------------------------------------------------


@pytest.mark.parametrize("eq_temp_k", [47.0, 110.0, 255.0, 405.0, 1209.0, 2400.0])
def test_axis_always_crosses_the_interesting_temperature_range(eq_temp_k: float):
    """Every planet's slider must reach both regimes, or the feature is dead for whole classes
    of planet (this is exactly what a fixed distance range got wrong for the ice giants)."""
    ratios, home = distance_ratios(eq_temp_k)
    assert len(ratios) == N_STOPS
    assert ratios[home] == 1.0
    assert list(ratios) == sorted(ratios)
    hottest = eq_temp_at(eq_temp_k, ratios[0])
    coldest = eq_temp_at(eq_temp_k, ratios[-1])
    assert hottest >= min(eq_temp_k, 2600.0) - 1.0
    assert coldest <= max(eq_temp_k, 40.0) + 1.0


def test_eq_temp_scales_as_inverse_square_root_of_distance():
    assert eq_temp_at(400.0, 1.0) == pytest.approx(400.0)
    assert eq_temp_at(400.0, 4.0) == pytest.approx(200.0)
    assert eq_temp_at(400.0, 0.25) == pytest.approx(800.0)


def test_track_gets_colder_outward_and_brightens_as_clouds_survive():
    """A cold jovian dragged inward should heat up and, per the parametric model's cloud and
    alkali behaviour, go darker. The CLAUDE.md milestone-1 expectation, on the distance axis."""
    track = migration_track(
        base_albedo=_albedo(CLOUDY_JUPITER),
        star_flux=SUN_FLUX,
        eq_temp_k=110.0,
        semi_major_axis_au=5.2,
        radius_r_earth=11.2,
        mass_m_earth=318.0,
    )
    temps = [s.eq_temp_k for s in track.stops]
    assert temps == sorted(temps, reverse=True)  # inward stops are first, and hottest
    assert track.stops[0].luminance_y < track.stops[-1].luminance_y


# --- What-if knobs ------------------------------------------------------------------------


def test_stripping_clouds_darkens_and_closing_them_brightens():
    albedo = _albedo(CLOUDY_JUPITER)
    base = _published(albedo, SUN_FLUX)
    variants = {
        v.id: v
        for v in what_if_variants(
            base_albedo=albedo,
            star_flux=SUN_FLUX,
            base_colour_xyz=base.xyz,
            eq_temp_k=110.0,
            radius_r_earth=11.2,
            mass_m_earth=318.0,
            metallicity=3.0,
        )
    }
    assert variants["clouds-off"].luminance_y < base.luminance_y
    assert variants["clouds-thick"].luminance_y > variants["clouds-off"].luminance_y
    # Stripping the clouds off a cloudy world is a big perceptual move; saying so is the point.
    assert variants["clouds-off"].delta_e2000 > 1.0


def test_rocky_worlds_get_no_metallicity_knobs():
    """A rocky world has no H/He envelope, so the giant mass-metallicity relation is
    meaningless for it — the pipeline stores None and the panel must not invent a value."""
    albedo = _albedo(CLOUDY_JUPITER)
    ids = {
        v.id
        for v in what_if_variants(
            base_albedo=albedo,
            star_flux=SUN_FLUX,
            base_colour_xyz=_published(albedo, SUN_FLUX).xyz,
            eq_temp_k=255.0,
            radius_r_earth=1.0,
            mass_m_earth=1.0,
            metallicity=None,
        )
    }
    assert ids == {"clouds-off", "clouds-thick"}


def test_metallicity_knob_moves_an_ice_giant_toward_blue_green():
    """Deeper methane bands eat the red end. Asserted as a real channel shift, not a vibe."""
    albedo = _albedo(METHANE_NEPTUNE)
    variants = {
        v.id: v
        for v in what_if_variants(
            base_albedo=albedo,
            star_flux=SUN_FLUX,
            base_colour_xyz=_published(albedo, SUN_FLUX).xyz,
            eq_temp_k=47.0,
            radius_r_earth=3.9,
            mass_m_earth=17.1,
            metallicity=30.0,
        )
    }
    poor = int(variants["metal-poor"].hex[1:3], 16) - int(variants["metal-poor"].hex[5:7], 16)
    rich = int(variants["metal-rich"].hex[1:3], 16) - int(variants["metal-rich"].hex[5:7], 16)
    assert rich < poor  # metal-rich is relatively less red / more blue


# --- Colour year --------------------------------------------------------------------------


def _track_for_year(eq_temp_k: float = 405.0):
    return migration_track(
        base_albedo=_albedo(CLOUDY_JUPITER),
        star_flux=BlackbodyStar(5645.0).spectrum(GRID_NM),
        eq_temp_k=eq_temp_k,
        semi_major_axis_au=0.46,
        radius_r_earth=11.6,
        mass_m_earth=1266.0,
    )


def test_circular_orbits_get_no_colour_year():
    assert colour_year(track=_track_for_year(), eccentricity=0.0, semi_major_axis_au=0.46) is None
    assert (
        colour_year(
            track=_track_for_year(),
            eccentricity=COLOUR_YEAR_MIN_ECCENTRICITY - 0.01,
            semi_major_axis_au=0.46,
        )
        is None
    )


def test_hd_80606b_like_orbit_spends_most_of_its_year_cold():
    """e = 0.93. Sampling in equal steps of TIME (via Kepler) rather than of true anomaly is
    what makes the loop honest: the planet loiters at apoastron and whips through periastron,
    so the colour should sit cool and flash hot briefly, not spend half the loop scorched."""
    track = _track_for_year()
    year = colour_year(track=track, eccentricity=0.93183, semi_major_axis_au=0.4603)
    assert year is not None
    assert year.periastron_au == pytest.approx(0.4603 * (1 - 0.93183), rel=1e-3)
    assert year.apoastron_au == pytest.approx(0.4603 * (1 + 0.93183), rel=1e-3)
    assert year.hot_fraction < 0.15  # a brief flash, not half the orbit

    # The extremes must land on the track's hot and cold sides of home.
    positions = year.track_positions
    assert min(positions) < track.home_index < max(positions)


def test_kepler_sampling_starts_at_periastron_and_reaches_apoastron():
    track = _track_for_year()
    year = colour_year(track=track, eccentricity=0.6, semi_major_axis_au=1.0, samples=64)
    assert year is not None
    positions = list(year.track_positions)
    # Mean anomaly 0 is periastron: the closest-in sample, i.e. the smallest track index.
    assert positions[0] == min(positions)
    # Half a period later the planet is at apoastron: the furthest-out sample.
    assert positions[len(positions) // 2] == max(positions)
    # And the loop is symmetric about that, since the orbit is traversed both ways.
    assert positions[1] == pytest.approx(positions[-1], abs=0.05)


def test_colour_year_positions_index_the_track_and_nothing_else():
    """The loop must be the migration track resampled, never a second model — otherwise the
    slider and the animation could disagree about the same planet at the same distance."""
    track = _track_for_year()
    year = colour_year(track=track, eccentricity=0.5, semi_major_axis_au=1.0)
    assert year is not None
    for pos in year.track_positions:
        assert 0.0 <= pos <= len(track.stops) - 1


def test_true_anomaly_solves_keplers_equation():
    from pipeline.modelspace import _true_anomaly

    for ecc in (0.0, 0.3, 0.6, 0.93, 0.99):
        for mean in (0.0, 0.7, math.pi / 2, math.pi, 5.0):
            nu = _true_anomaly(mean, ecc)
            # Recover the eccentric anomaly from nu and check M = E - e sin E holds.
            ecc_anom = 2.0 * math.atan2(
                math.sqrt(1.0 - ecc) * math.sin(nu / 2.0),
                math.sqrt(1.0 + ecc) * math.cos(nu / 2.0),
            )
            recovered = ecc_anom - ecc * math.sin(ecc_anom)
            # Compare as angles: the residual wraps, so 2π and 0 are the same answer.
            residual = (recovered - mean + math.pi) % (2 * math.pi) - math.pi
            assert residual == pytest.approx(0.0, abs=1e-6)
