"""The build-time model-space payload: its shape, its anchoring, and its contract with the JS.

Two things are easy to break here and expensive to notice:

  * the payload is inlined into ~5.8k pages, so its shape is a size decision as much as an API
    one — the stops are parallel arrays and the what-if wording lives in the JS precisely
    because repeating either per page cost real megabytes;
  * that second choice splits one fact across two languages. `pipeline.modelspace` owns the
    variant ids and `web/static/modelspace.js` owns their labels, so a variant renamed on one
    side and not the other would ship a chip labelled with a raw id. The last test pins them
    together.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pipeline.colour.cie import reflected_flux_to_colour
from pipeline.config import GRID_ID, GRID_NM
from pipeline.illuminant.blackbody import SUN
from pipeline.models import (
    ColourResultModel,
    Discovery,
    HostStar,
    PlanetParams,
    PlanetRecord,
    RecordMeta,
    SpectralCurve,
)
from pipeline.spectrum.synthetic import CLOUDY_JUPITER
from web.modelspace import modelspace_ctx

_MODELSPACE_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "modelspace.js"


def _record(**overrides) -> PlanetRecord:
    """A minimal but valid record: a cold jovian around a Sun-like star."""
    albedo = CLOUDY_JUPITER.geometric_albedo(GRID_NM)
    star = SUN.spectrum(GRID_NM)
    colour = reflected_flux_to_colour(
        albedo * star, method="full-spectrum", illuminant_flux=star, confidence="high"
    )
    params = dict(
        equilibrium_temp_k=110.0,
        radius_r_earth=11.2,
        mass_m_earth=318.0,
        semi_major_axis_au=5.2,
        eccentricity=0.05,
        assumed_cloud_state="cold, thick clouds + methane",
        assumed_metallicity=3.0,
        assumed_phase_angle_deg=0.0,
    )
    params.update(overrides.pop("params", {}))
    return PlanetRecord(
        id="test-b",
        name="Test b",
        host_star=HostStar(name="Test", teff_k=5772.0),
        params=PlanetParams(**params),
        discovery=Discovery(method="transit"),
        is_light_isolable=True,
        provenance=overrides.pop("provenance", "model"),
        spectrum=SpectralCurve(grid=GRID_ID, values=[float(a) for a in albedo]),
        true_colour=ColourResultModel(
            method="full-spectrum",
            hex=colour.hex,
            srgb=colour.srgb,
            xyz=colour.xyz,
            luminance_y=colour.luminance_y,
            out_of_gamut=colour.out_of_gamut,
            confidence="high",
            palette=[],
        ),
        meta=RecordMeta(generated_at="now", pipeline_version="0", schema_version=5),
        **overrides,
    )


def test_payload_stops_are_parallel_arrays_of_equal_length():
    ctx = modelspace_ctx(_record())
    stops = ctx["stops"]
    lengths = {k: len(v) for k, v in stops.items()}
    assert set(stops) == {"r", "au", "t", "h", "l"}
    assert len(set(lengths.values())) == 1, lengths
    assert 0 <= ctx["home"] < lengths["r"]


def test_home_stop_is_the_records_own_colour():
    """The anchoring rule, at the layer the page actually reads."""
    rec = _record()
    ctx = modelspace_ctx(rec)
    assert ctx["stops"]["h"][ctx["home"]] == rec.true_colour.hex
    assert ctx["stops"]["r"][ctx["home"]] == 1.0
    assert ctx["planetHex"] == rec.true_colour.hex


def test_records_without_a_spectrum_or_temperature_get_no_panel():
    """A pre-v1 release, or a planet the Archive has no temperature for, must render the page
    without the panel rather than with an empty or fabricated one."""
    rec = _record()
    rec.spectrum = None
    assert modelspace_ctx(rec) is None

    rec2 = _record(params={"equilibrium_temp_k": None})
    assert modelspace_ctx(rec2) is None


def test_cahoy_marks_are_limited_to_the_sliders_own_span():
    """Marks outside the control would point at nothing, so they are dropped in Python rather
    than positioned off-screen in CSS."""
    ctx = modelspace_ctx(_record())
    lo, hi = ctx["stops"]["r"][0], ctx["stops"]["r"][-1]
    for point in ctx["cahoy"]:
        assert lo <= point["r"] <= hi


def test_measured_base_flag_marks_a_real_starting_spectrum():
    assert modelspace_ctx(_record())["measured_base"] is False
    assert modelspace_ctx(_record(provenance="measured-albedo"))["measured_base"] is True


def test_circular_orbit_has_no_colour_year_but_an_eccentric_one_does():
    assert modelspace_ctx(_record(params={"eccentricity": 0.01}))["year"] is None
    year = modelspace_ctx(_record(params={"eccentricity": 0.6}))["year"]
    assert year is not None
    assert len(year["pos"]) > 0
    assert year["q"] < year["Q"]


def test_variant_ids_match_the_labels_shipped_in_the_javascript():
    """pipeline/modelspace.py owns the ids; web/static/modelspace.js owns their wording. If
    they drift, the page renders a chip labelled with a raw id like "clouds-off"."""
    js = _MODELSPACE_JS.read_text()
    block = re.search(r"var WHATIF_TEXT = \{(.*?)\n  \};", js, re.S)
    assert block, "WHATIF_TEXT table not found in modelspace.js"
    js_ids = set(re.findall(r'"([a-z-]+)":\s*\{', block.group(1)))

    # Every id the pipeline can emit — a rocky world drops the metallicity pair, so take the
    # union over both cases rather than one planet's worth.
    emitted = {v["id"] for v in modelspace_ctx(_record())["whatif"]}
    rocky = _record(
        params={"radius_r_earth": 1.0, "mass_m_earth": 1.0, "assumed_metallicity": None}
    )
    emitted |= {v["id"] for v in modelspace_ctx(rocky)["whatif"]}

    assert emitted == js_ids


def test_whatif_payload_carries_numbers_only():
    """Labels and explanations are the same sentence on every page; shipping them per planet
    was ~800 bytes x 5.8k pages. If they come back, this fails."""
    for variant in modelspace_ctx(_record())["whatif"]:
        assert set(variant) == {"id", "h", "l", "de"}


@pytest.mark.parametrize("radius", [1.0, 3.9, 11.2])
def test_payload_is_json_serialisable_for_every_planet_class(radius: float):
    ctx = modelspace_ctx(_record(params={"radius_r_earth": radius}))
    json.dumps(ctx)  # the template inlines this; a stray numpy scalar would raise here
