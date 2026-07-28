"""Static-site generator: read data/planets.json, render the gallery, per-planet detail
pages, and the long-press peek fragments into an output directory, then copy static
assets. (Per-planet DETAIL fragments were once emitted too, for an htmx drawer that no
longer exists; at ~770 KB × 6k planets they were half the site, so they are gone.)

    uv run python -m site.build --out dist

Pure static consumer — no colour maths here; both colours and palettes are precomputed in
planets.json. A regenerated planets.json (e.g. after real measured data lands) just changes
what renders; no template edits.

Two derived exceptions, both pure functions of values every record already carries, so both
ship on the next deploy with no data re-release:

- the host-star "lamp" swatch (pipeline.colour.star), from the star's Teff;
- the 5-stop palette ramp (pipeline.palette.derive), from the colour's own base hex. Ramps
  in already-released planets.json files are non-monotonic (see derive.py), so they are
  re-derived here rather than trusted. Base colours are never recomputed — the physics is
  read from planets.json exactly as written.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline.classify import planet_type
from pipeline.colour.family import colour_family
from pipeline.colour.star import star_swatch
from pipeline.illuminant.blackbody import SUN
from pipeline.models import PaletteStopModel, PlanetRecord, PlanetsFile
from pipeline.palette.derive import derive_palette_from_hex
from pipeline.palette.export import ase_bytes
from pipeline.sky import format_dec, format_ra
from pipeline.tours import Tour, TourStop
from pipeline.tours import resolve as resolve_tours
from web.hz import hz_strip_svg
from web.sky import sky_chart_svg, sky_field_svg
from web.svg import spectrum_svg

_HERE = Path(__file__).parent
_TEMPLATES = _HERE / "templates"
_STATIC = _HERE / "static"
_DEFAULT_JSON = Path("data/planets.json")
# Curated "seen in fiction" overlay: real systems that appear in named books/films/games.
# Hand-maintained, kept OUT of planets.json, joined here by planet name. Optional — a missing
# file just means no fiction sections render.
_FICTION_JSON = Path("data/fiction-references.json")
# Every jargon term on the site, defined once. Feeds both the /glossary page and the
# site-wide hover tooltips (templates mark a term with the g() macro; the short definition
# is shipped as one cached JS file rather than inlined into 900+ pages).
_GLOSSARY_JSON = Path("data/glossary.json")


def _load_glossary(path: Path = _GLOSSARY_JSON) -> dict:
    """The glossary document: {"categories": [...], "terms": [...]}. Missing file = no
    glossary page and inert (unstyled-but-readable) jargon markup, never a broken build."""
    if not path.exists():
        return {"categories": [], "terms": []}
    doc = json.loads(path.read_text())
    return {
        "categories": doc.get("categories", []),
        "terms": [t for t in doc.get("terms", []) if t.get("id") and t.get("term")],
    }


def _glossary_runtime_js(terms: list[dict]) -> str:
    """The hover-tooltip payload: id -> {t: term, s: short}. Only what a tooltip needs — the
    long definitions stay on the glossary page, so this stays a few KB for every page."""
    lookup = {t["id"]: {"t": t["term"], "s": t["short"]} for t in terms}
    return "window.GLOSSARY=" + json.dumps(lookup, separators=(",", ":")) + ";\n"


def _load_fiction(path: Path = _FICTION_JSON) -> dict[str, dict]:
    """Map archive planet name -> {system, recognizability, references} for planets that appear
    in fiction. Only the confirmed `systems` block is used (star-only cameos have no planet to
    join to). `unverified` references are dropped so the public page stays honest; a system left
    with no references is omitted entirely."""
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    lookup: dict[str, dict] = {}
    for sysrec in doc.get("systems", []):
        refs = [r for r in sysrec.get("references", []) if r.get("confidence") != "unverified"]
        if not refs:
            continue
        entry = {
            "system": sysrec["system"],
            "recognizability": sysrec.get("recognizability"),
            "references": refs,
        }
        for pl in sysrec.get("planets", []):
            lookup[pl["archive_name"]] = entry
    return lookup


def _tour_stop_ctx(stop: TourStop) -> dict:
    """Everything one tour stop needs, formatted here rather than in the template: the numbers
    a newcomer can read, plus the raw values the planet renderer wants."""
    rec = stop.planet
    view = rec.instrument_views[0]
    p = rec.params
    ly = round(p.distance_pc * _LY_PER_PC, 1) if p.distance_pc else None
    return {
        "rec": rec,
        "id": rec.id,
        "name": rec.name,
        "host": rec.host_star.name,
        "star": " · ".join(
            x
            for x in (
                f"{round(rec.host_star.teff_k):,} K" if rec.host_star.teff_k else None,
                rec.host_star.spectral_type,
            )
            if x
        ),
        "hex": rec.true_colour.hex,
        "palette": [s.hex for s in rec.true_colour.palette],
        "radius": p.radius_r_earth or "",
        "cloud": p.assumed_cloud_state,
        "lum": f"{rec.true_colour.luminance_y:.4f}",
        "temp": f"{round(p.equilibrium_temp_k):,} K" if p.equilibrium_temp_k else "unknown",
        "size": f"{p.radius_r_earth:.1f} × Earth's radius" if p.radius_r_earth else "unknown",
        # Solar-system anchors sit a few ten-thousandths of a parsec away; "0.0 ly" would be
        # both wrong-looking and beside the point for them.
        "dist": (
            f"{ly:,.1f} light-years" if ly and ly >= 0.1 else "in our own solar system"
        ),
        "reflect": f"{rec.true_colour.luminance_y * 100:.1f} % of the light that reaches it",
        "roman_hex": view.colour.hex,
        "roman_de": (
            f"{view.reconstruction_error.delta_e2000:.0f}" if view.reconstruction_error else ""
        ),
        # Phase-resolved colours, so a tour stop can run the same wax/wane cycle as the planet
        # page's hero (empty for records from a pre-phase data release: the render then just
        # sits at its default phase).
        "phases": (
            [
                {"d": c.phase_deg, "h": c.hex, "l": round(c.luminance_y, 4)}
                for c in rec.phase_colours.colours
            ]
            if rec.phase_colours
            else []
        ),
        "metric": stop.metric,
        "caption": stop.caption,
        "note": stop.note,
        "caveat": stop.caveat,
    }


def _tour_pages(env: Environment, tours: list[Tour], out: Path, build_id: str, n: int) -> None:
    """One index page plus one page per tour, under /tours/. Written as tours/index.html so the
    clean-URL rule (`try_files $uri $uri.html $uri/index.html`) serves /tours and /tours/<id>."""
    (out / "tours").mkdir(parents=True, exist_ok=True)
    (out / "tours" / "index.html").write_text(
        env.get_template("tours.html").render(tours=tours, n_planets=n, build_id=build_id)
    )
    tpl = env.get_template("tour.html")
    for tour in tours:
        (out / "tours" / f"{tour.id}.html").write_text(
            tpl.render(
                tour=tour,
                stops=[_tour_stop_ctx(s) for s in tour.stops],
                n_planets=n,
                build_id=build_id,
            )
        )


def _cockpit_instruments(records: list[PlanetRecord]) -> dict:
    """Real data for the 404 cockpit's instruments. `nearest`: the three nearest exoplanets
    (solar-system anchors excluded — "nearest world: Earth" is true but useless on a
    lost-in-space page), each with its real sky RA so the radar plots genuine positions.
    `spec`: one real reflected-light curve for the signal-trace screen — HD 189733 b (the
    most famous measured-colour planet) when present, else the first record with a
    spectrum."""
    cands = [r for r in records if r.params.distance_pc and r.params.distance_pc > 0.001]
    near = sorted(cands, key=lambda r: r.params.distance_pc)[:3]
    nearest = [
        {
            "id": r.id,
            "name": r.name,
            "ly": round(r.params.distance_pc * _LY_PER_PC, 1),
            "ra": round(r.sky.ra_deg, 1) if r.sky else (i * 137.0) % 360,
        }
        for i, r in enumerate(near)
    ]
    spec_rec = next((r for r in records if r.id == "hd-189733-b" and r.spectrum), None)
    if spec_rec is None:
        spec_rec = next((r for r in records if r.spectrum), None)
    spec = None
    if spec_rec is not None:
        vals = spec_rec.spectrum.values
        step = max(1, len(vals) // 64)
        ds = vals[::step][:64]
        mx = max(ds) or 1.0
        spec = {"id": spec_rec.id, "name": spec_rec.name, "vals": [round(v / mx, 3) for v in ds]}
    return {"nearest": nearest, "spec": spec}


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


# Approximate count of confirmed exoplanets, for the honest "modelling N of ~M" line. Rounded
# so it doesn't go stale precisely; refresh occasionally from the Archive's pscomppars count.
KNOWN_TOTAL_APPROX = 6300

# Distance is stored in parsecs but shown in light-years everywhere (friendlier to non-astronomers).
_LY_PER_PC = 3.26156


def _fmt_insolation(s: float | None) -> str | None:
    """Starlight received, Earth = 1. Spans 0.001x to 7,000x, so pick precision by magnitude."""
    if s is None:
        return None
    if s >= 100:
        return f"{s:,.0f}"
    if s >= 10:
        return f"{s:.1f}"
    if s >= 1:
        return f"{s:.2f}"
    if s >= 0.01:
        return f"{s:.3f}".rstrip("0")
    return f"{s:.4f}".rstrip("0")


def _planet_ctx(
    rec: PlanetRecord,
    fiction: dict[str, dict] | None = None,
    sky_points: list[tuple[float, float]] | None = None,
    tour_membership: dict[str, list[dict]] | None = None,
    sky_field_urls: tuple[str, str] | None = None,
) -> dict:
    view = rec.instrument_views[0]
    args = dict(
        true_albedo=rec.spectrum.values,
        roman_recon=view.reconstruction.values,
        extrap_below_nm=view.reconstruction.extrapolated_below_nm,
    )
    # Two scope faces: wide for desktop, near-square for phones (CSS picks one).
    return {
        "record": rec,
        # The lamp: the host star's own blackbody colour (and the Sun's, for the sun-swap
        # knob to switch the lamp display to). Derived from Teff at build time — see module
        # docstring.
        "star": star_swatch(rec.host_star.teff_k),
        "sun_lamp": star_swatch(SUN.teff_k),
        "spectrum_svg": spectrum_svg(**args),
        "spectrum_svg_compact": spectrum_svg(**args, compact=True),
        "fiction": (fiction or {}).get(rec.name),
        # Guided tours this planet is a stop on, so a planet page can point back at the walk
        # it belongs to (empty for the great majority of planets).
        "tours": (tour_membership or {}).get(rec.id, []),
        # None (no chart) for records without a sky position, e.g. pre-sky data releases.
        # The ~5.8k starfield dots are the same on every page, so they are referenced from one
        # shared file rather than inlined here; see sky_field_svg.
        "sky_svg": (
            sky_chart_svg(rec.sky, sky_points or [], field_url=(sky_field_urls or (None, None))[0])
            if rec.sky
            else None
        ),
        "sky_svg_compact": (
            sky_chart_svg(
                rec.sky,
                sky_points or [],
                compact=True,
                field_url=(sky_field_urls or (None, None))[1],
            )
            if rec.sky
            else None
        ),
        "sky_ra": format_ra(rec.sky.ra_deg) if rec.sky else None,
        "sky_dec": format_dec(rec.sky.dec_deg) if rec.sky else None,
        # None (no panel) when the star or orbit is too sparsely measured to place a zone.
        "hz_svg": hz_strip_svg(rec),
        "hz_svg_compact": hz_strip_svg(rec, compact=True),
        "hz_insol": _fmt_insolation(
            rec.habitability.insolation_earth if rec.habitability else None
        ),
    }


def _r(value: float | None, places: int) -> float | None:
    """Round for the index, passing None through.

    Values reach the index straight off the record, where they carry full float repr — a
    distance of 0.00014630707286050534 pc, a luminance of 0.059143490457500454. That is
    ~370 KB of digits nothing reads: every one of these is either displayed rounded hard
    (temperature as a whole number, radius to 1 dp) or used only to order a list. The
    precisions below are still far finer than anything shown, and were picked to leave the
    gallery's sorts in the same order — see tests/test_index_precision.py.
    """
    return None if value is None else round(value, places)


def _index_entry(rec: PlanetRecord, fiction: dict[str, dict] | None = None) -> dict:
    view = rec.instrument_views[0]
    entry = {
        "id": rec.id,
        "name": rec.name,
        "host": rec.host_star.name,
        "prov": rec.provenance,
        "temp": _r(rec.params.equilibrium_temp_k, 2),
        "dist": _r(rec.params.distance_pc, 8),
        "lum": _r(rec.true_colour.luminance_y, 7),
        "de": (
            round(view.reconstruction_error.delta_e2000, 4)
            if view.reconstruction_error
            else 0.0
        ),
        "hex": rec.true_colour.hex,
        "family": colour_family(tuple(rec.true_colour.srgb)),
        "ptype": planet_type(
            rec.params.radius_r_earth, rec.params.mass_m_earth, rec.params.equilibrium_temp_k
        ),
        "disc": rec.discovery.method,
        # The same four things again, as Roman's four bands would recover them. The gallery's
        # "seen from Roman" view swaps every colour-derived control onto these (swatch, colour
        # family, brightness sort, similar-colour sort), so the whole grid behaves as if the
        # four-band colour were the only colour there is. Costs ~90 bytes/planet in the index.
        "rhex": view.colour.hex,
        "rfam": colour_family(tuple(view.colour.srgb)),
        "rlum": round(view.colour.luminance_y, 5),
        # Habitable-zone lens: the zone the orbit falls in, and whether the planet is small
        # enough to have a surface. The gallery derives "could hold liquid water" from both.
        "hz": rec.habitability.zone if rec.habitability else "unknown",
        "srf": rec.habitability.surface if rec.habitability else "unknown",
        # For the card planet renders. The 5-stop ramps are NOT here: they are a pure function
        # of the hexes above (pipeline/palette/derive.py), so the browser derives them with
        # PlanetRender.ramp instead — ten hexes a planet was ~29% of this file.
        "radius": _r(rec.params.radius_r_earth, 4),
        "cloud": rec.params.assumed_cloud_state,
        "dist_ly": (
            round(rec.params.distance_pc * _LY_PER_PC, 1) if rec.params.distance_pc else None
        ),
    }
    # Fiction flag: the system name if this planet appears in the curated overlay, else absent
    # (kept off the entry entirely so the 900+ non-fiction rows stay lean). Drives the gallery
    # "seen in fiction" filter.
    fic = (fiction or {}).get(rec.name)
    if fic:
        entry["fic"] = fic["system"]
    return entry


def _extra_entry(rec: PlanetRecord) -> dict:
    """The fields only /compare and /sky read, split out of the main index.

    Every page that shows the grid — the gallery, the census, the 404 cockpit — pays for the
    index on first load, and these fields are dead weight to all of them: the star and orbit
    numbers are read only by the compare table, the sky coordinates only by "your sky
    tonight". Together they were ~22% of the index.

    Written in the same order as _index_entry, as a parallel array with no ids: the two files
    are generated from one pass over the same records, and the consumers zip them by position
    (see tests/test_index_split.py, which pins that alignment).
    """
    extra: dict = {
        "starTeff": _r(rec.host_star.teff_k, 1),
        "starType": rec.host_star.spectral_type,
        "metal": _r(rec.params.assumed_metallicity, 3),
        # Shown as "× Earth's mass" and " AU" to a couple of decimals; the record's full
        # float repr (193.87532827, 0.1765736996) is digits nobody reads. See _r.
        "mass": _r(rec.params.mass_m_earth, 4),
        "sma": _r(rec.params.semi_major_axis_au, 6),
        "year": rec.discovery.year,
    }
    # Sky position for the "your sky tonight" page (absent for pre-sky data releases).
    if rec.sky:
        extra["ra"] = round(rec.sky.ra_deg, 2)
        extra["dec"] = round(rec.sky.dec_deg, 2)
        if rec.sky.v_mag is not None:
            extra["vmag"] = round(rec.sky.v_mag, 1)
    return extra


def _stats(records: list[PlanetRecord]) -> dict:
    des = [
        v.reconstruction_error.delta_e2000
        for r in records
        for v in r.instrument_views
        if v.reconstruction_error
    ]
    # How many planets change colour FAMILY between the two views — the honest headline for
    # "how much colour identity survives Roman's filter set", and the number the gallery's
    # view-toggle explainer quotes. Derived, never hardcoded, so it stays true as data changes.
    shifted = sum(
        1
        for r in records
        if colour_family(tuple(r.true_colour.srgb))
        != colour_family(tuple(r.instrument_views[0].colour.srgb))
    )
    return {
        "total": len(records),
        "median_de": f"{statistics.median(des):.1f}" if des else "—",
        "cgi_targets": sum(1 for r in records if r.provenance == "simulated-cgi"),
        "microlensing": sum(1 for r in records if not r.is_light_isolable),
        "family_shift_pct": round(100 * shifted / len(records)) if records else 0,
    }


def _rederive_palettes(records: list[PlanetRecord]) -> None:
    """Rebuild every ramp from its stored base hex, in place.

    Palettes are a pure function of the base colour, so a ramp fix does not need a spectrum
    re-run or a data re-release -- it lands on the next deploy. Data written before the ramp
    was fixed carries a non-monotonic ramp (the old middle stop kept the base's own lightness
    and overshot the tints); this re-derives it. Colours themselves are untouched: the physics
    stays exactly as `planets.json` recorded it.
    """
    for rec in records:
        for colour in (rec.true_colour, *(v.colour for v in rec.instrument_views)):
            ramp = derive_palette_from_hex(colour.hex)
            accents = [s for s in colour.palette if s.role == "accent"]
            colour.palette = [
                PaletteStopModel(hex=s.hex, role=s.role, source_nm=s.source_nm) for s in ramp
            ] + accents


def build(planets_json: Path = _DEFAULT_JSON, out: Path = Path("dist")) -> Path:
    doc = PlanetsFile.model_validate_json(planets_json.read_text())
    records = doc.planets
    _rederive_palettes(records)
    env = _env()

    if out.exists():
        shutil.rmtree(out)
    (out / "planet").mkdir(parents=True)
    (out / "fragments" / "peek").mkdir(parents=True)
    (out / "palettes").mkdir(parents=True)

    fiction = _load_fiction()
    glossary = _load_glossary()
    # Cache-bust static assets on every build so browsers never serve a stale JS/CSS.
    build_id = str(int(time.time()))

    # Jargon definitions for the hover tooltips, one cached file for the whole site.
    (out / f"glossary.terms.{build_id}.js").write_text(_glossary_runtime_js(glossary["terms"]))

    # Emit one .ase per planet (true-colour + Roman-view stops, named), plus the star+planet
    # duotone pair: the host star's own colour ("lamp") and the planet base, as two inks.
    for rec in records:
        entries: list[tuple[str, str]] = [
            (f"{rec.name} true {s.role}", s.hex) for s in rec.true_colour.palette
        ]
        entries += [
            (f"{rec.name} roman {s.role}", s.hex) for s in rec.instrument_views[0].colour.palette
        ]
        lamp_hex = star_swatch(rec.host_star.teff_k).hex
        entries += [
            (f"{rec.name} duotone lamp ({rec.host_star.name})", lamp_hex),
            (f"{rec.name} duotone planet", rec.true_colour.hex),
        ]
        (out / "palettes" / f"{rec.id}.ase").write_bytes(ase_bytes(entries))

    # The gallery index is fetched at runtime (not inlined) so index.html stays tiny and the
    # grid scales to thousands of planets. Cache-busted by build_id.
    index_entries = [_index_entry(r, fiction) for r in records]
    (out / f"planets.index.{build_id}.json").write_text(
        json.dumps(index_entries, separators=(",", ":"))
    )
    # The compare/sky-only fields, as a parallel array in the same order (see _extra_entry).
    # Only those two pages fetch it; the gallery, census and 404 never pay for it.
    extra_url = f"/planets.extra.{build_id}.json"
    (out / f"planets.extra.{build_id}.json").write_text(
        json.dumps([_extra_entry(r) for r in records], separators=(",", ":"))
    )
    # Boot slice: the head of the default gallery view (unfiltered, name sort), inlined into
    # index.html so the first screens of cards paint before the multi-MB index downloads.
    # The sort rule (lowercase, then exact, plain code-point compare) is mirrored exactly by
    # the gallery's name sort in app.js — keep the two in sync or first paint will reshuffle.
    boot_planets = sorted(index_entries, key=lambda e: (e["name"].lower(), e["name"]))[:150]
    gallery_html = env.get_template("gallery.html").render(
        stats=_stats(records),
        index_url=f"/planets.index.{build_id}.json",
        boot_planets=boot_planets,
        n_modelled=len(records),
        known_total=KNOWN_TOTAL_APPROX,
        build_id=build_id,
    )
    (out / "index.html").write_text(gallery_html)
    (out / "how.html").write_text(env.get_template("how.html").render(build_id=build_id))
    # Compare page: consumes the same fetched index plus the extras (star + orbit numbers);
    # deep-linkable via ?a=&b=.
    (out / "compare.html").write_text(
        env.get_template("compare.html").render(
            index_url=f"/planets.index.{build_id}.json",
            extra_url=extra_url,
            build_id=build_id,
        )
    )
    # Glossary: every jargon term on the site, in plain English. Deliberately unlinked from
    # the nav — it is reachable at /glossary, and by hovering any marked term anywhere.
    (out / "glossary.html").write_text(
        env.get_template("glossary.html").render(
            categories=glossary["categories"], terms=glossary["terms"], build_id=build_id
        )
    )
    # Colour census: the whole catalog as one dataset (same fetched index).
    (out / "census.html").write_text(
        env.get_template("census.html").render(
            index_url=f"/planets.index.{build_id}.json", build_id=build_id
        )
    )
    # 404: served by nginx's `error_page 404 /404.html`. Needs the index URL because its
    # RANDOM WORLD key rolls over the same catalog, plus two real instrument feeds: the
    # three nearest catalog worlds (the radar chart — "you're lost, here's what's close")
    # and one real reflected-light spectrum for the signal trace.
    (out / "404.html").write_text(
        env.get_template("404.html").render(
            index_url=f"/planets.index.{build_id}.json",
            n_modelled=len(records),
            build_id=build_id,
            **_cockpit_instruments(records),
        )
    )
    # "Your sky tonight": every host star above the visitor's horizon (same fetched index,
    # plus the extras — the RA/Dec/magnitude it plots live there).
    (out / "sky.html").write_text(
        env.get_template("sky.html").render(
            index_url=f"/planets.index.{build_id}.json",
            extra_url=extra_url,
            build_id=build_id,
        )
    )
    # Guided tours: curated walks, resolved against THIS catalog (see pipeline/tours.py).
    tours = resolve_tours(records)
    _tour_pages(env, tours, out, build_id, len(records))
    tour_membership: dict[str, list[dict]] = {}
    for tour in tours:
        for stop in tour.stops:
            tour_membership.setdefault(stop.planet.id, []).append(
                {"id": tour.id, "title": tour.title}
            )

    page_tpl = env.get_template("planet.html")
    peek_tpl = env.get_template("fragments/peek.html")
    # Every host with a known position becomes a faint dot on every planet's sky chart. That
    # field is identical on all ~5.8k pages — only the crosshair moves — so it is written once
    # per geometry and referenced. Inlined, it was 93% of a planet page and ~4.4 GB of dist.
    # Build-stamped like the index, so it caches for a year and never goes stale.
    sky_points = [(r.sky.ra_deg, r.sky.dec_deg) for r in records if r.sky]
    sky_field_urls = None
    if sky_points:
        for name, compact in ((f"sky-field.{build_id}.svg", False),
                              (f"sky-field-c.{build_id}.svg", True)):
            (out / name).write_text(sky_field_svg(sky_points, compact=compact))
        sky_field_urls = (f"/sky-field.{build_id}.svg", f"/sky-field-c.{build_id}.svg")
    # Stream one planet at a time: each context carries two rendered SVG spectra, so
    # materialising all of them first is ~1 GB of strings at 6k planets — enough to push a
    # small VPS into swap during deploy. Peak memory is now one context, not N.
    for rec in records:
        ctx = _planet_ctx(rec, fiction, sky_points, tour_membership, sky_field_urls)
        pid = rec.id
        (out / "planet" / f"{pid}.html").write_text(page_tpl.render(ctx=ctx, build_id=build_id))
        (out / "fragments" / "peek" / f"{pid}.html").write_text(peek_tpl.render(ctx=ctx))

    shutil.copytree(_STATIC, out / "static")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(prog="site.build")
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--planets", type=Path, default=_DEFAULT_JSON)
    args = parser.parse_args()
    out = build(args.planets, args.out)
    n = len(list((out / "planet").glob("*.html")))
    print(f"Built site -> {out}  ({n} planet pages)")


if __name__ == "__main__":
    main()
