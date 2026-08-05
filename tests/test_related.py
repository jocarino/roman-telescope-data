"""The related-planet rails, and the one property the whole design rests on: reciprocity.

A nearest-neighbour "related" list looks the same on the page and behaves completely
differently in the graph — it is asymmetric, so the planets nobody happens to be nearest to
gain no inbound links and stay exactly as buried as they were. web/related.py uses rings
instead precisely so that cannot happen, and a ring that quietly stops being a ring would
still render fine. Hence these.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pytest

from pipeline.models import PlanetRecord
from web.related import RING, build_related, rail_stats

PLANETS_JSON = Path("data/planets.json")

pytestmark = pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")


@lru_cache(maxsize=1)
def _records() -> tuple[PlanetRecord, ...]:
    """A slice wide enough to exercise the rails: several colour families, several size
    classes, and the solar-system anchors (which are the odd ones out on every axis)."""
    doc = json.loads(PLANETS_JSON.read_text())
    picks = {"earth", "jupiter", "neptune", "hd-189733-b"}
    wanted = [p for p in doc["planets"] if p["id"] in picks]
    wanted += doc["planets"][:150]
    seen, planets = set(), []
    for p in wanted:
        if p["id"] not in seen:
            seen.add(p["id"])
            planets.append(p)
    return tuple(PlanetRecord.model_validate(p) for p in planets)


@lru_cache(maxsize=1)
def _related() -> dict[str, list]:
    return build_related(list(_records()))


def _links(rails: list) -> set[str]:
    return {p.id for rail in rails for p in rail.planets}


def test_every_planet_gets_rails():
    related = _related()
    assert set(related) == {r.id for r in _records()}
    empty = sorted(pid for pid, rails in related.items() if not rails)
    assert not empty, f"planets with no related links at all: {empty[:5]}"


def test_links_are_reciprocal():
    """The load-bearing property: if A points at B, B points back at A.

    This is what turns outbound links into inbound ones for *every* planet rather than for the
    popular half. If it fails, the rails have drifted from a ring to a nearest-neighbour list
    and the tail of the catalogue is thin again.
    """
    related = _related()
    broken = [
        (a, b)
        for a, rails in related.items()
        for b in _links(rails)
        if a not in _links(related[b])
    ]
    assert not broken, f"{len(broken)} one-way links, e.g. {broken[:3]}"


def test_inbound_matches_outbound_for_every_planet():
    related = _related()
    inbound: dict[str, int] = dict.fromkeys(related, 0)
    for rails in related.values():
        for pid in _links(rails):
            inbound[pid] += 1
    mismatched = {
        pid: (len(_links(related[pid])), n)
        for pid, n in inbound.items()
        if n != len(_links(related[pid]))
    }
    assert not mismatched, f"out/in degree disagree: {list(mismatched.items())[:3]}"


def test_no_self_links_and_no_duplicates():
    for pid, rails in _related().items():
        ids = [p.id for rail in rails for p in rail.planets]
        assert pid not in ids, f"{pid} links to itself"
        assert len(ids) == len(set(ids)), f"{pid} lists the same planet twice: {ids}"


def test_a_planet_never_relinks_its_own_siblings():
    """Siblings have their own strip at the top of the page; spending a rail on them would
    hand the reader a link they were just given, and buy the graph nothing."""
    records = {r.id: r for r in _records()}
    for pid, rails in _related().items():
        rec = records[pid]
        sibs = {s.id for s in rec.system.siblings} if rec.system else set()
        assert not (_links(rails) & sibs), f"{pid} re-links siblings {_links(rails) & sibs}"


def test_rails_are_deterministic():
    a, b = build_related(list(_records())), build_related(list(_records()))
    assert {k: [(r.key, [p.id for p in r.planets]) for r in v] for k, v in a.items()} == {
        k: [(r.key, [p.id for p in r.planets]) for r in v] for k, v in b.items()
    }


def test_rails_carry_a_plain_english_label_and_reason():
    """Dual-audience rule: a row of planet names with no stated relation is a widget, not an
    explanation. Every rail says what it is linking on."""
    for rails in _related().values():
        for rail in rails:
            assert rail.label and rail.label[0].isupper()
            assert rail.blurb.endswith(".")
            assert rail.key in RING


def test_stats_report_the_real_totals():
    related = _related()
    stats = rail_stats(related)
    assert stats["planets"] == len(related)
    assert stats["links"] == sum(len(_links(r)) for r in related.values())
    assert stats["min_per_planet"] >= 1
