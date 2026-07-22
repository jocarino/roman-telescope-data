"""Ingest the Cahoy et al. 2010 albedo grid into `data/cahoy_grid/`.

One-time data-prep. Reads the geometric-albedo (0° phase) files from the extracted Cahoy
distribution, converts wavelength µm -> nm, and writes CSVs + a manifest.json in the format
`CahoyProvider` reads. Run after downloading the grid:

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
_NAME_RE = re.compile(r"(Jupiter|Neptune)_(\d+)x_([\d.]+)AU_0deg\.dat$")


def ingest(raw_dir: Path, out_dir: Path = CAHOY_GRID_DIR) -> int:
    files = sorted(raw_dir.rglob("*_0deg.dat"))
    if not files:
        raise SystemExit(f"No *_0deg.dat geometric-albedo files under {raw_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    points = []
    for f in files:
        m = _NAME_RE.search(f.name)
        if not m:
            continue
        planet, met_str, dist_str = m.group(1), m.group(2), m.group(3)
        metallicity = _METALLICITY[met_str]
        dist_au = float(dist_str)

        arr = np.loadtxt(f)  # whitespace-delimited: µm, albedo
        wl_nm = arr[:, 0] * 1000.0  # µm -> nm
        albedo = arr[:, 1]
        csv_name = f"{planet}_{met_str}x_{dist_str}AU.csv"
        np.savetxt(out_dir / csv_name, np.column_stack([wl_nm, albedo]), delimiter=",",
                   fmt="%.6f")
        points.append({
            "dist_au": dist_au,
            "metallicity": metallicity,
            "cloud": "cahoy",
            "planet": planet,
            "file": csv_name,
        })

    (out_dir / "manifest.json").write_text(json.dumps({"points": points}, indent=2))
    return len(points)


def main() -> None:
    ap = argparse.ArgumentParser(prog="pipeline.spectrum.cahoy_ingest")
    ap.add_argument("raw_dir", type=Path, help="Extracted Cahoy distribution directory")
    ap.add_argument("--out", type=Path, default=CAHOY_GRID_DIR)
    args = ap.parse_args()
    n = ingest(args.raw_dir, args.out)
    print(f"Ingested {n} Cahoy geometric-albedo grid points -> {args.out}")


if __name__ == "__main__":
    main()
