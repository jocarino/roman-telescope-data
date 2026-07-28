"""The Roman target board: the curated shortlist, the join onto the catalogue, and the flip.

Two things these tests exist to stop:

* **A silently broken join.** The board's whole claim is "these named planets, with our
  predicted colours". The published target names do NOT all slug-match our ids (pi Men b is
  HD 39091 b here), so the join runs off explicit ids — and an id that stops resolving must
  show as an honest gap, never as a missing row.
* **A slot that will not fill.** The empty "measured" column is a promise that the day real
  photometry lands, it appears here. That promise is only kept if provenance `measured-cgi`
  really does flip the slot, so it is tested directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.models import PlanetRecord
from pipeline.roman_board import (
    SCALE_MAX_MAS,
    SCALE_MIN_MAS,
    load_document,
    resolve,
    scale_pos,
)

BOARD_JSON = Path("data/roman-targets.json")


def make_record(
    pid: str,
    *,
    name: str | None = None,
    host: str = "Star A",
    sma: float | None = 3.0,
    dist_pc: float | None = 15.0,
    hex_: str = "#8899aa",
    roman_hex: str = "#889aab",
    provenance: str = "model",
    band_source: str = "simulated",
    epoch: str | None = None,
) -> PlanetRecord:
    colour = {
        "method": "full-spectrum",
        "hex": hex_,
        "srgb": (136, 153, 170),
        "xyz": (0.4, 0.42, 0.5),
        "luminance_y": 0.3,
        "out_of_gamut": False,
        "confidence": "high",
        "palette": [{"hex": hex_, "role": "mid"}],
    }
    return PlanetRecord.model_validate(
        {
            "id": pid,
            "name": name or pid.replace("-", " ").title(),
            "host_star": {"name": host, "teff_k": 5500.0, "spectral_type": "G2 V"},
            "params": {
                "equilibrium_temp_k": 300.0,
                "radius_r_earth": 11.0,
                "distance_pc": dist_pc,
                "semi_major_axis_au": sma,
                "assumed_cloud_state": "cold / methane",
                "assumed_phase_angle_deg": 90.0,
            },
            "discovery": {"method": "Radial Velocity"},
            "is_light_isolable": True,
            "provenance": provenance,
            "true_colour": colour,
            "instrument_views": [
                {
                    "instrument_id": "roman-cgi",
                    "band_samples": {
                        "instrument_id": "roman-cgi",
                        "source": band_source,
                        "epoch": epoch,
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
                    "reconstruction_error": {"delta_e2000": 8.0, "note": "test"},
                }
            ],
            "meta": {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "pipeline_version": "0.1.0",
                "schema_version": 5,
            },
        }
    )


def write_board(tmp_path: Path, targets: list[dict]) -> Path:
    path = tmp_path / "roman-targets.json"
    path.write_text(
        json.dumps(
            {
                "mission": {"launch_utc": "2026-08-30T11:20:00Z"},
                "instrument": {"dark_hole_inner_mas": 150.0, "dark_hole_outer_mas": 450.0},
                "source": {"title": "t"},
                "targets": targets,
            }
        )
    )
    return path


# ── the curated file ──────────────────────────────────────────────────────────────────────


def test_curated_file_is_well_formed() -> None:
    doc = load_document(BOARD_JSON)
    assert doc is not None, "the board's curated file must exist"
    targets = doc["targets"]
    assert targets, "no targets defined"

    names = [t["name"] for t in targets]
    assert len(names) == len(set(names)), "target names must be unique"
    ids = [t["catalog_id"] for t in targets if t.get("catalog_id")]
    assert len(ids) == len(set(ids)), "two targets must not point at the same planet"

    for t in targets:
        assert t.get("name"), "every target needs a name"
        # catalog_id is required as a KEY (even when null) so that an unmodelled target is a
        # deliberate statement rather than a forgotten field.
        assert "catalog_id" in t, f"{t['name']}: missing catalog_id (use null if absent)"


def test_mission_and_source_are_present() -> None:
    """The board makes two factual claims outside the catalogue — a launch date and a source
    paper. Neither may go missing, because the page is built around them."""
    doc = load_document(BOARD_JSON)
    assert doc["mission"]["launch_utc"].endswith("Z"), "launch time must be UTC"
    assert doc["mission"]["launch_display"]
    assert doc["source"]["url"].startswith("http")
    counts = doc["source"]["counts"]
    # The three scenario counts the page quotes, straight from the paper's abstract.
    assert (counts["optimistic"], counts["intermediate"], counts["pessimistic"]) == (26, 10, 3)


def test_all_scenario_targets_are_the_three_the_paper_names() -> None:
    """The paper names exactly three planets as accessible under every scenario. Flagging a
    fourth would be inventing a claim the source does not make."""
    doc = load_document(BOARD_JSON)
    flagged = {t["name"] for t in doc["targets"] if t.get("all_scenarios")}
    assert flagged == {"HD 219134 h", "47 UMa c", "eps Eri b"}


def test_missing_file_means_no_board(tmp_path: Path) -> None:
    """A missing curated file drops the page, never breaks the build."""
    assert load_document(tmp_path / "nope.json") is None
    assert resolve([], tmp_path / "nope.json") is None


# ── the join ──────────────────────────────────────────────────────────────────────────────


def test_join_uses_explicit_id_not_the_display_name(tmp_path: Path) -> None:
    """The alias case that motivates the whole design: the board calls it "pi Men b", the
    catalogue calls it "HD 39091 b". Slugging the name would find nothing."""
    path = write_board(tmp_path, [{"name": "pi Men b", "catalog_id": "hd-39091-b"}])
    board = resolve([make_record("hd-39091-b", name="HD 39091 b")], path)
    slot = board.slots[0]
    assert slot.modelled
    assert slot.name == "pi Men b"
    assert slot.record.name == "HD 39091 b"


def test_unresolvable_target_becomes_an_honest_gap(tmp_path: Path) -> None:
    """A target our catalogue lacks stays on the board as an empty row — dropping it would
    quietly shorten the list and overstate our coverage."""
    path = write_board(
        tmp_path,
        [
            {"name": "In Catalogue", "catalog_id": "a-b"},
            {"name": "Not In Catalogue", "catalog_id": None, "note": "why"},
            {"name": "Id Went Stale", "catalog_id": "gone-b"},
        ],
    )
    board = resolve([make_record("a-b")], path)
    assert board.n_targets == 3
    assert board.n_modelled == 1
    absent = [s for s in board.slots if not s.modelled]
    assert len(absent) == 2
    for slot in absent:
        assert slot.predicted_hex is None
        assert slot.record is None
    # Unmodelled slots sink to the bottom, where they read as the gaps they are.
    assert [s.modelled for s in board.slots] == [True, False, False]


def test_ordering_puts_the_surest_targets_first(tmp_path: Path) -> None:
    """Order is the board's argument: all-scenario targets first, then widest-opening first."""
    path = write_board(
        tmp_path,
        [
            {"name": "Narrow", "catalog_id": "narrow-b"},
            {"name": "Wide", "catalog_id": "wide-b"},
            {"name": "Sure", "catalog_id": "sure-b", "all_scenarios": True},
        ],
    )
    board = resolve(
        [
            make_record("narrow-b", sma=1.0, dist_pc=20.0),  # 50 mas
            make_record("wide-b", sma=8.0, dist_pc=20.0),  # 400 mas
            make_record("sure-b", sma=2.0, dist_pc=20.0),  # 100 mas — but named by the paper
        ],
        path,
    )
    assert [s.name for s in board.slots] == ["Sure", "Wide", "Narrow"]


# ── the flip: what happens the day real data lands ────────────────────────────────────────


def test_slots_start_empty(tmp_path: Path) -> None:
    """Today's honest state, asserted so it cannot drift: a prediction and an empty slot."""
    path = write_board(tmp_path, [{"name": "P", "catalog_id": "p-b"}])
    board = resolve([make_record("p-b", roman_hex="#abcdef")], path)
    slot = board.slots[0]
    assert slot.predicted_hex == "#abcdef"
    assert slot.measured is False
    assert slot.measured_hex is None
    assert slot.epoch is None
    assert board.n_measured == 0
    assert board.any_measured is False
    assert board.n_awaiting == 1


def test_measured_provenance_fills_the_slot(tmp_path: Path) -> None:
    """The promise the empty column makes. A record whose provenance the swap seam set to
    measured-cgi fills its slot, carries its epoch, and lights the board's headline count —
    with no edit to this module, the template, or the curated file."""
    path = write_board(tmp_path, [{"name": "P", "catalog_id": "p-b"}])
    board = resolve(
        [
            make_record(
                "p-b",
                roman_hex="#123456",
                provenance="measured-cgi",
                band_source="measured",
                epoch="2027-03-14",
            )
        ],
        path,
    )
    slot = board.slots[0]
    assert slot.measured is True
    assert slot.measured_hex == "#123456"
    assert slot.epoch == "2027-03-14"
    assert board.n_measured == 1
    assert board.any_measured is True
    assert board.n_awaiting == 0


# ── the separation scale ──────────────────────────────────────────────────────────────────


def test_separation_is_arcseconds_of_semi_major_axis_over_distance(tmp_path: Path) -> None:
    """1 AU seen from 1 pc is 1 arcsecond, by the definition of the parsec — so 4 AU at
    20 pc is 0.2 arcsec, i.e. 200 mas. This is the anchor for the whole bar."""
    path = write_board(tmp_path, [{"name": "P", "catalog_id": "p-b"}])
    board = resolve([make_record("p-b", sma=4.0, dist_pc=20.0)], path)
    assert board.slots[0].separation_mas == 200.0


def test_separation_none_without_an_orbit(tmp_path: Path) -> None:
    path = write_board(tmp_path, [{"name": "P", "catalog_id": "p-b"}])
    board = resolve([make_record("p-b", sma=None)], path)
    assert board.slots[0].separation_mas is None
    assert board.slots[0].bar_pos is None


def test_reach_is_judged_against_the_working_annulus(tmp_path: Path) -> None:
    """"within" must mean within the 150–450 mas ring the page draws, or the bar and the
    words beside it would disagree."""
    path = write_board(
        tmp_path,
        [
            {"name": "Tight", "catalog_id": "tight-b"},
            {"name": "Good", "catalog_id": "good-b"},
            {"name": "Far", "catalog_id": "far-b"},
        ],
    )
    board = resolve(
        [
            make_record("tight-b", sma=1.0, dist_pc=20.0),  # 50 mas
            make_record("good-b", sma=5.0, dist_pc=20.0),  # 250 mas
            make_record("far-b", sma=20.0, dist_pc=20.0),  # 1000 mas
        ],
        path,
    )
    reach = {s.name: s.reach for s in board.slots}
    assert reach == {"Tight": "inside", "Good": "within", "Far": "beyond"}
    assert board.n_within == 1


def test_scale_positions_are_monotonic_and_bounded() -> None:
    """Every marker must land on the bar, and further out must always draw further right."""
    assert scale_pos(None) is None
    assert scale_pos(0) is None
    positions = [scale_pos(m) for m in (33, 134, 150, 250, 450, 1102)]
    assert all(0.0 <= p <= 100.0 for p in positions)
    assert positions == sorted(positions)
    # Values off the ends clamp onto the bar rather than overflowing it.
    assert scale_pos(SCALE_MIN_MAS / 10) == 0.0
    assert scale_pos(SCALE_MAX_MAS * 10) == 100.0


# ── the real catalogue ────────────────────────────────────────────────────────────────────


def test_board_resolves_against_the_real_catalogue() -> None:
    """The curated ids must actually match the shipped data. This is the test that catches a
    renamed or dropped planet before the page shows a row of blanks."""
    from pipeline.models import PlanetsFile

    planets = Path("data/planets.json")
    if not planets.exists():
        import pytest

        pytest.skip("planets.json not fetched (see scripts/fetch_data.py)")

    doc = PlanetsFile.model_validate_json(planets.read_text())
    board = resolve(doc.planets, BOARD_JSON)
    assert board is not None

    named = sum(1 for t in load_document(BOARD_JSON)["targets"] if t.get("catalog_id"))
    assert board.n_modelled == named, (
        "every target given a catalog_id must resolve — a stale id renders as a blank row"
    )
    # No exoplanet colour has ever been measured. If this ever fails, the day has come.
    assert board.n_measured == 0
    for slot in board.slots:
        if slot.modelled:
            assert slot.predicted_hex and slot.predicted_hex.startswith("#")
            assert slot.true_hex and slot.true_hex.startswith("#")
