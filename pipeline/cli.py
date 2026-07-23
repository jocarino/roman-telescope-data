"""Pipeline CLI.

Milestone 1:
    uv run python -m pipeline build            # build demo planets, print colours, write JSON
    uv run python -m pipeline build --limit 1  # just the first
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from pipeline.catalog import catalog_planets
from pipeline.config import INSTRUMENTS, ROMAN_CGI
from pipeline.demo_planets import demo_planets
from pipeline.emit.build import build_record
from pipeline.emit.writer import write_planets
from pipeline.system import attach_systems


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def cmd_build(args: argparse.Namespace) -> None:
    generated_at = _now_iso()
    instruments = [ROMAN_CGI] if args.targets_only is False else list(INSTRUMENTS.values())
    if args.source == "demo":
        inputs = demo_planets()
    else:
        inputs = catalog_planets(use_cache=not args.no_cache)
    if args.limit is not None:
        inputs = inputs[: args.limit]

    records = []
    for pin in inputs:
        rec = build_record(pin, instruments, generated_at)
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

    out = write_planets(records, generated_at)
    print(f"\nWrote {len(records)} planet(s) -> {out}")


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
    p_build.add_argument("--limit", type=int, default=None, help="Only build the first N planets")
    p_build.add_argument("--no-cache", action="store_true", help="Bypass the TAP disk cache")
    p_build.add_argument(
        "--targets-only", action="store_true", help="(reserved) restrict to CGI targets"
    )
    p_build.set_defaults(func=cmd_build, targets_only=False)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
