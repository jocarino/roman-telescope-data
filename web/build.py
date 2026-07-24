"""Static-site generator: read data/planets.json, render the gallery, per-planet detail
pages, and htmx detail fragments into an output directory, then copy static assets.

    uv run python -m site.build --out dist

Pure static consumer — no colour maths here; both colours and palettes are precomputed in
planets.json. A regenerated planets.json (e.g. after real measured data lands) just changes
what renders; no template edits.
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
from pipeline.models import PlanetRecord, PlanetsFile
from pipeline.palette.export import ase_bytes
from web.svg import spectrum_svg

_HERE = Path(__file__).parent
_TEMPLATES = _HERE / "templates"
_STATIC = _HERE / "static"
_DEFAULT_JSON = Path("data/planets.json")
# Curated "seen in fiction" overlay: real systems that appear in named books/films/games.
# Hand-maintained, kept OUT of planets.json, joined here by planet name. Optional — a missing
# file just means no fiction sections render.
_FICTION_JSON = Path("data/fiction-references.json")


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


def _planet_ctx(rec: PlanetRecord, fiction: dict[str, dict] | None = None) -> dict:
    view = rec.instrument_views[0]
    args = dict(
        true_albedo=rec.spectrum.values,
        roman_recon=view.reconstruction.values,
        extrap_below_nm=view.reconstruction.extrapolated_below_nm,
    )
    # Two scope faces: wide for desktop, near-square for phones (CSS picks one).
    return {
        "record": rec,
        "spectrum_svg": spectrum_svg(**args),
        "spectrum_svg_compact": spectrum_svg(**args, compact=True),
        "fiction": (fiction or {}).get(rec.name),
    }


def _index_entry(rec: PlanetRecord, fiction: dict[str, dict] | None = None) -> dict:
    view = rec.instrument_views[0]
    entry = {
        "id": rec.id,
        "name": rec.name,
        "host": rec.host_star.name,
        "prov": rec.provenance,
        "temp": rec.params.equilibrium_temp_k,
        "dist": rec.params.distance_pc,
        "lum": rec.true_colour.luminance_y,
        "de": view.reconstruction_error.delta_e2000 if view.reconstruction_error else 0.0,
        "hex": rec.true_colour.hex,
        "family": colour_family(tuple(rec.true_colour.srgb)),
        "ptype": planet_type(
            rec.params.radius_r_earth, rec.params.mass_m_earth, rec.params.equilibrium_temp_k
        ),
        "disc": rec.discovery.method,
        # For the card planet renders:
        "palette": [s.hex for s in rec.true_colour.palette],
        "radius": rec.params.radius_r_earth,
        "cloud": rec.params.assumed_cloud_state,
        # Extra fields for the compare page (the colour-driving data + fun facts).
        "dist_ly": (
            round(rec.params.distance_pc * _LY_PER_PC, 1) if rec.params.distance_pc else None
        ),
        "starTeff": rec.host_star.teff_k,
        "starType": rec.host_star.spectral_type,
        "metal": rec.params.assumed_metallicity,
        "mass": rec.params.mass_m_earth,
        "sma": rec.params.semi_major_axis_au,
        "year": rec.discovery.year,
    }
    # Fiction flag: the system name if this planet appears in the curated overlay, else absent
    # (kept off the entry entirely so the 900+ non-fiction rows stay lean). Drives the gallery
    # "seen in fiction" filter.
    fic = (fiction or {}).get(rec.name)
    if fic:
        entry["fic"] = fic["system"]
    return entry


def _stats(records: list[PlanetRecord]) -> dict:
    des = [
        v.reconstruction_error.delta_e2000
        for r in records
        for v in r.instrument_views
        if v.reconstruction_error
    ]
    return {
        "total": len(records),
        "median_de": f"{statistics.median(des):.1f}" if des else "—",
        "cgi_targets": sum(1 for r in records if r.provenance == "simulated-cgi"),
        "microlensing": sum(1 for r in records if not r.is_light_isolable),
    }


def build(planets_json: Path = _DEFAULT_JSON, out: Path = Path("dist")) -> Path:
    doc = PlanetsFile.model_validate_json(planets_json.read_text())
    records = doc.planets
    env = _env()

    if out.exists():
        shutil.rmtree(out)
    (out / "planet").mkdir(parents=True)
    (out / "fragments" / "planet").mkdir(parents=True)
    (out / "fragments" / "peek").mkdir(parents=True)
    (out / "palettes").mkdir(parents=True)

    fiction = _load_fiction()
    # Cache-bust static assets on every build so browsers never serve a stale JS/CSS.
    build_id = str(int(time.time()))

    # Emit one .ase per planet (true-colour + Roman-view stops, named).
    for rec in records:
        entries: list[tuple[str, str]] = [
            (f"{rec.name} true {s.role}", s.hex) for s in rec.true_colour.palette
        ]
        entries += [
            (f"{rec.name} roman {s.role}", s.hex)
            for s in rec.instrument_views[0].colour.palette
        ]
        (out / "palettes" / f"{rec.id}.ase").write_bytes(ase_bytes(entries))

    # The gallery index is fetched at runtime (not inlined) so index.html stays tiny and the
    # grid scales to thousands of planets. Cache-busted by build_id.
    (out / f"planets.index.{build_id}.json").write_text(
        json.dumps([_index_entry(r, fiction) for r in records], separators=(",", ":"))
    )
    gallery_html = env.get_template("gallery.html").render(
        stats=_stats(records),
        index_url=f"/planets.index.{build_id}.json",
        n_modelled=len(records),
        known_total=KNOWN_TOTAL_APPROX,
        build_id=build_id,
    )
    (out / "index.html").write_text(gallery_html)
    (out / "how.html").write_text(env.get_template("how.html").render(build_id=build_id))
    # Compare page: consumes the same fetched index; deep-linkable via ?a=&b=.
    (out / "compare.html").write_text(
        env.get_template("compare.html").render(
            index_url=f"/planets.index.{build_id}.json", build_id=build_id
        )
    )
    # Colour census: the whole catalog as one dataset (same fetched index).
    (out / "census.html").write_text(
        env.get_template("census.html").render(
            index_url=f"/planets.index.{build_id}.json", build_id=build_id
        )
    )

    page_tpl = env.get_template("planet.html")
    frag_tpl = env.get_template("fragments/planet_detail.html")
    peek_tpl = env.get_template("fragments/peek.html")
    # Stream one planet at a time: each context carries two rendered SVG spectra, so
    # materialising all of them first is ~1 GB of strings at 6k planets — enough to push a
    # small VPS into swap during deploy. Peak memory is now one context, not N.
    for rec in records:
        ctx = _planet_ctx(rec, fiction)
        pid = rec.id
        (out / "planet" / f"{pid}.html").write_text(page_tpl.render(ctx=ctx, build_id=build_id))
        (out / "fragments" / "planet" / f"{pid}.html").write_text(frag_tpl.render(ctx=ctx))
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
