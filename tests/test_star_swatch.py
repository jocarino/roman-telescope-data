"""The host-star "lamp" swatch: blackbody colour from Teff (pipeline.colour.star).

Physics sanity: cool M dwarfs glow orange-red, the Sun warm off-white, hot stars
blue-white, and blueness rises monotonically with temperature.
"""

from __future__ import annotations

from pipeline.colour.star import star_swatch


def _rgb(teff_k: float) -> tuple[int, int, int]:
    return star_swatch(teff_k).srgb


def test_m_dwarf_is_orange_red() -> None:
    r, g, b = _rgb(3000.0)
    assert r > g > b
    assert r - b > 100


def test_sun_is_warm_off_white() -> None:
    r, g, b = _rgb(5772.0)
    assert r > g > b  # warm tilt...
    assert r - b < 40  # ...but near-neutral, not orange
    assert min(r, g, b) > 150  # bright: an off-white, not a colour


def test_hot_star_is_blue_white() -> None:
    r, g, b = _rgb(10000.0)
    assert b > r


def test_blueness_increases_with_teff() -> None:
    blueness = [_rgb(t)[2] - _rgb(t)[0] for t in (3000.0, 4500.0, 5772.0, 7500.0, 10000.0)]
    assert blueness == sorted(blueness)
    assert blueness[0] < 0 < blueness[-1]  # spans warm to cool


def test_cache_collapses_near_identical_teffs() -> None:
    # Teff rounds to 10 K, so stars a few kelvin apart share one cached swatch...
    assert star_swatch(5052.0) is star_swatch(5054.9)
    # ...but genuinely different temperatures do not.
    assert star_swatch(5052.0) is not star_swatch(5066.0)
