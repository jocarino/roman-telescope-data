"""Cahoy grid provider, exercised against the real committed grid in data/cahoy_grid/.

If the grid is ever removed these are skipped (the provider raises ProviderUnavailable),
so the suite still passes with no grid — matching the router's fallback contract.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.config import GRID_NM
from pipeline.spectrum.base import ProviderUnavailable
from pipeline.spectrum.cahoy_grid import make_cahoy
from pipeline.spectrum.router import choose_model


def _cahoy_or_skip(**kw):
    try:
        return make_cahoy(**kw)
    except ProviderUnavailable:
        pytest.skip("Cahoy grid not installed")


def test_cahoy_jupiter_has_methane_absorption():
    p = _cahoy_or_skip(semi_major_axis_au=2.0, metallicity=1.0)
    alb = p.geometric_albedo(np.array([500.0, 890.0]))
    assert np.all((alb >= 0) & (alb <= 1))
    assert alb[1] < alb[0], "near-IR methane band should be darker than the visible"


def test_cahoy_albedo_on_full_grid_is_bounded():
    p = _cahoy_or_skip(semi_major_axis_au=5.0, metallicity=1.0)
    alb = p.geometric_albedo(GRID_NM)
    assert alb.shape == GRID_NM.shape
    assert np.all((alb >= 0) & (alb <= 1))


def test_router_selects_cahoy_for_cool_giant_when_grid_present():
    try:
        make_cahoy(semi_major_axis_au=2.0, metallicity=1.0)
    except ProviderUnavailable:
        pytest.skip("Cahoy grid not installed")
    chosen = choose_model(
        equilibrium_temp_k=220.0, radius_r_earth=13.0, mass_m_earth=800.0,
        semi_major_axis_au=2.1, teff_k=5800.0,
    )
    assert chosen.source == "cahoy"
