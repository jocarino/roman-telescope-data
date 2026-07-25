"""The habitable-zone lens, checked against planets whose answer is already known.

The solar system is the ground truth: Earth and Mars are inside the conservative zone by
the Kopparapu limits, Venus is not, and the giants are far outside it. The exoplanet cases
are the ones the literature quotes, so a coefficient typo or a units slip shows up here
rather than as a wrong badge on the site.
"""

from __future__ import annotations

import math

import pytest

from pipeline.habitable import (
    assess,
    habitable_zone,
    insolation_earth,
    luminosity_lsun,
    surface_class,
    zone_for,
)

SUN_TEFF = 5772.0


def _sun_assess(a_au: float, r_earth: float | None, m_earth: float | None = None):
    return assess(
        teff_k=SUN_TEFF,
        star_radius_r_sun=1.0,
        semi_major_axis_au=a_au,
        radius_r_earth=r_earth,
        mass_m_earth=m_earth,
    )


def test_sun_luminosity_is_one() -> None:
    assert luminosity_lsun(SUN_TEFF, 1.0) == pytest.approx(1.0, rel=1e-6)


def test_insolation_is_inverse_square() -> None:
    assert insolation_earth(1.0, 1.0) == pytest.approx(1.0)
    assert insolation_earth(1.0, 2.0) == pytest.approx(0.25)
    assert insolation_earth(4.0, 2.0) == pytest.approx(1.0)


def test_solar_habitable_zone_matches_kopparapu() -> None:
    """Kopparapu et al. 2014 put the Sun's conservative zone at ~0.99-1.70 AU."""
    hz = habitable_zone(SUN_TEFF, 1.0)
    assert hz is not None
    assert hz.runaway_greenhouse_au == pytest.approx(0.99, abs=0.03)
    assert hz.maximum_greenhouse_au == pytest.approx(1.70, abs=0.03)
    # The optimistic zone strictly contains the conservative one.
    assert hz.recent_venus_au < hz.runaway_greenhouse_au
    assert hz.early_mars_au > hz.maximum_greenhouse_au
    assert not hz.extrapolated


@pytest.mark.parametrize(
    ("name", "a_au", "r_earth", "zone"),
    [
        ("Venus", 0.7233, 0.949, "too-hot"),
        ("Earth", 1.0, 1.0, "conservative"),
        ("Mars", 1.5237, 0.532, "conservative"),
        ("Jupiter", 5.204, 11.209, "too-cold"),
        ("Neptune", 30.178, 3.883, "too-cold"),
    ],
)
def test_solar_system_zones(name: str, a_au: float, r_earth: float, zone: str) -> None:
    assert _sun_assess(a_au, r_earth).zone == zone, name


def test_earth_is_the_reference_candidate() -> None:
    earth = _sun_assess(1.0, 1.0)
    assert earth.insolation_earth == pytest.approx(1.0, rel=1e-6)
    assert earth.surface == "rocky"
    assert earth.is_candidate


def test_giants_in_the_zone_are_not_candidates() -> None:
    """A Jupiter parked at 1 AU gets Earth's starlight and still has no surface."""
    hot_jupiter_at_1au = _sun_assess(1.0, 11.2)
    assert hot_jupiter_at_1au.zone == "conservative"
    assert hot_jupiter_at_1au.surface == "enveloped"
    assert not hot_jupiter_at_1au.is_candidate
    assert any("no solid surface" in c or "nowhere for an ocean" in c
               for c in hot_jupiter_at_1au.caveats)


@pytest.mark.parametrize(
    ("name", "teff", "r_sun", "a_au", "r_earth", "insol"),
    [
        # Literature insolations: TRAPPIST-1 e ~0.65 S_earth, Kepler-186 f ~0.29.
        ("TRAPPIST-1 e", 2566.0, 0.1192, 0.02925, 0.920, 0.65),
        ("Kepler-186 f", 3788.0, 0.523, 0.432, 1.17, 0.29),
    ],
)
def test_known_habitable_zone_planets(
    name: str, teff: float, r_sun: float, a_au: float, r_earth: float, insol: float
) -> None:
    h = assess(
        teff_k=teff,
        star_radius_r_sun=r_sun,
        semi_major_axis_au=a_au,
        radius_r_earth=r_earth,
        mass_m_earth=None,
    )
    assert h.insolation_earth == pytest.approx(insol, abs=0.06), name
    assert h.zone == "conservative", name
    assert h.is_candidate, name


def test_hot_jupiter_is_far_too_hot() -> None:
    """HD 209458 b: ~0.047 AU around a Sun-like star, hundreds of times Earth's starlight."""
    h = assess(
        teff_k=6071.0,
        star_radius_r_sun=1.203,
        semi_major_axis_au=0.04747,
        radius_r_earth=15.2,
        mass_m_earth=219.0,
    )
    assert h.zone == "too-hot"
    assert h.insolation_earth > 500
    assert not h.is_candidate


def test_cool_host_flags_extrapolation() -> None:
    """Below 2,600 K the climate models stop; we still answer, but say the edges are stretched."""
    h = assess(
        teff_k=2400.0,
        star_radius_r_sun=0.12,
        semi_major_axis_au=0.03,
        radius_r_earth=1.0,
        mass_m_earth=None,
    )
    assert h.extrapolated
    assert any("extrapolated" in c for c in h.caveats)


def test_missing_inputs_degrade_to_unknown() -> None:
    """No stellar radius (and so no luminosity) means no zone — never a guess."""
    h = assess(
        teff_k=5772.0,
        star_radius_r_sun=None,
        semi_major_axis_au=1.0,
        radius_r_earth=1.0,
        mass_m_earth=None,
    )
    assert h.zone == "unknown"
    assert h.insolation_earth is None
    assert h.inner_au is None
    assert not h.is_candidate


def test_zone_boundaries_are_ordered_for_every_host_temperature() -> None:
    """Across the whole stellar range the four edges must stay in order, or the bands in the
    diagram would render inside out."""
    for teff in range(2000, 9001, 100):
        hz = habitable_zone(float(teff), 1.0)
        assert hz is not None
        assert hz.recent_venus_au < hz.runaway_greenhouse_au
        assert hz.runaway_greenhouse_au < hz.maximum_greenhouse_au
        assert hz.maximum_greenhouse_au < hz.early_mars_au
        assert all(
            math.isfinite(v)
            for v in (hz.recent_venus_au, hz.maximum_greenhouse_au, hz.early_mars_au)
        )


def test_zone_classification_agrees_with_the_edges() -> None:
    """Sweeping the orbit outward must produce the zones in order, with no gaps."""
    seen = [zone_for(SUN_TEFF, insolation_earth(1.0, a / 100.0)) for a in range(10, 400)]
    assert seen[0] == "too-hot"
    assert seen[-1] == "too-cold"
    # The sequence may only ever move forward through the zones.
    order = ["too-hot", "optimistic", "conservative", "optimistic", "too-cold"]
    idx = 0
    for z in seen:
        if z != order[idx]:
            idx += 1
            assert idx < len(order) and z == order[idx], f"unexpected transition to {z}"
    assert idx == len(order) - 1


@pytest.mark.parametrize(
    ("r_earth", "m_earth", "expected"),
    [
        (0.9, None, "rocky"),
        (1.55, None, "rocky"),
        (1.8, None, "uncertain"),
        (3.0, None, "enveloped"),
        (None, 1.0, "rocky"),
        (None, 5.0, "uncertain"),
        (None, 300.0, "enveloped"),
        (None, None, "unknown"),
    ],
)
def test_surface_class(r_earth: float | None, m_earth: float | None, expected: str) -> None:
    assert surface_class(r_earth, m_earth) == expected


def test_every_in_zone_verdict_carries_a_caveat() -> None:
    """The honesty guarantee the UI leans on: a planet is never shown as in-zone without at
    least the "starlight is not water" caveat travelling with it."""
    for a_au in (0.8, 1.0, 1.5, 1.75):
        for r in (0.9, 2.0, 11.0):
            h = _sun_assess(a_au, r)
            if h.zone in ("conservative", "optimistic"):
                assert h.caveats, f"{a_au} AU, {r} R_earth"
