"""What produced this file, and which upstream snapshot it was produced from.

`planets.json` used to carry three version numbers -- `schema_version`, `pipeline_version`
and the release tag -- none of which identifies the *data* it was built from. `pscomppars`
is a LIVING table: rows are added and values revised continuously, so two releases a month
apart are not comparable, and nothing in the file said so. Worse, `pipeline_version` is
hand-maintained and has never been bumped, so it identifies nothing at all.

This module records the things that actually pin a build down:

- the **code**: the git commit the pipeline ran at, and whether the tree was dirty;
- the **upstream snapshot**: every TAP query that fed the build, verbatim, each with the
  timestamp of the response it used -- which for a cache hit is when the *cached* response
  was fetched, not when the build ran. A rebuild today from a two-month-old cache is a
  two-month-old snapshot, and the header says so rather than inheriting `generated_at`.

The queries are collected by `pipeline.fetch.archive`, which calls `record_query()` on every
TAP response it returns (fresh or cached). `pipeline.emit.writer` then stamps the assembled
block into the file header. Nothing here imports the fetch layer, so the dependency runs one
way only.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# How a `fetched_at` was established, so a reader knows what it is trusting.
FETCHED_AT_RECORDED = "recorded"  # written by us when the response came back from TAP
FETCHED_AT_CACHE_MTIME = "cache-mtime"  # inferred from the cache file, no sidecar present
FETCHED_AT_UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryRecord:
    """One TAP response that fed this build."""

    service: str
    table: str
    adql: str
    fetched_at: str
    fetched_at_source: str
    rows: int
    from_cache: bool


# Module-level because the fetch layer is called from many places and threading a collector
# through every call site would put provenance plumbing in signatures that are about planets.
# One build = one process, so a process-wide list is the right scope.
_QUERIES: list[QueryRecord] = []


def record_query(
    *,
    service: str,
    table: str,
    adql: str,
    fetched_at: str,
    fetched_at_source: str,
    rows: int,
    from_cache: bool,
) -> None:
    """Note a TAP response used by this build. Idempotent per identical query text: the same
    query run twice in one build (curated + bulk paths can overlap) is recorded once."""
    rec = QueryRecord(
        service=service,
        table=table,
        adql=adql,
        fetched_at=fetched_at,
        fetched_at_source=fetched_at_source,
        rows=rows,
        from_cache=from_cache,
    )
    if any(q.adql == rec.adql and q.fetched_at == rec.fetched_at for q in _QUERIES):
        return
    _QUERIES.append(rec)


def recorded_queries() -> list[QueryRecord]:
    return list(_QUERIES)


def reset_queries() -> None:
    """Drop everything recorded so far. For tests, and for any caller building more than one
    file in a process."""
    _QUERIES.clear()


@dataclass(frozen=True)
class CodeVersion:
    """The commit the pipeline ran at. `source` says where it came from, because a build in a
    container with no `.git` can only report what the environment told it."""

    commit: str | None = None
    short: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    source: str = "unavailable"


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(  # noqa: S603 (fixed argv, no shell)
            ["git", "-C", str(_REPO_ROOT), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip()


def code_version() -> CodeVersion:
    """The git commit, or the CI-provided SHA when there is no working tree to ask.

    `dirty` counts uncommitted changes to TRACKED files only -- untracked scratch in the tree
    is not a difference in the code that ran, and treating it as one would mark almost every
    local build dirty.
    """
    commit = _git("rev-parse", "HEAD")
    if commit:
        status = _git("status", "--porcelain", "--untracked-files=no")
        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        return CodeVersion(
            commit=commit,
            short=commit[:12],
            branch=branch or None,
            dirty=bool(status) if status is not None else None,
            source="git",
        )
    # No working tree (container build, exported tarball): trust the environment if it says.
    env_sha = os.environ.get("GITHUB_SHA") or os.environ.get("GIT_COMMIT")
    if env_sha:
        return CodeVersion(commit=env_sha, short=env_sha[:12], source="env")
    return CodeVersion()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Upstream:
    """The Archive snapshot this file was built from."""

    # The oldest response used, because a file is only as fresh as its stalest input.
    snapshot_at: str | None = None
    newest_query_at: str | None = None
    queries: tuple[QueryRecord, ...] = ()
    note: str = (
        "pscomppars is a live table: rows are added and values revised continuously. "
        "snapshot_at is the oldest TAP response this build used (a cached response keeps "
        "its original fetch time), so it -- not generated_at -- bounds how current these "
        "planet parameters are. Two files with different snapshot_at values are built from "
        "different upstream data even when every version number matches."
    )


@dataclass(frozen=True)
class Provenance:
    """The header block: what code ran, against what data, and what the version numbers mean.

    The three version numbers live here TOGETHER because separately each one misleads:
    `schema_version` describes the record shape only, `pipeline_version` is hand-maintained
    and has never been bumped, and `release_tag` names a publication, not a build.
    `code.commit` and `upstream.snapshot_at` are the two that actually identify a build.
    """

    generated_at: str = ""
    schema_version: int = 0
    pipeline_version: str = ""
    gate_version: int = 0
    # Stamped in by scripts/release-data.sh at publish time; null in a locally built file,
    # which is itself informative -- an unstamped file was never published.
    release_tag: str | None = None
    planet_count: int = 0
    code: CodeVersion = field(default_factory=CodeVersion)
    upstream: Upstream = field(default_factory=Upstream)
    versions_note: str = (
        "schema_version describes the record SHAPE only -- it cannot express a change of "
        "input data or of the instrument band set. pipeline_version is hand-maintained. "
        "release_tag names a publication. To tell two builds apart, compare code.commit and "
        "upstream.snapshot_at; to tell what changed in the catalogue itself, compare the "
        "manifest.json published alongside this file (see pipeline/drift.py)."
    )

    def as_dict(self) -> dict:
        return asdict(self)


def build_provenance(*, planet_count: int, generated_at: str | None = None) -> Provenance:
    """Assemble the header block from what this process actually did."""
    from pipeline.config import PIPELINE_VERSION, SCHEMA_VERSION
    from pipeline.drift import GATE_VERSION

    queries = recorded_queries()
    stamps = sorted(q.fetched_at for q in queries if q.fetched_at)
    return Provenance(
        generated_at=generated_at or _now_iso(),
        schema_version=SCHEMA_VERSION,
        pipeline_version=PIPELINE_VERSION,
        gate_version=GATE_VERSION,
        release_tag=os.environ.get("DATA_RELEASE_TAG") or None,
        planet_count=planet_count,
        code=code_version(),
        upstream=Upstream(
            snapshot_at=stamps[0] if stamps else None,
            newest_query_at=stamps[-1] if stamps else None,
            queries=tuple(queries),
        ),
    )
