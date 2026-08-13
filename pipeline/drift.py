"""Has the Archive changed since we last built? — the cheap probe behind the weekly refresh.

Rebuilding the catalogue takes minutes and publishing it is an outward-facing act, so neither
should happen on a schedule "just in case". This module answers the prior question in one HTTP
request, so the expensive path only runs when there is something to rebuild for.

Two design decisions carry most of the value:

**Count rows and you will miss most of the change.** `pscomppars` is a *composite* table: it
re-derives each planet's best-available parameters from the literature continuously. A new paper
measuring a better radius for a planet found in 2014 rewrites that row, and its colour should
change with it — while the row count sits perfectly still. So the probe takes a FINGERPRINT:
the count plus sums over the columns the pipeline actually consumes. Additions, removals and
revisions all move it, for the same single query a bare count would have cost.

**The predicate is derived, never retyped.** The gated set is defined once, in
`pipeline.catalog.GATE_CLAUSES`, which carries each requirement as both a Python predicate and
its ADQL equivalent. A hand-written mirror of that gate is exactly how an earlier attempt
concluded the catalogue was "560 planets behind" when the difference was the gate doing its job.

The baseline lives in `manifest.json`, published beside `planets.json` on each data release, so
there is no state to keep anywhere: once a release ships, the probe goes quiet by itself.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pipeline.catalog import gate_adql
from pipeline.config import PIPELINE_VERSION, SCHEMA_VERSION
from pipeline.fetch.archive import BULK_PREFILTER_ADQL, TABLE, run_adql

# Columns summed into the fingerprint: every Archive value the colour pipeline reads. A revision
# to any of them changes a planet's modelled colour, so a revision to any of them must be
# visible here. Ordered for a stable manifest.
FINGERPRINT_COLUMNS: tuple[str, ...] = (
    "pl_rade",
    "pl_bmasse",
    "pl_eqt",
    "pl_orbsmax",
    "st_teff",
    "st_rad",
)

# Sums of thousands of floats are not bit-stable across servers or row orderings; the archive's
# own values carry far fewer significant figures than this, so rounding here removes false
# positives without hiding any real revision.
_SUM_DECIMALS = 3

# Bumped when the gate's meaning changes. A baseline recorded under a different gate version is
# not comparable, and the probe says so rather than reporting a drift that is really our own
# definition moving.
GATE_VERSION = 1


@dataclass(frozen=True)
class Fingerprint:
    """What the gated Archive set looks like right now, in one row of numbers."""

    n: int
    sums: dict[str, float]
    gate_version: int = GATE_VERSION
    queried_at: str = ""

    def differs_from(self, other: Fingerprint) -> bool:
        return self.n != other.n or self.sums != other.sums


@dataclass
class DriftReport:
    drift: bool
    reason: str
    live: Fingerprint | None = None
    baseline: Fingerprint | None = None
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    revisions: bool = False
    revision_check: str = "not checked"

    def headline(self) -> str:
        """One line fit for a PR title or a notification subject — the whole point is that this
        is readable without opening anything."""
        if not self.drift:
            return "Catalogue: in sync with the Archive"
        if self.baseline is None:
            # Don't dress "I have nothing to compare against" up as a finding about the data.
            return "Catalogue: no baseline to compare against — rebuild to establish one"
        bits = []
        if self.added:
            bits.append(f"+{len(self.added)} planet{'s' if len(self.added) != 1 else ''}")
        if self.removed:
            bits.append(f"-{len(self.removed)} planet{'s' if len(self.removed) != 1 else ''}")
        if self.revisions:
            # Deliberately not a number. The probe can prove revisions happened but cannot count
            # them without the previous per-planet values; the rebuild reports the real figure
            # from its cache misses. A plausible-looking count here would be invented.
            bits.append("values revised")
        return "Catalogue: " + (", ".join(bits) if bits else "Archive values changed")

    def to_json(self) -> str:
        payload = asdict(self)
        payload["headline"] = self.headline()
        return json.dumps(payload, indent=2, sort_keys=True)


def _gated_where() -> str:
    """The rows a bulk build would ingest: the fetch pre-filter AND the completeness gate."""
    return f"{BULK_PREFILTER_ADQL} and {gate_adql()}"


def fetch_fingerprint(*, use_cache: bool = False) -> Fingerprint:
    """One TAP query. Counts the gated set and sums the columns the pipeline consumes."""
    sums = ", ".join(f"sum({c}) as s_{c}" for c in FINGERPRINT_COLUMNS)
    rows = run_adql(
        f"select count(*) as n, {sums} from {TABLE} where {_gated_where()}",
        use_cache=use_cache,
    )
    if not rows:
        raise RuntimeError("TAP returned no rows for the fingerprint query")
    row = rows[0]
    return Fingerprint(
        n=int(row["n"]),
        # SUM() skips nulls, so a column nobody has measured yet reads 0.0 rather than vanishing.
        sums={
            c: round(float(row.get(f"s_{c}") or 0.0), _SUM_DECIMALS)
            for c in FINGERPRINT_COLUMNS
        },
        queried_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
    )


def fetch_gated_names(*, use_cache: bool = False) -> list[str]:
    """Every planet name in the gated set. ~100 KB, so it is fetched only once the fingerprint
    has already said something changed — that ordering is what makes the frequent probe cheap."""
    rows = run_adql(
        f"select pl_name from {TABLE} where {_gated_where()}", use_cache=use_cache
    )
    return sorted(str(r["pl_name"]) for r in rows)


def build_manifest(planets_json: Path, *, use_cache: bool = False) -> dict:
    """The release's self-description: what we built, and the Archive snapshot we built it from.

    Distinct from the `provenance` header inside `planets.json` (`pipeline/provenance.py`), and
    the two answer different questions. That one says what THIS file was built from — the commit,
    the queries, their timestamps. This one is a *comparable* fingerprint of the gated Archive
    set, which is what lets the next probe run decide whether anything moved.
    """
    data = json.loads(planets_json.read_text())
    fp = fetch_fingerprint(use_cache=use_cache)
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "catalogue": {
            "planets": len(data["planets"]),
            "schema_version": data.get("schema_version", SCHEMA_VERSION),
            "pipeline_version": PIPELINE_VERSION,
        },
        "archive": {
            "table": TABLE,
            "gate_version": fp.gate_version,
            "queried_at": fp.queried_at,
            "fingerprint": {"n": fp.n, "sums": fp.sums},
            "names": fetch_gated_names(use_cache=use_cache),
        },
    }


def fingerprint_from_manifest(manifest: dict) -> Fingerprint:
    arch = manifest["archive"]
    fp = arch["fingerprint"]
    return Fingerprint(
        n=int(fp["n"]),
        sums={k: round(float(v), _SUM_DECIMALS) for k, v in fp["sums"].items()},
        gate_version=int(arch.get("gate_version", 0)),
        queried_at=str(arch.get("queried_at", "")),
    )


def compare(baseline: dict | None, *, use_cache: bool = False) -> DriftReport:
    """Compare the live Archive against a release manifest.

    A missing or older-gate baseline reports drift with an explicit reason rather than pretending
    to be in sync — the honest answer to "I cannot tell" is not "no".
    """
    live = fetch_fingerprint(use_cache=use_cache)

    if baseline is None:
        return DriftReport(True, "no baseline manifest — treating as drift", live=live)

    base = fingerprint_from_manifest(baseline)
    if base.gate_version != live.gate_version:
        return DriftReport(
            True,
            f"baseline was recorded under gate v{base.gate_version}, we are on "
            f"v{live.gate_version} — not comparable, rebuild to re-baseline",
            live=live,
            baseline=base,
        )

    if not live.differs_from(base):
        return DriftReport(False, "fingerprint unchanged", live=live, baseline=base)

    report = DriftReport(True, "fingerprint changed", live=live, baseline=base)

    # Only now — once we know something moved — is it worth pulling 5,700 names to say what.
    known = baseline.get("archive", {}).get("names")
    if known is None:
        report.revision_check = "baseline carries no name list"
        return report

    live_names = fetch_gated_names(use_cache=use_cache)
    before, after = set(known), set(live_names)
    report.added = sorted(after - before)
    report.removed = sorted(before - after)

    if not report.added and not report.removed:
        # Membership identical, numbers moved: unambiguously a revision.
        report.revisions = True
        report.revision_check = "same planets, different values"
        return report

    # Membership changed, so the sums moved for that reason alone — which tells us nothing yet
    # about whether existing rows were *also* revised. Settle it: add the new rows' values to the
    # baseline sums, subtract the departed ones, and see whether the result reconciles. Anything
    # left over is a genuine revision to a planet that was already there.
    report.revisions, report.revision_check = _residual_revisions(
        base, live, report.added, report.removed, use_cache=use_cache
    )
    return report


# Beyond this many changed rows the reconciliation query stops being cheap, and the answer stops
# mattering — a rebuild is obviously warranted either way.
_RECONCILE_LIMIT = 200


def _residual_revisions(
    base: Fingerprint,
    live: Fingerprint,
    added: list[str],
    removed: list[str],
    *,
    use_cache: bool = False,
) -> tuple[bool, str]:
    """Did anything change beyond the planets that joined or left?"""
    changed = added + removed
    if len(changed) > _RECONCILE_LIMIT:
        return False, f"{len(changed)} membership changes — too many to reconcile, not checked"
    try:
        added_sums = _sums_for(added, use_cache=use_cache)
        removed_sums = _sums_for(removed, use_cache=use_cache)
    except RuntimeError as exc:  # pragma: no cover - network shape
        return False, f"reconciliation query failed ({exc})"

    # Tolerance an order of magnitude looser than the rounding, so float noise across thousands
    # of summed values cannot masquerade as a revision.
    tol = 10.0 ** (-(_SUM_DECIMALS - 1))
    for col in FINGERPRINT_COLUMNS:
        expected = base.sums.get(col, 0.0) + added_sums.get(col, 0.0) - removed_sums.get(col, 0.0)
        if abs(expected - live.sums.get(col, 0.0)) > tol:
            return True, f"{col} does not reconcile from membership changes alone"
    return False, "sums reconcile from membership changes alone — no revisions detected"


def _sums_for(names: list[str], *, use_cache: bool = False) -> dict[str, float]:
    """Sum the fingerprint columns over an explicit set of planet names."""
    if not names:
        return dict.fromkeys(FINGERPRINT_COLUMNS, 0.0)
    quoted = ",".join("'" + n.replace("'", "''") + "'" for n in names)
    sums = ", ".join(f"sum({c}) as s_{c}" for c in FINGERPRINT_COLUMNS)
    rows = run_adql(
        f"select {sums} from {TABLE} where pl_name in ({quoted})", use_cache=use_cache
    )
    if not rows:
        raise RuntimeError("no rows for the reconciliation query")
    return {
        c: round(float(rows[0].get(f"s_{c}") or 0.0), _SUM_DECIMALS) for c in FINGERPRINT_COLUMNS
    }


@dataclass
class CatalogueDiff:
    """What actually changed between two built catalogues.

    The number a reviewer wants before merging is not "how many records were recomputed" — with
    `--no-cache` that is always all of them — but how many *colours moved*. This computes it by
    comparing the two artifacts directly, so the figure in a pull request is measured rather than
    inferred from build mechanics.
    """

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    recoloured: list[str] = field(default_factory=list)
    roman_changed: list[str] = field(default_factory=list)
    total_before: int = 0
    total_after: int = 0

    def summary(self) -> str:
        return (
            f"{self.total_before} -> {self.total_after} planets; "
            f"+{len(self.added)} / -{len(self.removed)}; "
            f"{len(self.recoloured)} changed true colour, "
            f"{len(self.roman_changed)} changed Roman colour"
        )


def _colours(path: Path) -> dict[str, tuple[str, str]]:
    data = json.loads(path.read_text())
    out: dict[str, tuple[str, str]] = {}
    for rec in data["planets"]:
        views = rec.get("instrument_views") or []
        roman = (views[0].get("colour", {}) or {}).get("hex", "") if views else ""
        out[rec["id"]] = ((rec.get("true_colour", {}) or {}).get("hex", ""), roman)
    return out


def diff_catalogues(before: Path, after: Path) -> CatalogueDiff:
    """Compare two planets.json artifacts by planet id and swatch."""
    old, new = _colours(before), _colours(after)
    diff = CatalogueDiff(total_before=len(old), total_after=len(new))
    diff.added = sorted(set(new) - set(old))
    diff.removed = sorted(set(old) - set(new))
    for pid in sorted(set(old) & set(new)):
        if old[pid][0] != new[pid][0]:
            diff.recoloured.append(pid)
        if old[pid][1] != new[pid][1]:
            diff.roman_changed.append(pid)
    return diff


def load_baseline(path: Path | None, *, tag: str | None = None) -> dict | None:
    """Read the baseline manifest from a local file, or fetch it from a GitHub release.

    Falls back to `gh` so the probe is runnable by hand exactly as CI runs it; returns None
    rather than raising when no baseline can be found, and `compare` treats that as drift.
    """
    if path is not None:
        return json.loads(path.read_text()) if path.exists() else None
    args = ["gh", "release", "download"]
    if tag:
        args.append(tag)
    try:
        with _temp_dir() as tmp:
            subprocess.run(
                [*args, "--pattern", "manifest.json", "--dir", str(tmp)],
                check=True,
                capture_output=True,
                timeout=120,
            )
            found = tmp / "manifest.json"
            return json.loads(found.read_text()) if found.exists() else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # No gh, not authenticated, or no release carries a manifest yet (every release before
        # this module existed). Not an error — just no baseline.
        return None


def _temp_dir():
    import tempfile
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    return _ctx()
