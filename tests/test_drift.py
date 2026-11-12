"""Drift probe: gate/ADQL parity, fingerprint comparison, and the manifest contract.

All offline. The one thing worth guarding hardest is that `GATE_CLAUSES` keeps expressing the
same rule in both languages — a Python-side gate and an ADQL mirror that disagree is not a
hypothetical bug, it is the one that produced a phantom "560 planets behind".
"""

from __future__ import annotations

import json

import pytest

from pipeline.catalog import GATE_CLAUSES, completeness_gate, gate_adql
from pipeline.fetch.archive import ArchiveRecord


def _rec(**kw) -> ArchiveRecord:
    base = dict(pl_name="X b", hostname="X", pl_eqt=None, pl_rade=None, pl_bmasse=None,
                pl_orbsmax=None, pl_orbeccen=None, st_teff=None, st_rad=None, st_spectype=None,
                sy_dist=10.0, disc_method="tran", disc_year=2020, disc_facility="TESS")
    base.update(kw)
    return ArchiveRecord(**base)


# --- the gate is expressed twice; both must stay present and aligned ----------------------


def test_every_clause_carries_both_languages():
    for clause in GATE_CLAUSES:
        assert clause.reason, "a clause with no reason cannot explain an exclusion"
        assert callable(clause.keep)
        assert clause.adql.strip(), f"clause {clause.reason!r} has no ADQL equivalent"


def test_gate_adql_contains_every_clause():
    """The composed WHERE fragment must be the AND of all clauses — no clause silently dropped,
    which is how a remote count starts disagreeing with the local gate."""
    composed = gate_adql()
    for clause in GATE_CLAUSES:
        assert clause.adql in composed
    assert composed.count(" and ") >= len(GATE_CLAUSES) - 1


@pytest.mark.parametrize(
    "column",
    ["pl_rade", "pl_bmasse", "st_teff", "pl_eqt", "st_rad", "pl_orbsmax"],
)
def test_gate_adql_references_the_columns_it_gates_on(column):
    assert column in gate_adql()


def test_refactored_gate_preserves_its_verdicts():
    """The clause table replaced a chain of ifs; these are the same cases the original had, so a
    future reordering that changes an exclusion reason gets caught here."""
    ok, reason = completeness_gate(_rec(pl_rade=1.0, st_teff=5772.0, pl_eqt=300.0))
    assert ok and reason is None

    ok, reason = completeness_gate(_rec(st_teff=5772.0, pl_eqt=300.0))
    assert not ok and "size" in reason

    ok, reason = completeness_gate(_rec(pl_rade=2.2, pl_eqt=50.0))
    assert not ok and "host star" in reason

    ok, reason = completeness_gate(_rec(pl_rade=13.0, pl_eqt=300.0, st_teff=40000.0))
    assert not ok and "too hot" in reason

    ok, reason = completeness_gate(_rec(pl_rade=1.0, st_teff=5772.0))
    assert not ok and "temperature" in reason

    # A computable temperature is enough; so is a hot but genuine main-sequence star.
    assert completeness_gate(_rec(pl_rade=2.0, st_teff=5772.0, st_rad=1.0, pl_orbsmax=1.0))[0]
    assert completeness_gate(_rec(pl_bmasse=3000.0, pl_eqt=1700.0, st_teff=8000.0))[0]


def test_teff_ceiling_never_sees_a_null():
    """Clause order is load-bearing: the ceiling comparison would raise on None if the
    "unknown host star" clause did not reject those rows first."""
    ok, reason = completeness_gate(_rec(pl_rade=1.0, pl_eqt=300.0, st_teff=None))
    assert not ok and "host star" in reason


# --- what actually moved between two builds ------------------------------------------------


def _catalogue(tmp_path, name, planets):
    p = tmp_path / name
    p.write_text(json.dumps({"schema_version": 5, "planets": planets}))
    return p


def _planet(pid, true_hex="#112233", roman_hex="#445566"):
    return {
        "id": pid,
        "true_colour": {"hex": true_hex},
        "instrument_views": [{"colour": {"hex": roman_hex}}],
    }


def test_diff_reports_membership_and_colour_moves(tmp_path):
    from pipeline.drift import diff_catalogues

    before = _catalogue(tmp_path, "before.json", [_planet("a"), _planet("b"), _planet("c")])
    after = _catalogue(
        tmp_path,
        "after.json",
        [_planet("a"), _planet("b", true_hex="#ff0000"), _planet("d")],
    )
    d = diff_catalogues(before, after)
    assert d.added == ["d"] and d.removed == ["c"]
    assert d.recoloured == ["b"] and d.roman_changed == []
    assert d.total_before == 3 and d.total_after == 3
    assert "1 changed true colour" in d.summary()


def test_diff_separates_true_colour_from_roman_colour(tmp_path):
    """A band-configuration change moves the Roman swatch and leaves the true colour alone —
    the case that needs to be visible on its own, since it is the signature feature."""
    from pipeline.drift import diff_catalogues

    before = _catalogue(tmp_path, "b.json", [_planet("a")])
    after = _catalogue(tmp_path, "a.json", [_planet("a", roman_hex="#00ff00")])
    d = diff_catalogues(before, after)
    assert d.roman_changed == ["a"] and d.recoloured == []


def test_diff_tolerates_a_record_with_no_instrument_views(tmp_path):
    from pipeline.drift import diff_catalogues

    bare = {"id": "a", "true_colour": {"hex": "#112233"}, "instrument_views": []}
    before = _catalogue(tmp_path, "b2.json", [bare])
    after = _catalogue(tmp_path, "a2.json", [bare])
    assert diff_catalogues(before, after).recoloured == []
