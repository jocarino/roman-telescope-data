"""Pipeline CLI.

Milestone 1:
    uv run python -m pipeline build            # build demo planets, print colours, write JSON
    uv run python -m pipeline build --limit 1  # just the first
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pipeline.catalog import catalog_bulk, catalog_planets
from pipeline.config import INSTRUMENTS, ROMAN_CGI
from pipeline.demo_planets import demo_planets
from pipeline.emit.cache import cached_build_record
from pipeline.emit.writer import DEFAULT_OUT, write_planets
from pipeline.solar_system import solar_system_planets
from pipeline.system import attach_systems


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def cmd_build(args: argparse.Namespace) -> None:
    generated_at = _now_iso()
    instruments = [ROMAN_CGI] if args.targets_only is False else list(INSTRUMENTS.values())
    if args.source == "demo":
        inputs = demo_planets()
    elif args.planet:
        # The one-planet fast path. A dated release is always behind the Archive, so the
        # commonest newsjackable story ("new planet discovered") is the one we cannot answer
        # from data/planets.json. This pulls that single row live and builds it in seconds.
        # It writes to --out, never over the release file, so nothing else is disturbed.
        inputs = catalog_planets(list(args.planet), use_cache=not args.no_cache)
        if not inputs:
            print(
                f"\nNo colour for {', '.join(args.planet)}: the completeness gate rejected it "
                f"(reason above).\nThat is still a post — 'we can't compute a colour for this "
                f"one yet, and here is exactly\nwhich number is missing' beats a guess."
            )
            return
    elif args.bulk is not None:
        inputs = solar_system_planets() + catalog_bulk(args.bulk, use_cache=not args.no_cache)
    else:
        inputs = solar_system_planets() + catalog_planets(use_cache=not args.no_cache)
    if args.limit is not None:
        inputs = inputs[: args.limit]

    records = []
    hits = 0
    for pin in inputs:
        rec, was_hit = cached_build_record(
            pin, instruments, generated_at, use_cache=not args.no_cache
        )
        hits += was_hit
        records.append(rec)
        tc = rec.true_colour
        roman = rec.instrument_views[0]
        print(f"\n{rec.name}  [{rec.provenance}]")
        print(f"  true colour : {tc.hex}  lumY={tc.luminance_y:.3f}  oog={tc.out_of_gamut}")
        print(
            f"  roman view  : {roman.colour.hex}  "
            f"dE2000={roman.reconstruction_error.delta_e2000:.1f}  "
            f"(source={roman.band_samples.source})"
        )
        print(f"  palette     : {' '.join(s.hex for s in tc.palette)}")

    # Batch pass: link planets that share a host star (needs the whole set to group).
    attach_systems(records)

    out = write_planets(records, generated_at, args.out)
    n = len(records)
    print(f"\nWrote {n} planet(s) -> {out}  ({hits} from cache, {n - hits} rebuilt)")


def cmd_drift(args: argparse.Namespace) -> None:
    """Report whether the Archive has moved since the last release — or write the manifest that
    becomes the next baseline. Always exits 0 on success: the answer is the output, not the exit
    code, so a "yes it changed" run is not a failed workflow step."""
    from pipeline.drift import build_manifest, compare, diff_catalogues, load_baseline

    if args.diff_against is not None:
        d = diff_catalogues(args.diff_against, args.planets)
        print(json.dumps({**asdict(d), "summary": d.summary()}, indent=2, sort_keys=True))
        print(f"\n{d.summary()}")
        out = os.environ.get("GITHUB_OUTPUT")
        if args.github_output and out:
            with open(out, "a") as fh:
                fh.write(f"summary={d.summary()}\n")
                fh.write(f"recoloured={len(d.recoloured)}\n")
                fh.write(f"roman_changed={len(d.roman_changed)}\n")
        return

    if args.emit_manifest is not None:
        manifest = build_manifest(args.planets)
        args.emit_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.emit_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        arch = manifest["archive"]
        print(
            f"Wrote {args.emit_manifest}: {manifest['catalogue']['planets']} planets built, "
            f"{arch['fingerprint']['n']} in the gated Archive set (gate v{arch['gate_version']})"
        )
        return

    report = compare(load_baseline(args.baseline))
    print(report.to_json())
    print(f"\n{report.headline()} — {report.reason}")
    if report.added:
        shown = report.added[:20]
        print(f"  new: {', '.join(shown)}" + (" …" if len(report.added) > len(shown) else ""))
    if report.removed:
        print(f"  gone: {', '.join(report.removed[:20])}")

    out = os.environ.get("GITHUB_OUTPUT")
    if args.github_output and out:
        with open(out, "a") as fh:
            fh.write(f"drift={'true' if report.drift else 'false'}\n")
            fh.write(f"headline={report.headline()}\n")
            fh.write(f"added={len(report.added)}\nremoved={len(report.removed)}\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(required=True)

    p_build = sub.add_parser("build", help="Generate planet colours and write planets.json")
    p_build.add_argument(
        "--source",
        choices=("catalog", "demo"),
        default="catalog",
        help="catalog = real Exoplanet Archive planets (default); demo = synthetic archetypes",
    )
    p_build.add_argument(
        "--bulk",
        type=int,
        default=None,
        metavar="N",
        help="Scaled catalog: curated planets + nearest N well-characterised Archive planets",
    )
    p_build.add_argument(
        "--planet",
        action="append",
        default=None,
        metavar="NAME",
        help="One-planet fast path: build just this Archive pl_name (repeatable). Use with "
        "--out so the release planets.json is left alone. This is the newsjack path — a "
        "planet in the news that postdates the release can be coloured in ~5 minutes.",
    )
    p_build.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        metavar="PATH",
        help=f"Where to write the JSON (default: {DEFAULT_OUT})",
    )
    p_build.add_argument("--limit", type=int, default=None, help="Only build the first N planets")
    p_build.add_argument("--no-cache", action="store_true", help="Bypass the TAP disk cache")
    p_build.add_argument(
        "--targets-only", action="store_true", help="(reserved) restrict to CGI targets"
    )
    p_build.set_defaults(func=cmd_build, targets_only=False)

    p_drift = sub.add_parser(
        "drift",
        help="Ask the Archive whether anything changed since the last data release",
    )
    p_drift.add_argument(
        "--baseline",
        type=Path,
        default=None,
        metavar="PATH",
        help="Manifest to compare against. Omit to fetch manifest.json from the latest release.",
    )
    p_drift.add_argument(
        "--emit-manifest",
        type=Path,
        default=None,
        metavar="PATH",
        help="Instead of comparing, write the manifest for the built data/planets.json",
    )
    p_drift.add_argument(
        "--planets",
        type=Path,
        default=Path("data/planets.json"),
        help="Path to planets.json when emitting a manifest (default: data/planets.json)",
    )
    p_drift.add_argument(
        "--diff-against",
        type=Path,
        default=None,
        metavar="PATH",
        help="Compare a previous planets.json against --planets and report what actually moved",
    )
    p_drift.add_argument(
        "--github-output",
        action="store_true",
        help="Also append drift=/headline= to $GITHUB_OUTPUT for a workflow step",
    )
    p_drift.set_defaults(func=cmd_drift)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
