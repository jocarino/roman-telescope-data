"""Milestone-1 gate (from CLAUDE.md): the three archetypes must land the right colours.

  - cloudy Jupiter analog  -> warm off-white/cream, bright
  - deep-methane Neptune   -> blue-green
  - cloud-free hot Jupiter -> dark (low true luminance)
"""

from __future__ import annotations

import numpy as np

from pipeline.colour.cie import reflected_flux_to_colour
from pipeline.config import GRID_NM
from pipeline.illuminant.blackbody import SUN
from pipeline.spectrum.synthetic import (
    CLOUDFREE_HOT_JUPITER,
    CLOUDY_JUPITER,
    METHANE_NEPTUNE,
)

_STAR = SUN.spectrum(GRID_NM)


def _true_colour(provider):
    flux = provider.geometric_albedo(GRID_NM) * _STAR
    return reflected_flux_to_colour(flux, method="full-spectrum", illuminant_flux=_STAR)


def test_cloudy_jupiter_is_warm_and_bright():
    c = _true_colour(CLOUDY_JUPITER)
    r, g, b = c.srgb
    assert r >= b, f"expected warm (R>=B), got {c.srgb} {c.hex}"
    assert c.luminance_y > 0.4, f"expected bright, got lumY={c.luminance_y}"
    # near-neutral: not strongly saturated
    assert max(c.srgb) - min(c.srgb) < 40, f"expected near-neutral cream, got {c.srgb}"


def test_methane_neptune_is_blue_green():
    c = _true_colour(METHANE_NEPTUNE)
    r, g, b = c.srgb
    assert b > r and g > r, f"expected blue-green (G,B > R), got {c.srgb} {c.hex}"


def test_cloudfree_hot_jupiter_is_dark():
    c = _true_colour(CLOUDFREE_HOT_JUPITER)
    assert c.luminance_y < 0.15, f"expected dark (low true luminance), got lumY={c.luminance_y}"


def test_cutting_clouds_and_methane_darkens():
    bright = _true_colour(CLOUDY_JUPITER).luminance_y
    dark = _true_colour(CLOUDFREE_HOT_JUPITER).luminance_y
    assert dark < bright, "removing clouds should reduce reflected luminance"


def test_grid_has_81_samples():
    assert len(GRID_NM) == 81
    assert np.isclose(GRID_NM[0], 380.0) and np.isclose(GRID_NM[-1], 780.0)
