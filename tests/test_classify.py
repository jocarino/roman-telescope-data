"""Planet-type classification (pure logic)."""

from __future__ import annotations

from pipeline.classify import planet_type


def test_rocky_by_radius():
    assert planet_type(1.0, None, 300.0) == "rocky"
    assert planet_type(1.5, None, 300.0) == "rocky"


def test_super_earth_by_radius():
    assert planet_type(2.0, None, 400.0) == "super-earth"


def test_neptune_by_radius():
    assert planet_type(4.0, None, 200.0) == "neptune"


def test_cool_giant_is_gas_giant():
    assert planet_type(12.0, None, 200.0) == "gas-giant"


def test_hot_giant_is_hot_jupiter():
    assert planet_type(12.0, None, 1500.0) == "hot-jupiter"


def test_giant_without_temp_is_gas_giant():
    # No temperature -> can't call it hot; default to the cool label.
    assert planet_type(12.0, None, None) == "gas-giant"


def test_mass_fallback_when_no_radius():
    assert planet_type(None, 1.0, 300.0) == "rocky"
    assert planet_type(None, 5.0, 300.0) == "super-earth"
    assert planet_type(None, 30.0, 300.0) == "neptune"
    assert planet_type(None, 500.0, 1200.0) == "hot-jupiter"


def test_unknown_when_no_size():
    assert planet_type(None, None, 300.0) == "unknown"
