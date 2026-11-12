"""Compare the Archive's complete input rows with the release pinned in data/RELEASE.

Per-planet hashes detect metadata corrections and revisions that cancel in column sums.
A release manifest reuses the actual build inputs, never a newer live Archive snapshot.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline.catalog import CURATED_NAMES, gate_adql
from pipeline.config import PIPELINE_VERSION, SCHEMA_VERSION
from pipeline.fetch.archive import BULK_PREFILTER_ADQL, COLUMNS, TABLE, run_adql

GATE_VERSION = 1


@dataclass(frozen=True)
class Fingerprint:
    n: int
    rows: dict[str, str]
    gate_version: int = GATE_VERSION
    queried_at: str = ""

    def differs_from(self, other: Fingerprint) -> bool:
        return self.rows != other.rows


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
        if not self.drift:
            return "Catalogue: in sync with the Archive"
        if self.baseline is None:
            return f"Catalogue: {self.reason}"
        bits = []
        if self.added:
            bits.append(f"+{len(self.added)} planet{'s' if len(self.added) != 1 else ''}")
        if self.removed:
            bits.append(f"-{len(self.removed)} planet{'s' if len(self.removed) != 1 else ''}")
        if self.revisions:
            bits.append("values revised")
        return "Catalogue: " + (", ".join(bits) if bits else "Archive values changed")

    def to_json(self) -> str:
        payload = asdict(self)
        for key in ("live", "baseline"):
            if payload[key] is not None:
                del payload[key]["rows"]
        payload["headline"] = self.headline()
        return json.dumps(payload, indent=2, sort_keys=True)


def fingerprint_rows(rows: list[dict]) -> Fingerprint:
    hashes = {}
    for row in rows:
        values = {c: row[c] for c in COLUMNS}
        blob = json.dumps(values, sort_keys=True, separators=(",", ":"), allow_nan=False)
        name = row["pl_name"]
        if not isinstance(name, str) or not name or name in hashes:
            raise ValueError("Archive rows have an empty or duplicate planet name")
        hashes[name] = hashlib.sha256(blob.encode()).hexdigest()
    return Fingerprint(
        n=len(hashes), rows=hashes,
        queried_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
    )


def _gated_where() -> str:
    # Curated rows are pinned into bulk builds even when they have no distance.
    names = ",".join("'" + n.replace("'", "''") + "'" for n in CURATED_NAMES)
    return f"({BULK_PREFILTER_ADQL} or pl_name in ({names})) and {gate_adql()}"


def fetch_fingerprint(*, use_cache: bool = False) -> Fingerprint:
    rows = run_adql(
        f"select {','.join(COLUMNS)} from {TABLE} where {_gated_where()}",
        use_cache=use_cache,
    )
    return fingerprint_rows(rows)


def build_manifest(planets_json: Path) -> dict:
    data = json.loads(planets_json.read_text())
    snapshot = (data.get("provenance") or {}).get("archive_snapshot")
    if snapshot is None:
        raise ValueError("No build input snapshot; rebuild with pipeline build --bulk N first")
    fingerprint_from_manifest({"archive": {
        "gate_version": snapshot["gate_version"], "fingerprint": snapshot,
    }})
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "catalogue": {
            "planets": len(data["planets"]),
            "schema_version": data.get("schema_version", SCHEMA_VERSION),
            "pipeline_version": PIPELINE_VERSION,
        },
        "archive": {
            "table": TABLE,
            "gate_version": snapshot["gate_version"],
            "queried_at": snapshot["queried_at"],
            "fingerprint": {"n": snapshot["n"], "rows": snapshot["rows"]},
        },
    }


def fingerprint_from_manifest(manifest: dict) -> Fingerprint:
    arch = manifest["archive"]
    fp = arch["fingerprint"]
    rows = fp["rows"]
    if (not isinstance(rows, dict) or fp["n"] != len(rows)
            or any(not isinstance(name, str) or not name
                   or not isinstance(digest, str) or len(digest) != 64
                   for name, digest in rows.items())):
        raise ValueError("Invalid manifest row hashes or planet count")
    return Fingerprint(n=len(rows), rows=rows,
                       gate_version=int(arch.get("gate_version", 0)),
                       queried_at=str(arch.get("queried_at", "")))


def compare(baseline: dict | None, *, use_cache: bool = False) -> DriftReport:
    live = fetch_fingerprint(use_cache=use_cache)
    if baseline is None:
        return DriftReport(True, "no baseline manifest — rebuild to establish one", live=live)
    arch = baseline["archive"]
    if arch.get("gate_version", 0) != live.gate_version:
        return DriftReport(
            True, "baseline gate is not comparable — rebuild to re-baseline", live=live,
        )
    if "rows" not in arch["fingerprint"]:
        return DriftReport(True, "baseline has no row hashes — rebuild to migrate", live=live)
    base = fingerprint_from_manifest(baseline)
    if not live.differs_from(base):
        return DriftReport(False, "fingerprint unchanged", live=live, baseline=base)
    before, after = set(base.rows), set(live.rows)
    revised = any(base.rows[name] != live.rows[name] for name in before & after)
    return DriftReport(
        True, "input rows changed", live=live, baseline=base,
        added=sorted(after - before), removed=sorted(before - after), revisions=revised,
        revision_check="compared hashes of surviving planets",
    )


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


def load_baseline(path: Path | None, *, tag: str | None = None) -> dict:
    """Fetch the deployed baseline; operational failures must not look like first setup."""
    if path is not None:
        return json.loads(path.read_text())
    pinned = tag if tag is not None else Path("data/RELEASE").read_text().strip()
    if not pinned or pinned.startswith("-"):
        raise ValueError("data/RELEASE must name a release tag")
    with TemporaryDirectory() as tmp:
        subprocess.run(
            ["gh", "release", "download", pinned, "--pattern", "manifest.json", "--dir", tmp],
            check=True, capture_output=True, timeout=120,
        )
        return json.loads((Path(tmp) / "manifest.json").read_text())
