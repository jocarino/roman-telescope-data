"""The derived physics explanation.

The risk this file guards is specific: an explanation that sounds right and is wrong is worse
than none, because it will be repeated in public with the project's name on it. So the tests
are mostly "does it say the RIGHT mechanism", pinned against planets whose answer is known
independently of our code — the measured solar-system anchors, and the archetypes CLAUDE.md
names.

The bug that motivated most of them: an earlier version led with the spectrum tilt rather than
the regime, and so described HD 189733 b and WASP-12 b — both cloud-free, sodium-bearing and
dark — as "blue-green", because a dark planet's residual blue does tilt that way. Right
numbers, wrong mechanism.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pytest

from pipeline.explain import BANDS, band_means, physics_note

PLANETS = Path("data/planets.json")
pytestmark = pytest.mark.skipif(not PLANETS.exists(), reason="needs data/planets.json")


@lru_cache(maxsize=1)
def _catalogue() -> dict:
    return {p["id"]: p for p in json.loads(PLANETS.read_text())["planets"]}


def _note(pid: str):
    rec = _catalogue().get(pid)
    if rec is None:
        pytest.skip(f"{pid} not in this release")
    note = physics_note(rec)
    assert note is not None
    return rec, note


# --- the mechanism must match the regime, not the tilt ---------------------

@pytest.mark.parametrize(
    ("pid", "must_say"),
    [
        ("hd-189733-b", "sodium"),      # hot, cloud-free — dark, NOT "blue-green"
        ("wasp-12-b", "sodium"),        # ultra-hot, cloud-free
        ("neptune", "methane"),         # measured spectrum; the textbook methane case
        ("trappist-1-e", "rock"),       # rocky, featureless
    ],
)
def test_the_named_mechanism_is_the_regime_not_the_tilt(pid, must_say):
    _, note = _note(pid)
    assert must_say in note.mechanism.lower(), note.mechanism


def test_a_dark_cloud_free_planet_is_never_described_as_a_bright_hue():
    """The specific wrong sentence that shipped once."""
    for pid in ("hd-189733-b", "wasp-12-b"):
        _, note = _note(pid)
        assert "blue-green" not in note.mechanism.lower()


def test_jupiter_reads_as_a_bright_cloud_deck():
    """A measured spectrum with a known answer: thick cloud, bright, near-white."""
    _, note = _note("jupiter")
    assert "cloud" in note.mechanism.lower()
    assert "bright" in note.mechanism.lower() or "white" in note.mechanism.lower()


# --- the illuminant, which is the half people forget ------------------------

def test_a_cool_host_is_reported_as_warming_the_result():
    """Colour is albedo × starlight. TRAPPIST-1 is 2,566 K — that has to appear."""
    _, note = _note("trappist-1-e")
    assert "red-heavy" in note.illuminant
    assert "warmer" in note.illuminant


def test_a_hot_host_is_reported_as_cooling_the_result():
    _, note = _note("bet-pic-d")            # A6 V, ~8,000 K
    assert "blue-heavy" in note.illuminant


def test_a_missing_spectral_type_does_not_produce_a_dangling_parenthetical():
    """Regression: read 'The host is 6,265 K (the host)'."""
    _, note = _note("wasp-12-b")
    assert "(the host)" not in note.illuminant


# --- every claim has to be checkable ---------------------------------------

def test_the_evidence_quotes_the_numbers_and_points_at_the_plot():
    """An explanation nobody can verify is just a nicer-sounding guess."""
    _, note = _note("neptune")
    assert "blue" in note.evidence and "red" in note.evidence
    assert "spectrum plot" in note.evidence


def test_the_caveat_names_the_engine_and_the_assumptions():
    rec, note = _note("k2-18-b")
    assert rec["params"]["spectrum_source"] in note.caveat
    assert "assumed" in note.caveat


def test_band_means_follow_the_stated_grid():
    """The index arithmetic is only safe because the grid is fixed at 380-780/5 nm."""
    values = [0.0] * 40 + [1.0] * 41          # blue half dark, red half bright
    means = band_means(values)
    assert means["blue"] < means["red"]
    assert set(means) == {name for name, _, _ in BANDS}


def test_no_spectrum_means_no_explanation():
    """Better nothing than a story invented around missing data."""
    assert physics_note({"spectrum": {"values": []}, "params": {}, "host_star": {}}) is None


# --- the disagreement flag --------------------------------------------------

def test_a_regime_contradicted_by_its_own_spectrum_is_flagged():
    """Either the regime is wrong for that planet or the spectrum is; both are worth knowing
    before it goes in a post, and neither should be written around."""
    rec = {
        "spectrum": {"values": [0.45] * 81},        # bright and flat …
        "params": {"assumed_cloud_state": "hot, cloud-free, alkali (sodium) absorption",
                   "spectrum_source": "parametric", "sources": {}},
        "host_star": {"teff_k": 5800.0, "spectral_type": "G2 V"},
    }
    note = physics_note(rec)                        # … but filed as cloud-free and dark
    assert note.contradiction is not None
    assert any("Check this one" in line for line in note.lines())


def test_a_consistent_planet_is_not_flagged():
    _, note = _note("neptune")
    assert note.contradiction is None
