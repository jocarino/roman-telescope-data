"""The measured branch of the swap seam.

Post-launch, real Roman CGI photometry for a tech-demo target arrives as a small JSON file
dropped into `data/cgi_measured/{planet_id}.{instrument_id}.json`. When present it REPLACES
the simulated band samples with zero change to anything downstream — same shape, same
`reconstruct -> cie -> palette`. At v1 the directory is empty, so this always returns None
and the pipeline uses simulated samples.

Measured file format:
    {
      "epoch": "2027-03-14",
      "samples": [{"band_id": "cgi-575", "center_nm": 575.0, "value": 0.31,
                   "uncertainty": 0.04}, ...]
    }

Planet identity / matching (v1 assumption, documented):
    The join between an incoming Roman measurement and one of our planets is by SLUG:
    slug(NASA `pl_name`) == the measured file's basename. This works because we control both
    sides and the CGI tech-demo targets are well-known RV planets with stable canonical names.
    It does NOT yet handle name aliases (e.g. "47 UMa c" == "HD 95128 c"). When real CGI data
    products are ingested, add a `resolve_planet_id()` step here that maps an incoming name to
    our canonical slug via the Archive alias table, or matches on host star + planet letter,
    or on host-star coordinates (most robust). Left as a documented assumption for now.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.bands.integrate import BandSample, BandSampleSet
from pipeline.config import Instrument

MEASURED_DIR = Path("data/cgi_measured")


def load_measured_samples(
    planet_id: str, instrument: Instrument, measured_dir: Path = MEASURED_DIR
) -> BandSampleSet | None:
    path = measured_dir / f"{planet_id}.{instrument.id}.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    samples = tuple(
        BandSample(
            band_id=s["band_id"],
            center_nm=float(s["center_nm"]),
            value=float(s["value"]),
            uncertainty=s.get("uncertainty"),
        )
        for s in payload["samples"]
    )
    return BandSampleSet(
        instrument_id=instrument.id,
        source="measured",
        epoch=payload.get("epoch"),
        samples=samples,
    )
