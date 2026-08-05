"""The file must say what built it and which upstream snapshot it was built from.

`schema_version` describes the record shape, and `pscomppars` is a live table — so two files
can agree on every version number and still be built from different data. These tests pin the
things that actually distinguish two builds.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from pipeline import provenance
from pipeline.config import ROMAN_CGI
from pipeline.demo_planets import demo_planets
from pipeline.emit.build import build_record
from pipeline.emit.writer import write_planets


@pytest.fixture(autouse=True)
def _clean_recorder():
    provenance.reset_queries()
    yield
    provenance.reset_queries()


def _write(tmp_path):
    pin = demo_planets()[0]
    rec = build_record(pin, [ROMAN_CGI], "2026-08-05T00:00:00+00:00")
    out = write_planets([rec], "2026-08-05T00:00:00+00:00", out=tmp_path / "planets.json")
    return json.loads(out.read_text())


def test_header_records_the_code_that_built_it(tmp_path):
    doc = _write(tmp_path)
    prov = doc["provenance"]

    assert prov["generated_at"] == "2026-08-05T00:00:00+00:00"
    assert prov["planet_count"] == 1
    # Run from a checkout, so the commit is knowable and must be there — a build that cannot
    # name its own code is the failure mode this block exists to prevent.
    assert prov["code"]["source"] == "git"
    assert len(prov["code"]["commit"]) == 40
    assert prov["code"]["dirty"] in (True, False)


def test_header_records_every_tap_query_with_its_own_timestamp(tmp_path):
    provenance.record_query(
        service="https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
        table="pscomppars",
        adql="select top 5 pl_name from pscomppars",
        fetched_at="2026-06-01T09:00:00+00:00",
        fetched_at_source=provenance.FETCHED_AT_RECORDED,
        rows=5,
        from_cache=True,
    )
    provenance.record_query(
        service="https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
        table="pscomppars",
        adql="select pl_name from pscomppars where pl_name = 'Earth'",
        fetched_at="2026-08-04T09:00:00+00:00",
        fetched_at_source=provenance.FETCHED_AT_RECORDED,
        rows=1,
        from_cache=False,
    )

    up = _write(tmp_path)["provenance"]["upstream"]

    assert [q["rows"] for q in up["queries"]] == [5, 1]
    # Verbatim, because a paraphrased query cannot be re-run.
    assert up["queries"][0]["adql"] == "select top 5 pl_name from pscomppars"
    # A file is only as fresh as its STALEST input: the two-month-old cached response bounds
    # the snapshot, not the fresh query and not generated_at.
    assert up["snapshot_at"] == "2026-06-01T09:00:00+00:00"
    assert up["newest_query_at"] == "2026-08-04T09:00:00+00:00"


def test_a_cache_hit_keeps_the_original_fetch_time(tmp_path, monkeypatch):
    """A rebuild off an old cache is an old snapshot. Inheriting the build's clock here would
    make a stale file look fresh — the exact claim the provenance block exists to refuse."""
    from pipeline.fetch import archive

    monkeypatch.setattr(archive, "_CACHE_DIR", tmp_path)
    query = "select top 1 pl_name from pscomppars"
    archive._cache_path(query).write_text(json.dumps([{"pl_name": "HD 189733 b"}]))
    archive._cache_meta_path(query).write_text(
        json.dumps({"query": query, "fetched_at": "2026-01-15T12:00:00+00:00"})
    )

    rows = archive._run_query(query, use_cache=True)

    assert rows == [{"pl_name": "HD 189733 b"}]
    (q,) = provenance.recorded_queries()
    assert q.fetched_at == "2026-01-15T12:00:00+00:00"
    assert q.fetched_at_source == provenance.FETCHED_AT_RECORDED
    assert q.from_cache is True
    assert q.rows == 1


def test_a_cache_entry_with_no_sidecar_falls_back_to_its_mtime(tmp_path, monkeypatch):
    """Caches written before the sidecar existed must still date themselves — approximately,
    and labelled as approximate, rather than silently borrowing the build's timestamp."""
    from pipeline.fetch import archive

    monkeypatch.setattr(archive, "_CACHE_DIR", tmp_path)
    query = "select top 2 pl_name from pscomppars"
    path = archive._cache_path(query)
    path.write_text(json.dumps([{"pl_name": "a"}, {"pl_name": "b"}]))
    old = datetime.now(UTC) - timedelta(days=30)
    import os

    os.utime(path, (old.timestamp(), old.timestamp()))

    archive._run_query(query, use_cache=True)

    (q,) = provenance.recorded_queries()
    assert q.fetched_at_source == provenance.FETCHED_AT_CACHE_MTIME
    assert q.fetched_at.startswith(old.strftime("%Y-%m-%d"))


def test_release_tag_is_null_until_stamped(tmp_path):
    """A locally built file was never published, and says so."""
    from scripts.stamp_release_tag import stamp

    out = tmp_path / "planets.json"
    doc = _write(tmp_path)
    assert doc["provenance"]["release_tag"] is None

    stamp(out, "data-20260805-1200")
    assert json.loads(out.read_text())["provenance"]["release_tag"] == "data-20260805-1200"


def test_stamping_a_file_with_no_provenance_refuses(tmp_path):
    """Publishing a file built by an older pipeline would ship an un-identifiable snapshot."""
    from scripts.stamp_release_tag import stamp

    old = tmp_path / "old.json"
    old.write_text(json.dumps({"schema_version": 5, "planets": []}))
    with pytest.raises(SystemExit, match="no provenance header"):
        stamp(old, "data-20260805-1200")
