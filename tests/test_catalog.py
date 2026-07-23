"""Pure-logic tests for the M2 batch layer (no network)."""

from __future__ import annotations

import math

from pipeline.catalog import _display_name, _model_temperature, completeness_gate
from pipeline.fetch.archive import ArchiveRecord
from pipeline.spectrum.parametric import model_for


def test_display_name_expands_abbreviations():
    assert _display_name("51 Peg b") == "51 Pegasi b"
    assert _display_name("47 UMa b") == "47 Ursae Majoris b"
    assert _display_name("ups And d") == "upsilon Andromedae d"
    assert _display_name("Proxima Cen b") == "Proxima Centauri b"
    assert _display_name("bet Pic b") == "beta Pictoris b"


def test_display_name_leaves_catalog_designations_untouched():
    for n in ["HD 189733 b", "WASP-12 b", "GJ 1214 b", "Kepler-186 f", "TRAPPIST-1 e"]:
        assert _display_name(n) == n


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


def test_hot_jupiter_keeps_archive_temp_for_model():
    # Irradiated hot Jupiter: archive eqt ~ irradiation temp -> NOT reclassified.
    rec = _rec(pl_eqt=1200.0, st_teff=5052.0, st_rad=0.76, pl_orbsmax=0.031)
    assert _model_temperature(rec, rec.equilibrium_temp_k()) == 1200.0


def test_young_imaged_giant_reclassified_to_irradiation_temp():
    # Archive pl_eqt=1200 K (internal heat), but at 68 AU irradiation temp is ~cold.
    rec = _rec(pl_eqt=1200.0, st_teff=7400.0, st_rad=1.4, pl_orbsmax=68.0)
    mt = _model_temperature(rec, rec.equilibrium_temp_k())
    assert mt is not None and mt < 100, f"expected cold irradiation temp, got {mt}"


def test_gate_passes_with_radius_and_temp():
    ok, reason = completeness_gate(_rec(pl_rade=1.0, pl_eqt=300.0))
    assert ok and reason is None


def test_gate_passes_with_mass_only_and_temp():
    # 51 Eri b shape: no radius, but a mass (giant) + measured temp -> keep, radius assumed.
    ok, _ = completeness_gate(_rec(pl_bmasse=3464.0, pl_eqt=807.0))
    assert ok


def test_gate_passes_with_computable_temp():
    ok, _ = completeness_gate(_rec(pl_rade=2.0, st_teff=5772.0, st_rad=1.0, pl_orbsmax=1.0))
    assert ok


def test_gate_excludes_no_size():
    ok, reason = completeness_gate(_rec(pl_eqt=300.0))
    assert not ok and "size" in reason


def test_gate_excludes_no_temperature():
    ok, reason = completeness_gate(_rec(pl_rade=1.0))  # no eqt, nothing to compute from
    assert not ok and "temperature" in reason
