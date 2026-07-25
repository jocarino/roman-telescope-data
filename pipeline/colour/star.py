"""Host-star swatch: the star's own colour — "the lamp" every planet colour reflects.

A planet makes no visible light of its own; its palette is its star's light filtered by the
atmosphere. This module renders the lamp itself: the star's blackbody spectrum pushed through
the exact same CIE codepath as the planets (chromaticity at the fixed display luminance), so
star and planet swatches are directly comparable — cool M dwarfs come out orange-red, the Sun
warm off-white, hot A/B stars blue-white.

It is a pure function of the star's Teff, which every planets.json record already carries —
so the site build can derive it without a data re-release.
"""

from __future__ import annotations

from functools import lru_cache

from pipeline.colour.cie import ColourResult, reflected_flux_to_colour
from pipeline.config import GRID_NM
from pipeline.illuminant.blackbody import BlackbodyStar


@lru_cache(maxsize=4096)
def _swatch_at(teff_10k: int) -> ColourResult:
    flux = BlackbodyStar(teff_k=float(teff_10k) * 10.0).spectrum(GRID_NM)
    return reflected_flux_to_colour(flux, method="blackbody-star")


def star_swatch(teff_k: float) -> ColourResult:
    """Swatch colour of a star's own light, from its effective temperature.

    Teff is rounded to 10 K — far below a visible colour difference — so the cache collapses
    the catalog's ~thousands of near-identical stars into a few hundred entries.
    `luminance_y` on the result is the display constant, not a physical brightness; a star
    has no meaningful "reflectance" so only the chromaticity (hex/srgb) is meaningful here.
    """
    return _swatch_at(round(teff_k / 10.0))
