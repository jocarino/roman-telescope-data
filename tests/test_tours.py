"""Guided tours: the selection rules, the generated captions, and the curated JSON itself.

The point of these tests is that a tour cannot quietly start lying — the pages make factual
claims ("the darkest worlds", "planets of dead stars") that are only true if the rule really
sorts on what the copy says it does.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.models import PlanetRecord
from pipeline.tours import (
    _RULES,
    colour_reason,
    load_definitions,
    resolve,
)

TOURS_JSON = Path("data/tours.json")
PLANETS_JSON = Path("data/planets.json")


def make_record(
    pid: str,
    *,
    host: str = "Star A",
    teff: float = 5500.0,
    stype: str | None = "G2 V",
    hex_: str = "#8899aa",
    xyz: tuple[float, float, float] = (0.4, 0.42, 0.5),
    lum: float = 0.3,
    oog: bool = False,
    cloud: str = "temperate / warm, partial cloud + haze",
    temp: float | None = 400.0,
    radius: float | None = 5.0,
    dist_pc: float | None = 20.0,
    roman_hex: str = "#889aab",
    roman_de: float | None = 8.0,
) -> PlanetRecord:
    colour = {
        "method": "full-spectrum",
        "hex": hex_,
        "srgb": (136, 153, 170),
        "xyz": xyz,
        "luminance_y": lum,
        "out_of_gamut": oog,
        "confidence": "high",
        "palette": [{"hex": hex_, "role": "base"}],
    }
    return PlanetRecord.model_validate(
        {
            "id": pid,
            "name": pid.replace("-", " ").title(),
            "host_star": {"name": host, "teff_k": teff, "spectral_type": stype},
            "params": {
                "equilibrium_temp_k": temp,
                "radius_r_earth": radius,
                "distance_pc": dist_pc,
                "assumed_cloud_state": cloud,
                "assumed_phase_angle_deg": 20.0,
            },
            "discovery": {"method": "Transit"},
            "is_light_isolable": True,
            "provenance": "model",
            "true_colour": colour,
            "instrument_views": [
                {
                    "instrument_id": "roman-cgi",
                    "band_samples": {
                        "instrument_id": "roman-cgi",
                        "source": "simulated",
                        "samples": [],
                    },
                    "reconstruction": {
                        "grid": "cie-vis-380-780-5",
                        "values": [],
                        "interpolant": "pchip",
                        "extrapolated_below_nm": 575.0,
                        "extrapolated_above_nm": 835.0,
                    },
                    "colour": {**colour, "hex": roman_hex, "method": "band-reconstruction"},
                    "reconstruction_error": (
                        {"delta_e2000": roman_de, "note": "test"} if roman_de is not None else None
                    ),
                }
            ],
            "meta": {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "pipeline_version": "0.1.0",
                "schema_version": 4,
            },
        }
    )


# ── the curated file ──────────────────────────────────────────────────────────────────────


def test_definitions_are_well_formed() -> None:
    defs = load_definitions(TOURS_JSON)
    assert defs, "no tours defined"
    ids = [d["id"] for d in defs]
    assert len(ids) == len(set(ids)), "tour ids must be unique (they are URLs)"
    for d in defs:
        for field in ("id", "title", "kicker", "intro", "basis"):
            assert d.get(field), f"{d.get('id')}: missing {field}"
        # Exactly one source of stops: a rule the resolver knows, or an explicit list.
        if "select" in d:
            assert d["select"]["rule"] in _RULES, f"{d['id']}: unknown rule"
            assert "stops" not in d, f"{d['id']}: rule tours must not hard-code stops"
        else:
            assert d.get("stops"), f"{d['id']}: neither a select rule nor stops"


# ── selection rules ───────────────────────────────────────────────────────────────────────


def test_dimmest_picks_the_least_reflective_first() -> None:
    recs = [
        make_record("bright", lum=0.6, host="H1"),
        make_record("dark", lum=0.04, host="H2"),
        make_record("middling", lum=0.3, host="H3"),
    ]
    stops = _RULES["dimmest"](recs, limit=3)
    assert [s.planet.id for s in stops] == ["dark", "middling", "bright"]
    assert "4.0 %" in stops[0].caption


def test_rules_keep_one_planet_per_host_system() -> None:
    """Four planets of one star would otherwise fill a ten-stop tour with one system."""
    recs = [make_record(f"a-{i}", host="Same Star", lum=0.05 + i / 100) for i in range(4)]
    recs.append(make_record("other", host="Other Star", lum=0.2))
    stops = _RULES["dimmest"](recs, limit=10)
    assert [s.planet.id for s in stops] == ["a-0", "other"]


def test_nearest_excludes_the_solar_system_and_orders_by_distance() -> None:
    recs = [
        make_record("jupiter", host="Sun", dist_pc=0.000025),
        make_record("far", host="Far Star", dist_pc=40.0),
        make_record("near", host="Near Star", dist_pc=1.3),
    ]
    stops = _RULES["nearest"](recs, limit=5)
    assert [s.planet.id for s in stops] == ["near", "far"]
    assert "closest known planet" in stops[0].caption.lower()
    assert "4.2 light-years" in stops[0].caption  # 1.3 pc


def test_roman_gap_ranks_by_reconstruction_error_and_shows_both_colours() -> None:
    recs = [
        make_record("small-gap", host="H1", roman_de=2.0),
        make_record("big-gap", host="H2", hex_="#3fb0ff", roman_hex="#ffa991", roman_de=46.0),
        make_record("no-view", host="H3", roman_de=None),
    ]
    stops = _RULES["roman-gap"](recs, limit=5)
    assert [s.planet.id for s in stops] == ["big-gap", "small-gap"]
    assert "#3fb0ff" in stops[0].caption and "#ffa991" in stops[0].caption


def test_remnant_hosts_finds_white_dwarfs_only() -> None:
    recs = [
        make_record("wd-a", host="WD 1856+534", teff=4710.0, stype="DC"),
        make_record("wd-b", host="Some Star", teff=10393.0, stype="DQ"),
        make_record("normal", host="Kepler-1", teff=5500.0, stype="G2 V"),
        # A "D"-prefixed catalogue name is not a spectral type — must not be swept in.
        make_record("normal-2", host="DENIS-1", teff=3000.0, stype="M5 V"),
    ]
    stops = _RULES["remnant-hosts"](recs, limit=5)
    assert {s.planet.id for s in stops} == {"wd-a", "wd-b"}
    assert stops[0].planet.id == "wd-b", "hottest cinder first, as the page claims"
    assert "white dwarf" in stops[0].caption


def test_colour_outliers_skip_planets_that_look_like_one_already_picked() -> None:
    """Ten near-identical amber worlds are not ten strange colours."""
    far = (0.6, 0.3, 0.05)  # a long way from the median in Lab
    recs = [make_record(f"amber-{i}", host=f"H{i}", xyz=far) for i in range(5)]
    recs += [make_record(f"mid-{i}", host=f"M{i}", xyz=(0.4, 0.42, 0.5)) for i in range(5)]
    recs.append(make_record("teal", host="T", xyz=(0.25, 0.35, 0.45)))
    stops = _RULES["colour-outliers"](recs, limit=10, min_separation_de=9.0)
    ids = [s.planet.id for s in stops]
    assert len([i for i in ids if i.startswith("amber")]) == 1, ids


def test_blue_two_ways_alternates_cold_and_hot() -> None:
    cold = [
        make_record(f"cold-{i}", host=f"C{i}", cloud="cold, thick clouds + methane", temp=200.0)
        for i in range(3)
    ]
    hot = [
        make_record(f"hot-{i}", host=f"H{i}", cloud="ultra-hot, cloud-free, very dark", temp=2400.0)
        for i in range(3)
    ]
    stops = _RULES["blue-two-ways"](cold + hot, limit=4)
    kinds = ["cold" if s.planet.id.startswith("cold") else "hot" for s in stops]
    assert kinds == ["cold", "hot", "cold", "hot"]


# ── generated prose ───────────────────────────────────────────────────────────────────────


def test_colour_reason_names_a_brown_dwarf_host_correctly() -> None:
    """Below ~2,400 K the host fuses nothing: calling it a red dwarf would be wrong."""
    brown = colour_reason(make_record("x", teff=575.0), brief=True)
    red = colour_reason(make_record("y", teff=2900.0), brief=True)
    assert "brown dwarf" in brown and "red-dwarf" not in brown
    assert "red-dwarf" in red and "brown dwarf" not in red
    # Above the star-dominated regime the host is a footnote, not the lead.
    sunlike = colour_reason(make_record("z", teff=5500.0))
    assert "dwarf" not in sunlike


def test_colour_reason_leads_with_the_star_when_the_star_dominates() -> None:
    """A methane world around a very red sun looks amber; leading with "leaving blue-green"
    would contradict its own swatch."""
    reason = colour_reason(make_record("x", teff=2900.0, cloud="cold, thick clouds + methane"))
    assert reason.index("red and infrared") < reason.index("methane")


def test_out_of_gamut_swatches_are_flagged() -> None:
    stops = _RULES["dimmest"]([make_record("clipped", oog=True, lum=0.05)], limit=1)
    assert stops[0].caveat and "screen" in stops[0].caveat
    plain = _RULES["dimmest"]([make_record("fine", oog=False, lum=0.05)], limit=1)
    assert plain[0].caveat is None


# ── resolution ────────────────────────────────────────────────────────────────────────────


def test_resolve_drops_tours_that_cannot_be_filled(tmp_path: Path) -> None:
    doc = {
        "tours": [
            {
                "id": "thin",
                "title": "T",
                "kicker": "k",
                "intro": "i",
                "basis": "b",
                "select": {"rule": "remnant-hosts"},
            }
        ]
    }
    path = tmp_path / "tours.json"
    path.write_text(json.dumps(doc))
    # One white dwarf in the catalogue is a link, not a tour.
    assert resolve([make_record("wd", host="WD 1", stype="DA")], path) == []


def test_resolve_skips_explicit_ids_missing_from_this_data_release(tmp_path: Path) -> None:
    doc = {
        "tours": [
            {
                "id": "curated",
                "title": "T",
                "kicker": "k",
                "intro": "i",
                "basis": "b",
                "stops": [{"id": "here"}, {"id": "gone"}, {"id": "also-here", "note": "n"}],
            }
        ]
    }
    path = tmp_path / "tours.json"
    path.write_text(json.dumps(doc))
    recs = [make_record("here"), make_record("also-here", host="H2")]
    tours = resolve(recs, path)
    assert [s.planet.id for s in tours[0].stops] == ["here", "also-here"]
    assert tours[0].stops[1].note == "n"


def test_unknown_rule_is_a_build_error(tmp_path: Path) -> None:
    path = tmp_path / "tours.json"
    path.write_text(
        json.dumps(
            {
                "tours": [
                    {
                        "id": "x",
                        "title": "T",
                        "kicker": "k",
                        "intro": "i",
                        "basis": "b",
                        "select": {"rule": "does-not-exist"},
                    }
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="unknown select rule"):
        resolve([make_record("a")], path)


@pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")
def test_every_tour_fills_against_the_real_catalogue() -> None:
    """The end-to-end check the site depends on: with the committed tours.json and the current
    planets.json, every tour resolves to a usable walk with a caption on every stop."""
    from pipeline.models import PlanetsFile

    doc = PlanetsFile.model_validate_json(PLANETS_JSON.read_text())
    tours = resolve(doc.planets, TOURS_JSON)
    assert len(tours) == len(load_definitions(TOURS_JSON))
    for tour in tours:
        assert len(tour.stops) >= 2, tour.id
        ids = [s.planet.id for s in tour.stops]
        assert len(ids) == len(set(ids)), f"{tour.id}: a planet appears twice"
        for stop in tour.stops:
            assert stop.caption.strip().endswith("."), f"{tour.id}/{stop.planet.id}"
            assert stop.metric
