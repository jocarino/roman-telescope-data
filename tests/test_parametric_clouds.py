"""The parametric engine's cloud rule: a hot planet must be ABLE to be cloudy.

The defect this file pins closed: `cloud_fraction` used to be a strict inverse function of
equilibrium temperature, so above ~1,400 K it was forced below 0.02 and a cloudy hot giant was
unrepresentable at any parameter choice. That is not a tuning slip — it puts a real, measured
class of planet outside the model's reach, and it made us call Kepler-7 b "very dark" when it is
the textbook bright one.

The physical basis and every citation live in `pipeline/spectrum/parametric.py`
(`_silicate_deck`). What is asserted here is only what a measurement can settle:

  Kepler-7 b   T_eq 1,630 K   Ag = 0.32 +/- 0.03   Demory et al. 2011, arXiv:1105.5143
  TrES-2 b     T_eq 1,466 K   Ag = 0.0253 +/- 0.0072   Kipping & Spiegel 2011, arXiv:1108.2297
  HD 189733 b  T_eq 1,209 K   Ag < 0.12 (450-570 nm), "deep blue"   Evans et al. 2013,
                                                                    arXiv:1307.3239

Albedos here are compared as a mean over 430-780 nm, which is this project's visible-grid proxy
for the Kepler bandpass (Kepler runs to ~900 nm; our grid stops at 780). It is a proxy, so the
bounds below are deliberately loose — they are testing "is the physics reachable and roughly
right", not reproducing a photometric measurement.
"""

from __future__ import annotations

import numpy as np

from pipeline.colour.cie import reflected_flux_to_colour
from pipeline.config import GRID_NM
from pipeline.illuminant.blackbody import BlackbodyStar
from pipeline.spectrum.parametric import model_for

_KEPLER_PROXY = (GRID_NM >= 430.0) & (GRID_NM <= 780.0)

# T_eq (K), radius (R_earth), mass (M_earth), host T_eff (K) — Archive values, as built.
KEPLER_7B = dict(equilibrium_temp_k=1630.0, radius_r_earth=18.180998, mass_m_earth=140.16303)
TRES_2B = dict(equilibrium_temp_k=1466.0, radius_r_earth=15.24424, mass_m_earth=473.5667)
HD_189733B = dict(equilibrium_temp_k=1209.0, radius_r_earth=12.66617, mass_m_earth=359.1479)


def _mean_albedo(**params) -> float:
    """Mean modelled geometric albedo over the Kepler-bandpass proxy."""
    albedo = model_for(**params).albedo.geometric_albedo(GRID_NM)
    return float(albedo[_KEPLER_PROXY].mean())


def _colour(teff_k: float, **params):
    star = BlackbodyStar(teff_k).spectrum(GRID_NM)
    flux = model_for(**params).albedo.geometric_albedo(GRID_NM) * star
    return reflected_flux_to_colour(flux, method="full-spectrum", illuminant_flux=star)


# --- The defect itself --------------------------------------------------------------------


def test_a_cloudy_hot_giant_is_representable():
    """THE regression. There must exist a hot (>1,400 K) giant the model calls substantially
    cloudy. Under the old rule no parameter choice could produce one."""
    cloudiest = max(
        model_for(equilibrium_temp_k=t, radius_r_earth=15.0, mass_m_earth=200.0)
        .albedo.cloud_fraction
        for t in range(1400, 2200, 10)
    )
    assert cloudiest > 0.3, (
        f"no hot giant can be cloudy: best cloud_fraction above 1,400 K is {cloudiest:.3f}. "
        "Cloud coverage has collapsed back onto a monotonic function of temperature."
    )


def test_cloudiness_is_not_monotonic_in_temperature():
    """The whole physical claim, stated as a shape: somewhere above the temperature where the
    cool deck is gone, cloudiness must RISE again with temperature (Parmentier et al. 2016's
    silicate window) before falling away. A monotonic rule cannot pass this."""
    fractions = [
        model_for(equilibrium_temp_k=t, radius_r_earth=15.0, mass_m_earth=200.0)
        .albedo.cloud_fraction
        for t in range(1200, 2200, 20)
    ]
    rises = [b - a for a, b in zip(fractions, fractions[1:], strict=False) if b > a]
    assert rises, "cloud fraction never increases with temperature — the window is gone"
    assert max(rises) > 0.01, "the rise is too small to be the silicate window"
    # and it must come back down again: this is a window, not a new floor
    assert fractions[-1] < 0.05, (
        f"still cloudy at 2,180 K ({fractions[-1]:.3f}); the window must close by ~1,900 K"
    )


# --- Checks against planets with published measurements -----------------------------------


def test_kepler_7b_is_bright_like_its_measurement():
    """Ag = 0.32 +/- 0.03 (Demory et al. 2011). The old model gave 0.084 on this proxy and
    labelled it 'ultra-hot, cloud-free, very dark'."""
    a = _mean_albedo(**KEPLER_7B)
    assert 0.25 < a < 0.40, f"expected ~0.32 for Kepler-7 b, got {a:.3f}"
    assert "silicate" in model_for(**KEPLER_7B).cloud_state


def test_tres_2b_stays_dark():
    """Ag = 0.0253 +/- 0.0072 (Kipping & Spiegel 2011) — the darkest known planet, and only
    ~160 K cooler than Kepler-7 b. It must NOT be swept into the silicate window.

    The bound is 0.15, not 0.03: this model floors out near 0.09 for any cloud-free giant and
    so cannot reach a true 0.025. That is a known, documented limitation of the analytic
    albedo's dark end (see parametric.py), unchanged by the cloud work. What is pinned here is
    that TrES-2 b stays far darker than Kepler-7 b."""
    dark = _mean_albedo(**TRES_2B)
    assert dark < 0.15, f"TrES-2 b must stay dark, got {dark:.3f}"
    assert dark < 0.5 * _mean_albedo(**KEPLER_7B), (
        "TrES-2 b must stay much darker than Kepler-7 b — 13x apart in the measurements"
    )
    assert "silicate" not in model_for(**TRES_2B).cloud_state


def test_hd_189733b_stays_dark_and_blue():
    """Ag < 0.12 across 450-570 nm and "would appear a deep blue color" (Evans et al. 2013)."""
    assert _mean_albedo(**HD_189733B) < 0.15
    c = _colour(5052.0, **HD_189733B)
    r, _g, b = c.srgb
    assert b > r, f"HD 189733 b must stay blue, got {c.srgb} {c.hex}"
    assert c.luminance_y < 0.15, f"HD 189733 b must stay dark, got lumY={c.luminance_y:.3f}"


def test_ultra_hot_jupiters_stay_dark():
    """Above ~1,900 K the window has closed (Parmentier 2016 put the reflected-to-thermal
    transition there). WASP-12 b and HAT-P-7 b must not brighten."""
    for name, t in (("WASP-12 b", 2601.0), ("HAT-P-7 b", 2733.0)):
        a = _mean_albedo(equilibrium_temp_k=t, radius_r_earth=20.0, mass_m_earth=446.0)
        assert a < 0.12, f"{name} should stay dark, got {a:.3f}"


# --- The change must not leak into the rest of the catalogue ------------------------------


def test_cool_and_temperate_planets_are_untouched_by_the_window():
    """The silicate deck must be exactly zero below ~1,450 K, so no cool or temperate planet
    moves because of it. This is what keeps the blast radius to the hot band."""
    from pipeline.spectrum.parametric import _silicate_deck

    for t in (50.0, 110.0, 300.0, 500.0, 900.0, 1200.0, 1400.0):
        assert _silicate_deck(t, 0.0) < 1e-3, f"silicate deck leaked down to {t} K"


def test_a_cold_jupiter_is_still_bright_and_a_neptune_still_methane_blue():
    """Guard rails on the regimes this change was not supposed to touch."""
    jup = model_for(equilibrium_temp_k=110.0, radius_r_earth=11.2, mass_m_earth=317.8)
    assert jup.albedo.cloud_fraction > 0.6 and "methane" in jup.cloud_state
    nep = model_for(equilibrium_temp_k=47.0, radius_r_earth=3.88, mass_m_earth=17.1)
    assert nep.albedo.methane > 1.0


def test_gravity_separates_two_planets_at_the_same_temperature():
    """Sedimentation (Ackerman & Marley 2001) is the only thing giving the model any spread at
    fixed temperature, so it must actually do something."""
    low_g = model_for(equilibrium_temp_k=1700.0, radius_r_earth=18.0, mass_m_earth=130.0)
    high_g = model_for(equilibrium_temp_k=1700.0, radius_r_earth=11.0, mass_m_earth=1200.0)
    assert low_g.albedo.cloud_fraction > high_g.albedo.cloud_fraction + 0.1


def test_the_silicate_label_has_plain_english_prose():
    """Every cloud state the engine can emit needs a plain-English explanation, or the planet
    page falls back to a generic line (dual-audience rule in CLAUDE.md)."""
    from pipeline.tours import colour_reason

    label = model_for(**KEPLER_7B).cloud_state

    class _Params:
        assumed_cloud_state = label
        equilibrium_temp_k = 1630.0

    class _Star:
        teff_k = 5933.0

    class _Rec:
        params = _Params()
        host_star = _Star()

    prose = colour_reason(_Rec(), brief=True)
    assert "rock" in prose or "silicate" in prose, prose
    assert "modelled atmosphere shapes" not in prose, "fell through to the generic clause"


def test_grid_assumption_holds():
    """The Kepler proxy above assumes the standard visible grid."""
    assert np.isclose(GRID_NM[0], 380.0) and np.isclose(GRID_NM[-1], 780.0)
