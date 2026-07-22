"""Curated batch of real, well-characterised planets for Milestone 2.

Each entry is a real Exoplanet Archive `pl_name`. We fetch their parameters, map them to an
albedo regime (pipeline.spectrum.parametric), use the real host-star Teff as a blackbody
illuminant, and build PlanetInputs. `is_cgi_target` marks Roman-Coronagraph-style targets
(RV giants) whose Roman view is simulated now and will accept real photometry post-launch;
microlensing planets are flagged `is_light_isolable=False` (their light is never isolable).
"""

from __future__ import annotations

import re

from pipeline.emit.build import PlanetInput
from pipeline.fetch.archive import ArchiveRecord, fetch_by_names
from pipeline.illuminant.blackbody import BlackbodyStar
from pipeline.models import Discovery, HostStar, PlanetParams
from pipeline.spectrum.router import choose_model

# Planets flagged as Roman-CGI-style reflected-light targets (RV giants at wide separation).
_CGI_TARGETS = {"47 UMa b", "ups And d", "upsilon And d", "47 UMa c"}

# The Archive returns abbreviated discovery-method codes; map to readable labels.
_METHOD_LABELS = {
    "rv": "Radial Velocity",
    "tran": "Transit",
    "micro": "Microlensing",
    "imag": "Imaging",
    "ttv": "Transit Timing Variations",
    "ast": "Astrometry",
    "puls": "Pulsar Timing",
}


def _method_label(code: str | None) -> str:
    if not code:
        return "Unknown"
    return _METHOD_LABELS.get(code.lower(), code)

# The curated name list. Chosen for recognisability and type coverage.
CURATED_NAMES: list[str] = [
    "HD 189733 b",     # archetypal hot Jupiter — measured deep blue
    "51 Peg b",        # first hot Jupiter around a Sun-like star
    "HD 209458 b",     # "Osiris", first transiting planet
    "WASP-12 b",       # ultra-hot, very dark
    "WASP-121 b",      # ultra-hot Jupiter
    "WASP-43 b",       # hot Jupiter
    "51 Eri b",        # directly imaged cool jovian
    "HR 8799 b",       # imaged cold giant
    "HR 8799 c",       # imaged cold giant
    "HR 8799 e",       # imaged cold giant
    "beta Pic b",      # imaged young giant
    "HD 95086 b",      # imaged cold giant
    "GJ 504 b",        # imaged cold, low-mass giant
    "47 UMa b",        # RV giant — Roman CGI-style target
    "ups And d",       # RV giant — Roman CGI-style target
    "Kepler-186 f",    # rocky, temperate
    "TRAPPIST-1 e",    # rocky, temperate
    "Proxima Cen b",   # nearest rocky planet
    "GJ 1214 b",       # warm sub-Neptune
    "OGLE-2005-BLG-390L b",  # microlensing — light never isolable
]


def _slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _model_temperature(rec: ArchiveRecord, eq_temp: float | None) -> float | None:
    """Temperature that sets the reflected-light regime. Usually the archive equilibrium
    temp, but for internal-heat-dominated young imaged giants (archive pl_eqt >> irradiation
    temp) use the irradiation temp — otherwise they are mis-routed to the hot-Jupiter engine
    and render an unphysical clipped blue. The 3x guard only triggers on clear cases and
    leaves normal irradiated planets (where the two temps ~match) untouched."""
    irr = rec.irradiation_temp_k()
    if irr is not None and eq_temp is not None and eq_temp > 3.0 * irr:
        return irr
    return eq_temp


def _to_input(rec: ArchiveRecord) -> PlanetInput:
    eq_temp = rec.equilibrium_temp_k()
    teff = rec.st_teff if rec.st_teff is not None else 5772.0
    # The Archive returns abbreviated method codes ("micro", "tran", "rv", "imag", ...).
    is_microlensing = "micro" in (rec.disc_method or "").lower()

    # The router picks the best available albedo engine (Cahoy / PICASO / parametric) and
    # reports which it used; with no grid/opacity data installed it returns parametric.
    model = choose_model(
        equilibrium_temp_k=_model_temperature(rec, eq_temp),
        radius_r_earth=rec.pl_rade,
        mass_m_earth=rec.pl_bmasse,
        semi_major_axis_au=rec.pl_orbsmax,
        teff_k=teff,
    )

    host = HostStar(
        name=rec.hostname or rec.pl_name,
        teff_k=teff,
        spectral_type=rec.st_spectype,
    )
    params = PlanetParams(
        equilibrium_temp_k=eq_temp,
        radius_r_earth=rec.pl_rade,
        mass_m_earth=rec.pl_bmasse,
        semi_major_axis_au=rec.pl_orbsmax,
        assumed_cloud_state=model.cloud_state,
        assumed_metallicity=model.metallicity,
        assumed_phase_angle_deg=model.phase_angle_deg,
        spectrum_source=model.source,
    )
    discovery = Discovery(
        method=_method_label(rec.disc_method),
        year=rec.disc_year,
        facility=rec.disc_facility,
    )
    return PlanetInput(
        id=_slug(rec.pl_name),
        name=rec.pl_name,
        host_star=host,
        params=params,
        discovery=discovery,
        provider=model.provider,
        illuminant=BlackbodyStar(teff_k=teff),
        is_light_isolable=not is_microlensing,
        is_cgi_target=rec.pl_name in _CGI_TARGETS,
    )


def catalog_planets(names: list[str] | None = None, *, use_cache: bool = True) -> list[PlanetInput]:
    records = fetch_by_names(names or CURATED_NAMES, use_cache=use_cache)
    return [_to_input(rec) for rec in records]
