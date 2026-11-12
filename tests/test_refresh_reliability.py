"""Regression cases for missed Archive updates and unsafe release baselines."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
from dataclasses import asdict, fields

import pytest

from pipeline import catalog, cli, drift
from pipeline.fetch.archive import ArchiveRecord


def _row(name="A b", **changes):
    row = dict.fromkeys(f.name for f in fields(ArchiveRecord))
    row.update(pl_name=name, hostname="A", pl_rade=1.0, pl_bmasse=1.0,
               pl_eqt=300.0, pl_orbsmax=1.0, st_teff=5000.0, st_rad=1.0,
               sy_dist=10.0, pl_orbeccen=0.0, disc_method="tran")
    row.update(changes)
    return row


@pytest.fixture
def archive(monkeypatch):
    """Execute the real emitted query against controlled Archive rows."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    columns = ",".join(f.name for f in fields(ArchiveRecord))
    db.execute(f"create table pscomppars ({columns})")

    def replace(*rows):
        db.execute("delete from pscomppars")
        for row in rows:
            names = ",".join(row)
            placeholders = ",".join("?" for _ in row)
            db.execute(
                f"insert into pscomppars ({names}) values ({placeholders})", list(row.values()),
            )

    monkeypatch.setattr(drift, "run_adql", lambda query, **_: [dict(r) for r in db.execute(query)])
    replace(_row())
    yield replace
    db.close()


def _baseline():
    fp = drift.fetch_fingerprint()
    return {"archive": {"gate_version": fp.gate_version, "fingerprint": asdict(fp)}}


@pytest.mark.parametrize("field,value", [
    ("sy_dist", 20.0), ("pl_orbeccen", 0.8), ("ra", 42.0), ("dec", -10.0),
    ("sy_vmag", 8.5), ("hostname", "Corrected host"), ("st_spectype", "K1V"),
    ("disc_method", "micro"), ("disc_year", 2026), ("disc_facility", "Roman"),
    ("pl_rade", 2.0), ("pl_bmasse", 2.0), ("pl_eqt", 310.0),
    ("pl_orbsmax", 2.0), ("st_teff", 5100.0), ("st_rad", 1.1),
])
def test_consumed_metadata_correction_triggers_refresh(archive, field, value):
    baseline = _baseline()
    archive(_row(**{field: value}))
    report = drift.compare(baseline)
    assert report.drift and report.revisions


def test_opposite_temperature_revisions_cannot_cancel(archive):
    archive(_row(st_teff=3000.0), _row("B b", st_teff=6000.0))
    baseline = _baseline()
    archive(_row(st_teff=4000.0), _row("B b", st_teff=5000.0))
    assert drift.compare(baseline).revisions


def test_removal_alone_does_not_claim_survivor_revisions(archive):
    archive(_row(), _row("B b"))
    baseline = _baseline()
    archive(_row())
    report = drift.compare(baseline)
    assert report.removed == ["B b"]
    assert not report.revisions


def test_removal_and_survivor_revision_are_both_reported(archive):
    archive(_row(), _row("B b"))
    baseline = _baseline()
    archive(_row(st_teff=5100.0))
    report = drift.compare(baseline)
    assert report.removed == ["B b"] and report.revisions


def test_row_order_does_not_trigger_refresh(archive):
    archive(_row(), _row("B b"))
    baseline = _baseline()
    archive(_row("B b"), _row())
    assert not drift.compare(baseline).drift


def test_addition_does_not_claim_survivor_revisions(archive):
    baseline = _baseline()
    archive(_row(), _row("B b"))
    report = drift.compare(baseline)
    assert report.added == ["B b"] and not report.revisions


def test_probe_includes_curated_planets_without_distance(archive):
    archive(_row("HD 189733 b", sy_dist=None), _row("Unknown b", sy_dist=None))
    assert set(drift.fetch_fingerprint().rows) == {"HD 189733 b"}


def test_no_baseline_requests_rebuild(archive):
    assert drift.compare(None).drift


def test_changed_gate_requests_rebaseline(archive):
    baseline = _baseline()
    baseline["archive"]["gate_version"] = 0
    report = drift.compare(baseline)
    assert report.drift and "not comparable" in report.reason


def test_corrupt_manifest_cannot_report_in_sync(archive):
    baseline = _baseline()
    baseline["archive"]["fingerprint"]["n"] = 100
    with pytest.raises(ValueError, match="count"):
        drift.compare(baseline)


def test_old_aggregate_manifest_requests_migration(archive):
    old = {"archive": {"gate_version": 1, "fingerprint": {
        "n": 1, "sums": {"st_teff": 5000.0},
    }}}
    report = drift.compare(old)
    assert report.drift and "row hashes" in report.reason


def test_bulk_build_keeps_snapshot_of_inputs_actually_built(archive, monkeypatch, tmp_path):
    def fetch_inputs(*args, **kwargs):
        rows = [ArchiveRecord(**_row())]
        archive(_row(), _row("B b"))
        return rows

    monkeypatch.setattr(catalog, "fetch_bulk", fetch_inputs)
    monkeypatch.setattr(catalog, "fetch_by_names", lambda *a, **kw: [])
    monkeypatch.setattr(cli, "solar_system_planets", lambda: [])
    out = tmp_path / "planets.json"
    cli.cmd_build(argparse.Namespace(source="catalog", bulk=10000, planet=None,
        targets_only=False, no_cache=True, limit=None, merge_into=None, out=out))
    manifest = drift.build_manifest(out)
    assert manifest["archive"]["fingerprint"]["n"] == 1
    assert drift.compare(manifest).added == ["B b"]


def test_manifest_refuses_to_invent_snapshot_for_old_artifact(archive, tmp_path):
    out = tmp_path / "planets.json"
    out.write_text(json.dumps({"planets": [{"id": "a-b"}], "provenance": {}}))
    with pytest.raises(ValueError, match="snapshot"):
        drift.build_manifest(out)


@pytest.fixture
def partial_merge(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "solar_system_planets", lambda: [])

    def build(initial, selected, *, limit=None):
        fetched = []
        monkeypatch.setattr(catalog, "fetch_bulk", lambda *a, **kw: [
            ArchiveRecord(**row) for row in initial
        ])
        monkeypatch.setattr(catalog, "fetch_by_names", lambda *a, **kw: [
            ArchiveRecord(**row) for row in fetched
        ])
        out = tmp_path / "planets.json"
        args = argparse.Namespace(source="catalog", bulk=10000, planet=None,
            targets_only=False, no_cache=True, limit=None, merge_into=None, out=out)
        cli.cmd_build(args)
        previous = json.loads(out.read_text())["provenance"]["archive_snapshot"]
        fetched = selected
        args.bulk, args.planet, args.merge_into = None, [r["pl_name"] for r in selected], out
        args.limit = limit
        cli.cmd_build(args)
        return out, previous

    return build


def test_partial_merge_detects_archive_reverting_to_premerge_value(archive, partial_merge):
    out, _ = partial_merge([_row(st_teff=5000.0)], [_row(st_teff=5100.0)])
    data = json.loads(out.read_text())
    assert data["planets"][0]["host_star"]["teff_k"] == 5100.0
    archive(_row(st_teff=5100.0))
    assert not drift.compare(drift.build_manifest(out)).drift
    archive(_row(st_teff=5000.0))
    report = drift.compare(drift.build_manifest(out))
    assert report.drift and report.revisions


def test_partial_merge_keeps_untouched_planets_hashes(archive, partial_merge):
    out, previous = partial_merge([_row(), _row("B b")], [_row(st_teff=5100.0)])
    snapshot = json.loads(out.read_text())["provenance"]["archive_snapshot"]
    assert snapshot["rows"]["B b"] == previous["rows"]["B b"]
    archive(_row(st_teff=5100.0), _row("B b", st_teff=5200.0))
    report = drift.compare(drift.build_manifest(out))
    assert report.drift and report.revisions


def test_partial_merge_adds_new_planet_hash(archive, partial_merge):
    out, _ = partial_merge([_row()], [_row("B b", st_teff=5100.0)])
    archive(_row(), _row("B b", st_teff=5100.0))
    data = json.loads(out.read_text())
    assert len(data["planets"]) == 2
    assert data["provenance"]["archive_snapshot"]["n"] == 2
    assert not drift.compare(drift.build_manifest(out)).drift


def test_limited_partial_merge_does_not_acknowledge_unbuilt_inputs(archive, partial_merge):
    out, previous = partial_merge(
        [_row(), _row("B b")], [_row(st_teff=5100.0), _row("B b", st_teff=5200.0)], limit=1,
    )
    data = json.loads(out.read_text())
    assert data["planets"][1]["host_star"]["teff_k"] == 5000.0
    snapshot = data["provenance"]["archive_snapshot"]
    assert snapshot["rows"]["B b"] == previous["rows"]["B b"]
    archive(_row(st_teff=5100.0), _row("B b", st_teff=5200.0))
    assert drift.compare(drift.build_manifest(out)).revisions


def test_partial_merge_cannot_invent_missing_bulk_snapshot(partial_merge):
    out, _ = partial_merge([_row()], [_row(st_teff=5100.0)])
    data = json.loads(out.read_text())
    del data["provenance"]["archive_snapshot"]
    out.write_text(json.dumps(data))
    cli.cmd_build(argparse.Namespace(source="catalog", bulk=None, planet=["A b"],
        targets_only=False, no_cache=True, limit=None, merge_into=out, out=out))
    with pytest.raises(ValueError, match="snapshot"):
        drift.build_manifest(out)


def test_truncated_build_cannot_publish_full_catalog_snapshot(archive, monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "fetch_bulk", lambda *a, **kw: [ArchiveRecord(**_row())])
    monkeypatch.setattr(catalog, "fetch_by_names", lambda *a, **kw: [])
    monkeypatch.setattr(cli, "solar_system_planets", lambda: [])
    out = tmp_path / "planets.json"
    cli.cmd_build(argparse.Namespace(source="catalog", bulk=10000, planet=None,
        targets_only=False, no_cache=True, limit=1, merge_into=None, out=out))
    with pytest.raises(ValueError, match="snapshot"):
        drift.build_manifest(out)


def _fake_gh(tmp_path, monkeypatch, body):
    executable = tmp_path / "gh"
    executable.write_text("#!/usr/bin/env python3\n" + body)
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + ":" + os.environ["PATH"])
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/RELEASE").write_text("data-pinned\n")


def test_cli_default_baseline_uses_committed_pin(tmp_path, monkeypatch):
    _fake_gh(tmp_path, monkeypatch, """import json, pathlib, sys
args = sys.argv[1:]
tag = args[2] if len(args) > 2 else ''
directory = pathlib.Path(args[args.index('--dir') + 1])
(directory / 'manifest.json').write_text(json.dumps({'selected': tag}))
""")
    assert drift.load_baseline(None) == {"selected": "data-pinned"}


def test_baseline_download_failure_stops_refresh(tmp_path, monkeypatch):
    _fake_gh(tmp_path, monkeypatch, "raise SystemExit(1)\n")
    with pytest.raises(subprocess.CalledProcessError):
        drift.load_baseline(None)


def test_explicit_missing_baseline_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        drift.load_baseline(tmp_path / "missing.json")
