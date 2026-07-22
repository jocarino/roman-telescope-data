"""Pure-logic tests for the M2 batch layer (no network)."""

from __future__ import annotations

import math

from pipeline.fetch.archive import ArchiveRecord
from pipeline.spectrum.parametric import model_for


def _rec(**kw) -> ArchiveRecord:
    base = dict(
        pl_name="Test b", hostname="Test", pl_eqt=None, pl_rade=None, pl_bmasse=None,
        pl_orbsmax=None, pl_orbeccen=None, st_teff=None, st_rad=None, st_spectype=None,
        disc_method=None, disc_year=None, disc_facility=None,
    )
    base.update(kw)
    return ArchiveRecord(**base)


def test_eqt_uses_archive_value_when_present():
    assert _rec(pl_eqt=1209.0).equilibrium_temp_k() == 1209.0


def test_eqt_fallback_from_stellar_params():
    # Sun-like star, planet at 1 AU: T_eq ~ 255 K for Bond albedo 0.3.
    rec = _rec(st_teff=5772.0, st_rad=1.0, pl_orbsmax=1.0)
    t = rec.equilibrium_temp_k(bond_albedo=0.3)
    assert t is not None
    assert 240 < t < 290, t


def test_eqt_none_when_insufficient():
    assert _rec(st_teff=5000.0).equilibrium_temp_k() is None


def test_regime_hot_is_cloudfree_sodium():
    m = model_for(equilibrium_temp_k=1200.0, radius_r_earth=12.0)
    assert m.albedo.cloud_fraction < 0.2
    assert m.albedo.sodium > 0.5
    assert "cloud-free" in m.cloud_state


def test_regime_cold_ice_giant_is_methane_rich():
    m = model_for(equilibrium_temp_k=60.0, radius_r_earth=3.5)
    assert m.albedo.methane > 1.0
    assert m.albedo.cloud_fraction > 0.8


def test_regime_rocky_is_grey():
    m = model_for(equilibrium_temp_k=250.0, radius_r_earth=1.0)
    assert m.albedo.methane == 0.0
    assert "rocky" in m.cloud_state


def test_eqt_fallback_matches_formula():
    rec = _rec(st_teff=6000.0, st_rad=1.2, pl_orbsmax=2.0)
    r_star_au = 1.2 * 0.00465047
    expected = 6000.0 * math.sqrt(r_star_au / (2 * 2.0)) * (1 - 0.3) ** 0.25
    assert math.isclose(rec.equilibrium_temp_k(), expected, rel_tol=1e-9)
