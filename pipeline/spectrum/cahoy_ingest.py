"""Ingest the Cahoy et al. 2010 albedo grid into `data/cahoy_grid/`.

One-time data-prep. Reads ALL phase-angle files (0-180 deg in 10 deg steps) from the
extracted Cahoy distribution, converts wavelength µm -> nm, and writes CSVs + a
manifest.json in the format `CahoyProvider` reads. Run after downloading the grid:

    curl -L https://roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz -o cahoy.tgz
    tar xzf cahoy.tgz -C /tmp/cahoy
    uv run python -m pipeline.spectrum.cahoy_ingest /tmp/cahoy

Data credit: Cahoy, Marley & Fortney 2010, ApJ 724, 189.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

from pipeline.config import CAHOY_GRID_DIR

_METALLICITY = {"1": 1.0, "3": 3.0, "10": 10.0, "30": 30.0}
_NAME_RE = re.compile(r"(Jupiter|Neptune)_(\d+)x_([\d.]+)AU_(\d+)deg\.dat$")


# Recorded into every manifest we write. See data/cahoy_grid/README.md and LICENSE-DATA S5.
SOURCE = {
    "dataset": "Cahoy et al. (2010) albedo grid",
    "citation": (
        "Cahoy, K. L., Marley, M. S., & Fortney, J. J. (2010), ApJ 724, 189"
    ),
    "doi": "10.1088/0004-637X/724/1/189",
    "url": "https://roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz",
    "licence": "unresolved - upstream ships no licence file; see LICENSE-DATA section 5",
    "columns": ["wavelength_nm", "geometric_albedo"],
    "note": (
        "Not our data. Deriving colours from it is ordinary use; redistributing the grid "
        "files is a separate act we have not cleared. Exclude from any dataset deposit."
    ),
}


def ingest(raw_dir: Path, out_dir: Path = CAHOY_GRID_DIR) -> int:
    files = sorted(raw_dir.rglob("*deg.dat"))
    if not files:
        raise SystemExit(f"No *deg.dat albedo files under {raw_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    # One grid point per (planet, metallicity, distance), holding all its phase spectra.
    points: dict[tuple[str, float, float], dict] = {}
    n_files = 0
    for f in files:
        m = _NAME_RE.search(f.name)
        if not m:
            continue
        planet, met_str, dist_str, deg_str = m.group(1), m.group(2), m.group(3), m.group(4)
        metallicity = _METALLICITY[met_str]
        dist_au = float(dist_str)
        phase_deg = int(deg_str)

        arr = np.loadtxt(f)  # whitespace-delimited: µm, albedo
        wl_nm = arr[:, 0] * 1000.0  # µm -> nm
        albedo = arr[:, 1]
        csv_name = f"{planet}_{met_str}x_{dist_str}AU_{phase_deg:03d}deg.csv"
        np.savetxt(out_dir / csv_name, np.column_stack([wl_nm, albedo]), delimiter=",",
                   fmt="%.6f")
        key = (planet, metallicity, dist_au)
        points.setdefault(key, {
            "dist_au": dist_au,
            "metallicity": metallicity,
            "cloud": "cahoy",
            "planet": planet,
            "phase_files": {},
        })["phase_files"][str(phase_deg)] = csv_name
        n_files += 1

    ordered = sorted(points.values(), key=lambda p: (p["planet"], p["metallicity"], p["dist_au"]))
    # Stamp provenance into the manifest, not just the docs. A data directory that cannot say
    # whose work it holds is one filesystem copy away from being unattributable -- and this
    # grid is the one input whose redistribution terms we have NOT established, so it is the
    # last place to be vague about where it came from.
    (out_dir / "manifest.json").write_text(
        json.dumps({"source": SOURCE, "points": ordered}, indent=2)
    )
    return n_files


def main() -> None:
    ap = argparse.ArgumentParser(prog="pipeline.spectrum.cahoy_ingest")
    ap.add_argument("raw_dir", type=Path, help="Extracted Cahoy distribution directory")
    ap.add_argument("--out", type=Path, default=CAHOY_GRID_DIR)
    args = ap.parse_args()
    n = ingest(args.raw_dir, args.out)
    print(f"Ingested {n} Cahoy phase spectra -> {args.out}")


if __name__ == "__main__":
    main()
