"""PICASO provider + anchor verification.

Runs against the COMMITTED PICASO spectra in data/picaso_spectra/ (so no 7 GB opacity DB or
isolated venv is needed at test time) and the committed planets.json. Tests skip cleanly if a
spectrum isn't cached, preserving the fallback contract.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pytest

from pipeline.config import GRID_NM
from pipeline.models import PlanetsFile
from pipeline.spectrum.base import ProviderUnavailable
from pipeline.spectrum.picaso_model import make_picaso

_PLANETS = PlanetsFile.model_validate_json(pathlib.Path("data/planets.json").read_text())
_BY_ID = {p.id: p for p in _PLANETS.planets}


def _make_from_record(rec):
    return make_picaso(
        equilibrium_temp_k=rec.params.equilibrium_temp_k,
        radius_r_earth=rec.params.radius_r_earth,
        mass_m_earth=rec.params.mass_m_earth,
        teff_k=rec.host_star.teff_k,
        metallicity=rec.params.assumed_metallicity,
    )


# --- ANCHOR 2 (external truth): HD 189733 b's reflected light is BLUE (Hubble measured it) ---
def test_hd189733b_picaso_spectrum_is_blue():
    rec = _BY_ID["hd-189733-b"]
    try:
        p = _make_from_record(rec)
    except ProviderUnavailable:
        pytest.skip("HD 189733 b PICASO spectrum not cached")
    alb = p.geometric_albedo(np.array([450.0, 700.0]))
    assert alb[0] > alb[1], f"blue expected: A(450)={alb[0]:.3f} A(700)={alb[1]:.3f}"


def test_hd189733b_true_colour_is_blue():
    rec = _BY_ID["hd-189733-b"]
    if rec.params.spectrum_source != "picaso":
        pytest.skip("HD 189733 b not built with PICASO")
    r, g, b = rec.true_colour.srgb
    assert b > r, f"HD 189733 b should be blue (B>R), got {rec.true_colour.srgb}"


# --- The whole point: PICASO differentiates hot Jupiters (parametric made them near-identical) ---
def test_picaso_differentiates_hot_jupiters():
    ids = ["hd-189733-b", "51-peg-b", "hd-209458-b", "wasp-12-b", "wasp-43-b"]
    recs = [_BY_ID[i] for i in ids if i in _BY_ID]
    if not all(r.params.spectrum_source == "picaso" for r in recs):
        pytest.skip("hot Jupiters not all built with PICASO")
    hexes = {r.true_colour.hex for r in recs}
    assert len(hexes) >= 3, f"expected varied hot-Jupiter colours, got {hexes}"


def test_picaso_albedo_bounded():
    rec = _BY_ID["hd-189733-b"]
    try:
        p = _make_from_record(rec)
    except ProviderUnavailable:
        pytest.skip("not cached")
    alb = p.geometric_albedo(GRID_NM)
    assert alb.shape == GRID_NM.shape and np.all((alb >= 0) & (alb <= 1))


def test_unavailable_without_cache_or_venv(monkeypatch, tmp_path):
    # Point the cache at an empty dir and disable the venv path -> must raise, not crash.
    from pipeline.spectrum import picaso_model

    monkeypatch.setattr(picaso_model, "SPECTRA_CACHE_DIR", tmp_path)
    monkeypatch.setenv("PICASO_VENV_PYTHON", str(tmp_path / "nope"))
    monkeypatch.delenv("PICASO_OPACITY_DB", raising=False)
    with pytest.raises(ProviderUnavailable):
        make_picaso(equilibrium_temp_k=1200.0, radius_r_earth=12.0, mass_m_earth=300.0,
                    teff_k=5500.0, metallicity=1.0)
