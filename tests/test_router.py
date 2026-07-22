"""Spectrum-engine router: correct provider preference, and graceful fallback to the
always-available parametric provider when Cahoy/PICASO data is not installed.
"""

from __future__ import annotations

import numpy as np

from pipeline.config import GRID_NM
from pipeline.spectrum import router
from pipeline.spectrum.base import ProviderUnavailable


class _FakeProvider:
    def geometric_albedo(self, wavelengths_nm):
        return np.full_like(np.asarray(wavelengths_nm, dtype=float), 0.4)


def _choose(**kw):
    base = dict(
        equilibrium_temp_k=300.0, radius_r_earth=10.0, mass_m_earth=300.0,
        semi_major_axis_au=2.0, teff_k=5772.0,
    )
    base.update(kw)
    return router.choose_model(**base)


def test_fallback_to_parametric_when_nothing_installed():
    # No Cahoy grid dir, no PICASO -> everything falls back, but still produces a spectrum.
    chosen = _choose(equilibrium_temp_k=1200.0)  # hot giant would prefer PICASO
    assert chosen.source == "parametric"
    alb = chosen.provider.geometric_albedo(GRID_NM)
    assert alb.shape == GRID_NM.shape
    assert np.all((alb >= 0) & (alb <= 1))


def test_rocky_uses_parametric_only(monkeypatch):
    # Even if Cahoy/PICASO were available, a rocky planet should not use them.
    monkeypatch.setattr(router, "make_cahoy", lambda **kw: _FakeProvider())
    monkeypatch.setattr(router, "make_picaso", lambda **kw: _FakeProvider())
    chosen = _choose(radius_r_earth=1.0, equilibrium_temp_k=250.0)
    assert chosen.source == "parametric"


def test_cool_giant_prefers_cahoy(monkeypatch):
    monkeypatch.setattr(router, "make_cahoy", lambda **kw: _FakeProvider())
    monkeypatch.setattr(router, "make_picaso", lambda **kw: _FakeProvider())
    chosen = _choose(equilibrium_temp_k=120.0, radius_r_earth=11.0)
    assert chosen.source == "cahoy"


def test_cool_giant_falls_to_picaso_when_no_cahoy(monkeypatch):
    def no_cahoy(**kw):
        raise ProviderUnavailable("no grid")

    monkeypatch.setattr(router, "make_cahoy", no_cahoy)
    monkeypatch.setattr(router, "make_picaso", lambda **kw: _FakeProvider())
    chosen = _choose(equilibrium_temp_k=120.0, radius_r_earth=11.0)
    assert chosen.source == "picaso"


def test_hot_giant_prefers_picaso(monkeypatch):
    monkeypatch.setattr(router, "make_cahoy", lambda **kw: _FakeProvider())
    monkeypatch.setattr(router, "make_picaso", lambda **kw: _FakeProvider())
    chosen = _choose(equilibrium_temp_k=1400.0, radius_r_earth=13.0)
    assert chosen.source == "picaso"  # Cahoy is not offered to hot giants


def test_metadata_always_present():
    chosen = _choose()
    assert chosen.cloud_state and chosen.metallicity > 0 and chosen.source
