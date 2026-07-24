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
from pipeline.fetch.archive import ArchiveRecord, fetch_bulk, fetch_by_names
from pipeline.illuminant.blackbody import BlackbodyStar
from pipeline.models import Discovery, HostStar, ParamSources, PlanetParams
from pipeline.spectrum.router import choose_model

# Planets flagged as Roman-CGI-style reflected-light targets (RV giants at wide separation).
_CGI_TARGETS = {"47 UMa b", "ups And d", "upsilon And d", "47 UMa c"}

# The Archive returns abbreviated discovery-method codes; map to readable labels.
_METHOD_LABELS = {
    "rv": "Radial Velocity",
    "tran": "Transit",
    "micro": "Microlensing",
    "ima": "Imaging",
    "imag": "Imaging",
    "ttv": "Transit Timing Variations",
    "etv": "Eclipse Timing Variations",
    "ast": "Astrometry",
    "puls": "Pulsar Timing",
    "dkin": "Disk Kinematics",
    "obm": "Orbital Brightness Modulation",
}


def _method_label(code: str | None) -> str:
    if not code:
        return "Unknown"
    return _METHOD_LABELS.get(code.lower(), code)

# The curated name list. Chosen for recognisability and type coverage.
CURATED_NAMES: list[str] = [
    "HD 189733 b",     # archetypal hot Jupiter, measured deep blue
    "51 Peg b",        # first hot Jupiter around a Sun-like star
    "HD 209458 b",     # "Osiris", first transiting planet
    "WASP-12 b",       # ultra-hot, very dark
    "WASP-121 b",      # ultra-hot Jupiter
    "WASP-43 b",       # hot Jupiter
    "51 Eri b",        # directly imaged cool jovian
    "HR 8799 b",       # imaged cold giant
    "HR 8799 c",       # imaged cold giant
    "HR 8799 e",       # imaged cold giant
    "bet Pic b",       # imaged young giant (Archive uses the abbreviated "bet")
    "HD 95086 b",      # imaged cold giant
    "GJ 504 b",        # imaged cold, low-mass giant
    "47 UMa b",        # RV giant, Roman CGI-style target
    "ups And d",       # RV giant, Roman CGI-style target
    "Kepler-186 f",    # rocky, temperate
    "TRAPPIST-1 e",    # rocky, temperate
    "Proxima Cen b",   # nearest rocky planet
    "GJ 1214 b",       # warm sub-Neptune
    "OGLE-2005-BLG-390L b",  # microlensing, light never isolable
]


def _slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# The Archive's canonical pl_name abbreviates constellation genitives ("51 Peg b") and Greek
# letters ("ups And d"). The friendlier public NASA display expands them ("51 Pegasi b"). We
# expand only for DISPLAY; the id/slug and data matching still use the raw Archive name.
_CONSTELLATIONS = {
    "And": "Andromedae", "Aqr": "Aquarii", "Aql": "Aquilae", "Ari": "Arietis",
    "Boo": "Bootis", "Cnc": "Cancri", "CVn": "Canum Venaticorum", "CMa": "Canis Majoris",
    "Cap": "Capricorni", "Cas": "Cassiopeiae", "Cen": "Centauri", "Cet": "Ceti",
    "Com": "Comae Berenices", "CrB": "Coronae Borealis", "Cyg": "Cygni", "Dra": "Draconis",
    "Eri": "Eridani", "Gem": "Geminorum", "Her": "Herculis", "Hya": "Hydrae",
    "Leo": "Leonis", "Lib": "Librae", "Lyr": "Lyrae", "Oph": "Ophiuchi", "Ori": "Orionis",
    "Peg": "Pegasi", "Per": "Persei", "Psc": "Piscium", "Pic": "Pictoris", "Sco": "Scorpii",
    "Ser": "Serpentis", "Tau": "Tauri", "Tri": "Trianguli", "UMa": "Ursae Majoris",
    "UMi": "Ursae Minoris", "Vir": "Virginis", "Vul": "Vulpeculae",
}
_GREEK = {
    "alf": "alpha", "bet": "beta", "gam": "gamma", "del": "delta", "eps": "epsilon",
    "zet": "zeta", "tet": "theta", "iot": "iota", "kap": "kappa", "lam": "lambda",
    "ksi": "xi", "omi": "omicron", "sig": "sigma", "ups": "upsilon", "ome": "omega",
}


def _display_name(name: str) -> str:
    out = []
    for tok in name.split():
        if tok in _CONSTELLATIONS:
            out.append(_CONSTELLATIONS[tok])
        elif tok.lower() in _GREEK:
            out.append(_GREEK[tok.lower()])
        else:
            out.append(tok)
    return " ".join(out)


def _model_temperature(rec: ArchiveRecord, eq_temp: float | None) -> float | None:
    """Temperature that sets the reflected-light regime. Usually the archive equilibrium
    temp, but for internal-heat-dominated young imaged giants (archive pl_eqt >> irradiation
    temp) use the irradiation temp, otherwise they are mis-routed to the hot-Jupiter engine
    and render an unphysical clipped blue. The 3x guard only triggers on clear cases and
    leaves normal irradiated planets (where the two temps ~match) untouched."""
    irr = rec.irradiation_temp_k()
    if irr is not None and eq_temp is not None and eq_temp > 3.0 * irr:
        return irr
    return eq_temp


def completeness_gate(rec: ArchiveRecord) -> tuple[bool, str | None]:
    """The minimum real data a planet needs before we will model a colour for it. Below this
    there is nothing to anchor an archetype to and the result would be pure guesswork, so we
    exclude it rather than invent it. Returns (ok, reason-if-excluded).

    Requires a SIZE (radius, or a mass we can class by), a real HOST-STAR temperature (the
    illuminant IS the colour, so a made-up star produces a made-up colour and there is no point
    showing it), and a planet TEMPERATURE (measured, or computable from the star + orbit).
    A missing radius on a known giant is still fine (the value is tagged 'assumed' and barely
    affects reflected-light colour); a missing/unknowable illuminant is not."""
    if rec.pl_rade is None and rec.pl_bmasse is None:
        return False, "no size (neither radius nor mass)"
    if rec.st_teff is None:
        return False, "unknown host star (no stellar temperature; the illuminant is the colour)"
    temp_computable = rec.st_rad is not None and rec.pl_orbsmax is not None
    if rec.pl_eqt is None and not temp_computable:
        return False, "no temperature and none computable from star + orbit"
    return True, None


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
        name=_display_name(rec.hostname or rec.pl_name),
        teff_k=teff,
        spectral_type=rec.st_spectype,
    )
    # Per-field origin: a real Archive measurement, a value we computed, or an archetype
    # assumption. Cloud/metallicity/phase are always assumed (we hold no per-planet atmosphere
    # data); eqt is measured if the Archive gives it, else computed from the star + orbit.
    eq_source = (
        "measured" if rec.pl_eqt is not None else ("computed" if eq_temp is not None else "assumed")
    )
    sources = ParamSources(
        equilibrium_temp_k=eq_source,
        radius_r_earth="measured" if rec.pl_rade is not None else "assumed",
        mass_m_earth="measured" if rec.pl_bmasse is not None else "assumed",
        semi_major_axis_au="measured" if rec.pl_orbsmax is not None else "assumed",
        distance_pc="measured" if rec.sy_dist is not None else "assumed",
        star_teff_k="measured" if rec.st_teff is not None else "assumed",
        metallicity="assumed",
        cloud_state="assumed",
        phase_angle_deg="assumed",
    )
    params = PlanetParams(
        equilibrium_temp_k=eq_temp,
        radius_r_earth=rec.pl_rade,
        mass_m_earth=rec.pl_bmasse,
        semi_major_axis_au=rec.pl_orbsmax,
        distance_pc=rec.sy_dist,
        assumed_cloud_state=model.cloud_state,
        assumed_metallicity=model.metallicity,
        assumed_phase_angle_deg=model.phase_angle_deg,
        spectrum_source=model.source,
        sources=sources,
    )
    discovery = Discovery(
        method=_method_label(rec.disc_method),
        year=rec.disc_year,
        facility=rec.disc_facility,
    )
    return PlanetInput(
        id=_slug(rec.pl_name),
        name=_display_name(rec.pl_name),
        host_star=host,
        params=params,
        discovery=discovery,
        provider=model.provider,
        illuminant=BlackbodyStar(teff_k=teff),
        is_light_isolable=not is_microlensing,
        is_cgi_target=rec.pl_name in _CGI_TARGETS,
    )


def _apply_gate(records: list[ArchiveRecord], *, verbose: bool = True) -> list[PlanetInput]:
    """Run each fetched record through the completeness gate; keep passers, log exclusions."""
    kept: list[PlanetInput] = []
    excluded: list[tuple[str, str]] = []
    for rec in records:
        ok, reason = completeness_gate(rec)
        if not ok:
            excluded.append((rec.pl_name, reason or "incomplete"))
            continue
        kept.append(_to_input(rec))
    if excluded and verbose:
        print(f"Completeness gate: excluded {len(excluded)} of {len(records)} planet(s):")
        # At scale the per-planet list is noise; summarise by reason, show a few examples.
        by_reason: dict[str, list[str]] = {}
        for name, reason in excluded:
            by_reason.setdefault(reason, []).append(name)
        for reason, names in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
            sample = ", ".join(names[:4]) + (" …" if len(names) > 4 else "")
            print(f"  - {len(names):>3}× {reason}  ({sample})")
    return kept


def catalog_planets(names: list[str] | None = None, *, use_cache: bool = True) -> list[PlanetInput]:
    """The curated set (or an explicit name list), passed through the completeness gate."""
    records = fetch_by_names(names or CURATED_NAMES, use_cache=use_cache)
    return _apply_gate(records)


def catalog_bulk(limit: int, *, use_cache: bool = True) -> list[PlanetInput]:
    """A scaled catalog: the curated planets (always pinned) plus the nearest well-characterised
    planets from the Archive, up to `limit` total, de-duplicated by planet id and gate-checked."""
    curated = fetch_by_names(CURATED_NAMES, use_cache=use_cache)
    bulk = fetch_bulk(limit, use_cache=use_cache)
    seen: set[str] = set()
    merged: list[ArchiveRecord] = []
    for rec in [*curated, *bulk]:  # curated first so pinned planets always win a dedupe
        key = rec.pl_name
        if key in seen:
            continue
        seen.add(key)
        merged.append(rec)
    kept = _apply_gate(merged)
    print(f"Scaled catalog: {len(kept)} planets kept (curated pinned + nearest {limit}).")
    return kept
