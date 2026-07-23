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

from pipeline.colour.family import colour_family
from pipeline.models import PlanetRecord, PlanetsFile
from pipeline.palette.export import ase_bytes
from web.svg import spectrum_svg

_HERE = Path(__file__).parent
_TEMPLATES = _HERE / "templates"
_STATIC = _HERE / "static"
_DEFAULT_JSON = Path("data/planets.json")


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _planet_ctx(rec: PlanetRecord) -> dict:
    view = rec.instrument_views[0]
    svg = spectrum_svg(
        true_albedo=rec.spectrum.values,
        roman_recon=view.reconstruction.values,
        extrap_below_nm=view.reconstruction.extrapolated_below_nm,
    )
    return {"record": rec, "spectrum_svg": svg}


def _index_entry(rec: PlanetRecord) -> dict:
    view = rec.instrument_views[0]
    return {
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
        # For the card planet renders:
        "palette": [s.hex for s in rec.true_colour.palette],
        "radius": rec.params.radius_r_earth,
        "cloud": rec.params.assumed_cloud_state,
    }


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
    (out / "palettes").mkdir(parents=True)

    contexts = [_planet_ctx(r) for r in records]
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

    gallery_html = env.get_template("gallery.html").render(
        planets=contexts,
        stats=_stats(records),
        index_json=json.dumps([_index_entry(r) for r in records]),
        build_id=build_id,
    )
    (out / "index.html").write_text(gallery_html)

    page_tpl = env.get_template("planet.html")
    frag_tpl = env.get_template("fragments/planet_detail.html")
    for ctx in contexts:
        pid = ctx["record"].id
        (out / "planet" / f"{pid}.html").write_text(page_tpl.render(ctx=ctx, build_id=build_id))
        (out / "fragments" / "planet" / f"{pid}.html").write_text(frag_tpl.render(ctx=ctx))

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
