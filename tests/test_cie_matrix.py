"""The two memoised matrices in pipeline.colour.cie must BE colour-science's own transforms,
not an approximation of them.

Both are cached by probing the library function with basis vectors, which is exact only
because each transform is linear. These tests are what makes that claim checkable: if a
future colour-science release makes either step non-linear (an out-of-gamut roll-off in
XYZ_to_sRGB, say), the probe would silently start returning wrong colours for every planet
on the site — and these tests would fail instead.
"""

from __future__ import annotations

import numpy as np
import pytest
from colour import XYZ_to_sRGB

from pipeline.colour.cie import (
    _flux_to_xyz,
    _sd_to_xyz,
    _xyz_to_linear_srgb_matrix,
    reflected_flux_to_colour,
)
from pipeline.config import GRID_N


def _random_spectra(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Spread over many orders of magnitude: stellar flux scales are enormous and the
    # normalisation must not care.
    scales = 10.0 ** rng.uniform(-6, 12, size=(n, 1))
    return rng.random((n, GRID_N)) * scales


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_flux_matrix_reproduces_colour_science_integral(seed: int) -> None:
    for flux in _random_spectra(12, seed):
        assert np.allclose(_flux_to_xyz(flux), _sd_to_xyz(flux), rtol=1e-12, atol=0.0)


def test_flux_matrix_batch_matches_one_at_a_time() -> None:
    fluxes = _random_spectra(40, 7)
    batched = _flux_to_xyz(fluxes)
    assert batched.shape == (40, 3)
    for i, flux in enumerate(fluxes):
        assert np.allclose(batched[i], _sd_to_xyz(flux), rtol=1e-12, atol=0.0)


@pytest.mark.parametrize("seed", [3, 4])
def test_srgb_matrix_reproduces_colour_science_transform(seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(20):
        xyz = rng.random(3) * rng.uniform(0.01, 5.0)
        expected = np.asarray(XYZ_to_sRGB(xyz, apply_cctf_encoding=False))
        assert np.allclose(xyz @ _xyz_to_linear_srgb_matrix(), expected, rtol=1e-12, atol=1e-15)


def test_zero_flux_is_handled_not_divided_by() -> None:
    result = reflected_flux_to_colour(
        np.zeros(GRID_N), method="full-spectrum", illuminant_flux=np.ones(GRID_N)
    )
    assert result.hex == "#000000"
    assert result.luminance_y == 0.0
