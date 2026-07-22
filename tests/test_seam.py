"""The swap seam: dropping a measured file flips a planet's Roman view from simulated to
measured with no code change — provenance becomes measured-cgi, source becomes measured.
"""

from __future__ import annotations

import json

from pipeline import emit
from pipeline.config import ROMAN_CGI
from pipeline.demo_planets import demo_planets
from pipeline.emit.build import build_record
from pipeline.fetch.targets import load_measured_samples


def test_simulated_by_default():
    rec = build_record(demo_planets()[0], [ROMAN_CGI], "2026-07-22T00:00:00+00:00")
    assert rec.provenance == "model"
    assert rec.instrument_views[0].band_samples.source == "simulated"


def test_measured_file_flips_provenance(tmp_path, monkeypatch):
    pin = demo_planets()[0]
    measured = {
        "epoch": "2027-03-14",
        "samples": [
            {"band_id": "cgi-575", "center_nm": 575.0, "value": 0.31, "uncertainty": 0.04},
            {"band_id": "cgi-660", "center_nm": 660.0, "value": 0.28, "uncertainty": 0.05},
            {"band_id": "cgi-730", "center_nm": 730.0, "value": 0.19, "uncertainty": 0.05},
            {"band_id": "cgi-835", "center_nm": 835.0, "value": 0.15, "uncertainty": 0.06},
        ],
    }
    (tmp_path / f"{pin.id}.{ROMAN_CGI.id}.json").write_text(json.dumps(measured))

    # Point the seam's loader at the temp measured directory.
    monkeypatch.setattr(
        emit.build,
        "load_measured_samples",
        lambda planet_id, instrument: load_measured_samples(planet_id, instrument, tmp_path),
    )

    rec = build_record(pin, [ROMAN_CGI], "2027-03-15T00:00:00+00:00")
    view = rec.instrument_views[0]
    assert view.band_samples.source == "measured"
    assert view.band_samples.epoch == "2027-03-14"
    assert rec.provenance == "measured-cgi"
    # Downstream products still present and unchanged in shape.
    assert view.colour.hex.startswith("#")
    assert view.reconstruction_error is not None
