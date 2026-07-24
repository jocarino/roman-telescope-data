"""Phase-resolved albedo: the three tiers (cahoy-grid / cahoy-ratio / lambert-grey) and
the physical sanity of the emitted phase colours (identity at 0°, dark at 180°, dimming
monotone-ish in between)."""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.config import GRID_NM
from pipeline.spectrum.base import ProviderUnavailable
from pipeline.spectrum.cahoy_grid import make_cahoy
from pipeline.spectrum.phase import PHASE_ANGLES_DEG, PhasedAlbedo, lambert_phase
from pipeline.spectrum.synthetic import CLOUDY_JUPITER, METHANE_NEPTUNE


def _cahoy_or_skip(**kw):
    try:
        return make_cahoy(**kw)
    except ProviderUnavailable:
        pytest.skip("Cahoy grid not installed")


def test_lambert_phase_endpoints():
    assert lambert_phase(0.0) == pytest.approx(1.0)
    assert lambert_phase(180.0) == pytest.approx(0.0, abs=1e-12)
    assert 0.3 < lambert_phase(90.0) < 0.35  # Lambert quadrature is 1/pi ≈ 0.318


def test_cahoy_native_phases_dim_toward_new():
    p = _cahoy_or_skip(semi_major_axis_au=2.0, metallicity=1.0)
    means = [p.albedo_at_phase(GRID_NM, d).mean() for d in (0, 60, 120, 180)]
    assert means[0] > means[1] > means[2] > means[3]
    assert means[3] == pytest.approx(0.0, abs=1e-4)


def test_cahoy_phase_interpolates_between_grid_steps():
    p = _cahoy_or_skip(semi_major_axis_au=2.0, metallicity=1.0)
    lo, mid, hi = (p.albedo_at_phase(GRID_NM, d).mean() for d in (40.0, 45.0, 50.0))
    assert lo >= mid >= hi
    assert mid == pytest.approx((lo + hi) / 2.0, rel=0.05)


def test_parametric_giant_borrows_cahoy_ratio():
    phased = PhasedAlbedo(METHANE_NEPTUNE, semi_major_axis_au=2.0, metallicity=30.0)
    if phased.source == "lambert-grey":
        pytest.skip("Cahoy grid not installed")
    assert phased.source == "cahoy-ratio"
    a0 = phased(GRID_NM, 0.0)
    assert np.allclose(a0, METHANE_NEPTUNE.geometric_albedo(GRID_NM))  # 0° keeps identity
    a90 = phased(GRID_NM, 90.0)
    assert a90.mean() < 0.65 * a0.mean()  # strong dimming by quadrature
    assert phased(GRID_NM, 180.0).mean() == pytest.approx(0.0, abs=1e-3)


def test_rocky_world_gets_grey_lambert():
    phased = PhasedAlbedo(CLOUDY_JUPITER, semi_major_axis_au=1.0, metallicity=None)
    assert phased.source == "lambert-grey"
    a0 = phased(GRID_NM, 0.0)
    a60 = phased(GRID_NM, 60.0)
    # Grey: same spectral shape, uniformly scaled by the Lambert factor.
    assert np.allclose(a60, a0 * lambert_phase(60.0))


def test_phase_angles_cover_full_to_new():
    assert PHASE_ANGLES_DEG[0] == 0
    assert PHASE_ANGLES_DEG[-1] == 180
    assert len(PHASE_ANGLES_DEG) == 19
