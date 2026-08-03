"""Drift probe: gate/ADQL parity, fingerprint comparison, and the manifest contract.

All offline. The one thing worth guarding hardest is that `GATE_CLAUSES` keeps expressing the
same rule in both languages — a Python-side gate and an ADQL mirror that disagree is not a
hypothetical bug, it is the one that produced a phantom "560 planets behind".
"""

from __future__ import annotations

import json

import pytest

from pipeline.catalog import GATE_CLAUSES, completeness_gate, gate_adql
from pipeline.drift import (
    FINGERPRINT_COLUMNS,
    Fingerprint,
    compare,
    fingerprint_from_manifest,
)
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


# --- the fingerprint ---------------------------------------------------------------------


def _fp(n=100, **sums) -> Fingerprint:
    base = {c: 1.0 for c in FINGERPRINT_COLUMNS}
    base.update(sums)
    return Fingerprint(n=n, sums=base)


def test_fingerprint_covers_every_column_the_pipeline_reads():
    """A revision to a column the pipeline consumes must be visible, or the probe reports
    "in sync" while colours are stale."""
    for column in ("pl_rade", "pl_bmasse", "pl_eqt", "pl_orbsmax", "st_teff", "st_rad"):
        assert column in FINGERPRINT_COLUMNS


def test_identical_fingerprints_do_not_differ():
    assert not _fp().differs_from(_fp())


def test_count_change_is_drift():
    assert _fp(n=101).differs_from(_fp(n=100))


def test_value_revision_is_drift_even_at_the_same_count():
    """The whole reason the probe sums instead of counting: same membership, changed values."""
    assert _fp(st_teff=2.0).differs_from(_fp(st_teff=1.0))


# --- comparison against a manifest --------------------------------------------------------


def _manifest(names, n=None, **sums) -> dict:
    base = {c: 1.0 for c in FINGERPRINT_COLUMNS}
    base.update(sums)
    return {
        "catalogue": {"planets": len(names), "schema_version": 5, "pipeline_version": "0.1.0"},
        "archive": {
            "table": "pscomppars",
            "gate_version": 1,
            "queried_at": "2026-08-03T00:00:00+00:00",
            "fingerprint": {"n": n if n is not None else len(names), "sums": base},
            "names": sorted(names),
        },
    }


def test_manifest_round_trips_to_a_fingerprint():
    fp = fingerprint_from_manifest(_manifest(["A b", "B c"], st_teff=7.5))
    assert fp.n == 2 and fp.sums["st_teff"] == 7.5 and fp.gate_version == 1


def test_no_baseline_reports_drift_not_silence(monkeypatch):
    """"I cannot tell" must not be answered with "no". A first run, or a release published before
    manifests existed, has to trigger a rebuild rather than report everything is fine."""
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp())
    report = compare(None)
    assert report.drift and "no baseline" in report.reason


def test_gate_version_mismatch_is_not_reported_as_data_drift(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp())
    stale = _manifest(["A b"])
    stale["archive"]["gate_version"] = 0
    report = compare(stale)
    assert report.drift and "not comparable" in report.reason
    assert not report.added and not report.removed


def test_unchanged_fingerprint_reports_in_sync(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=2))
    called = []
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: called.append(1) or [])
    report = compare(_manifest(["A b", "B c"], n=2))
    assert not report.drift
    assert not called, "the expensive name query must not run when nothing changed"


def test_added_and_removed_planets_are_named(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=2))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["B c", "C d"])
    report = compare(_manifest(["A b", "B c"], n=3))
    assert report.drift
    assert report.added == ["C d"]
    assert report.removed == ["A b"]


def test_revision_only_drift_is_reported_without_membership_change(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=2, st_teff=99.0))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c"])
    report = compare(_manifest(["A b", "B c"], n=2))
    assert report.drift and not report.added and not report.removed
    assert report.revisions and "same planets" in report.revision_check


def test_an_addition_alone_is_not_reported_as_revisions(monkeypatch):
    """The bug this test exists for: adding a planet moves the sums, and an earlier version read
    that as thousands of planets being revised. Reconcile the sums against the new row instead."""
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=3, st_teff=4.0))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c", "C d"])
    # The newcomer accounts for the whole delta: baseline st_teff 1.0 + 3.0 == live 4.0.
    monkeypatch.setattr(
        "pipeline.drift._sums_for",
        lambda names, **_: {c: (3.0 if (names and c == "st_teff") else 0.0)
                            for c in FINGERPRINT_COLUMNS},
    )
    report = compare(_manifest(["A b", "B c"], n=2))
    assert report.added == ["C d"]
    assert not report.revisions, report.revision_check
    assert report.headline() == "Catalogue: +1 planet"


def test_addition_plus_a_real_revision_is_detected(monkeypatch):
    """Same shape, but the sums do not reconcile — an existing planet changed too."""
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=3, st_teff=50.0))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c", "C d"])
    monkeypatch.setattr(
        "pipeline.drift._sums_for",
        lambda names, **_: {c: (3.0 if (names and c == "st_teff") else 0.0)
                            for c in FINGERPRINT_COLUMNS},
    )
    report = compare(_manifest(["A b", "B c"], n=2))
    assert report.revisions and "reconcile" in report.revision_check
    assert report.headline() == "Catalogue: +1 planet, values revised"


def test_headline_never_invents_a_revision_count(monkeypatch):
    """The probe cannot count revisions without the old per-planet values; the rebuild reports
    the real number from its cache misses. So the headline must not carry a figure."""
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=2, st_teff=99.0))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c"])
    headline = compare(_manifest(["A b", "B c"], n=2)).headline()
    assert "values revised" in headline
    assert not any(ch.isdigit() for ch in headline)


def test_headline_is_readable_without_opening_anything(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=3))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c", "C d"])
    monkeypatch.setattr("pipeline.drift._sums_for", lambda names, **_: dict.fromkeys(
        FINGERPRINT_COLUMNS, 1.0 if names else 0.0))
    report = compare(_manifest(["A b", "B c"], n=2))
    assert report.headline().startswith("Catalogue: +1 planet")
    assert json.loads(report.to_json())["headline"] == report.headline()


def test_in_sync_headline(monkeypatch):
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp(n=2))
    monkeypatch.setattr("pipeline.drift.fetch_gated_names", lambda **_: ["A b", "B c"])
    assert "in sync" in compare(_manifest(["A b", "B c"], n=2)).headline()


def test_no_baseline_headline_does_not_claim_a_data_finding(monkeypatch):
    """A first run has nothing to compare against. Saying "Archive values changed" would be a
    claim we cannot support — the project's whole position is not doing that."""
    monkeypatch.setattr("pipeline.drift.fetch_fingerprint", lambda **_: _fp())
    headline = compare(None).headline()
    assert "no baseline" in headline
    assert "changed" not in headline


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
