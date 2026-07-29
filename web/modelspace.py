"""Build-time adapter: PlanetRecord -> the model-space payload the planet page inlines.

Like the host-star lamp and the palette ramp, this is derived at SITE-BUILD time from values
every record already carries (its albedo spectrum, equilibrium temperature, orbit and host
Teff), so it ships on the next deploy with no data re-release. The physics lives in
`pipeline.modelspace`; this module only decides what the page needs and names it compactly —
the payload is inlined into ~5.8k pages, so keys are short on purpose.
"""

from __future__ import annotations

import numpy as np

from pipeline.config import GRID_NM
from pipeline.illuminant.blackbody import BlackbodyStar
from pipeline.models import PlanetRecord
from pipeline.modelspace import colour_year, migration_track, what_if_variants


def modelspace_ctx(rec: PlanetRecord) -> dict | None:
    """Everything the migration slider, the what-if panel and the colour year need.

    None when the record carries no albedo spectrum (pre-v1 releases) — the page then simply
    renders without the panel rather than with an empty one.
    """
    if rec.spectrum is None or rec.true_colour is None:
        return None

    params = rec.params
    eq_temp_k = params.equilibrium_temp_k
    if eq_temp_k is None or eq_temp_k <= 0:
        return None  # the whole distance axis is anchored on it; without it there is no track

    star_flux = BlackbodyStar(rec.host_star.teff_k).spectrum(GRID_NM)
    albedo = np.asarray(rec.spectrum.values, dtype=float)

    track = migration_track(
        base_albedo=albedo,
        star_flux=star_flux,
        eq_temp_k=eq_temp_k,
        semi_major_axis_au=params.semi_major_axis_au,
        radius_r_earth=params.radius_r_earth,
        mass_m_earth=params.mass_m_earth,
        metallicity=params.assumed_metallicity,
    )
    variants = what_if_variants(
        base_albedo=albedo,
        star_flux=star_flux,
        base_colour_xyz=rec.true_colour.xyz,
        eq_temp_k=eq_temp_k,
        radius_r_earth=params.radius_r_earth,
        mass_m_earth=params.mass_m_earth,
        metallicity=params.assumed_metallicity,
    )
    year = colour_year(
        track=track,
        eccentricity=params.eccentricity,
        semi_major_axis_au=params.semi_major_axis_au,
    )

    return {
        "home": track.home_index,
        # What the WebGL planet renderer needs to draw a disc in any of these colours. Same
        # inputs the page hero uses, so a moved planet is drawn exactly like the real one.
        "planetHex": rec.true_colour.hex,
        "radius": params.radius_r_earth or 8.0,
        "cloudState": params.assumed_cloud_state,
        # Parallel arrays, not a list of objects: this payload is inlined into ~5.8k pages, and
        # repeating five key names 25 times per page costs more than the numbers do.
        "stops": {
            "r": [s.r_over_a for s in track.stops],
            "au": [s.au for s in track.stops],
            "t": [round(s.eq_temp_k) for s in track.stops],
            "h": [s.hex for s in track.stops],
            "l": [round(s.luminance_y, 4) for s in track.stops],
        },
        # Only the grid points that actually fall on the slider get a reference mark; the rest
        # would sit off the ends of the control with nothing to point at.
        "cahoy": [
            {"au": c.au, "r": c.r_over_a, "h": c.hex}
            for c in track.cahoy_points
            if c.in_track_range
        ],
        # Only the per-planet numbers. Each variant's label and explanation are the same
        # sentence on every page, so they live in web/static/modelspace.js keyed by id and are
        # downloaded once rather than 5.8k times.
        "whatif": [
            {"id": v.id, "h": v.hex, "l": round(v.luminance_y, 4), "de": v.delta_e2000}
            for v in variants
        ],
        "year": (
            {
                "e": year.eccentricity,
                "q": year.periastron_au,
                "Q": year.apoastron_au,
                "pos": [round(p, 2) for p in year.track_positions],
                "hot": year.hot_fraction,
            }
            if year
            else None
        ),
        # Solar-system anchors and any future measured spectrum: the starting colour is a real
        # measurement, so the page must say the MOVEMENT is modelled even though the home
        # swatch is not.
        "measured_base": rec.provenance in ("measured-albedo", "measured-cgi"),
    }
