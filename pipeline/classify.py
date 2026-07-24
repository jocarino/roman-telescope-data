"""Classify a planet into a size/temperature type, for the gallery type filter.

Radius is the primary axis (the standard exoplanet size classes); when only a mass is known
we fall back to a mass-based cut. Giants are split into hot-Jupiter vs (cool) gas-giant by
equilibrium temperature — the distinction that actually drives their reflected-light colour."""

from __future__ import annotations

# Chip order + display labels for the type filter.
TYPE_LABELS = {
    "rocky": "Rocky",
    "super-earth": "Super-Earth",
    "neptune": "Neptune-like",
    "gas-giant": "Gas giant",
    "hot-jupiter": "Hot Jupiter",
    "unknown": "Unknown",
}
TYPE_ORDER = ["rocky", "super-earth", "neptune", "gas-giant", "hot-jupiter", "unknown"]

_HOT_JUPITER_TEMP_K = 1000.0


def planet_type(
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    equilibrium_temp_k: float | None,
) -> str:
    """Return one of TYPE_ORDER. Radius-first; mass fallback; giants split hot/cool by temp."""
    cls = _size_class(radius_r_earth, mass_m_earth)
    if cls == "giant":
        hot = equilibrium_temp_k is not None and equilibrium_temp_k >= _HOT_JUPITER_TEMP_K
        return "hot-jupiter" if hot else "gas-giant"
    return cls


def _size_class(radius_r_earth: float | None, mass_m_earth: float | None) -> str:
    if radius_r_earth is not None:
        if radius_r_earth < 1.6:
            return "rocky"
        if radius_r_earth < 2.4:
            return "super-earth"
        if radius_r_earth < 6.0:
            return "neptune"
        return "giant"
    if mass_m_earth is not None:
        if mass_m_earth < 2.0:
            return "rocky"
        if mass_m_earth < 10.0:
            return "super-earth"
        if mass_m_earth < 50.0:
            return "neptune"
        return "giant"
    return "unknown"
