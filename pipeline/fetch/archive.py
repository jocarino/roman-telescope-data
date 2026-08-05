"""NASA Exoplanet Archive fetch via the TAP API (`pscomppars` table).

Batches queries and caches raw responses to `data/cache/` (the TAP API rate-limits).
No API key needed. Equilibrium temperature is frequently null in the Archive, so we provide
a fallback computed from stellar Teff, stellar radius and semi-major axis.
"""

from __future__ import annotations

import hashlib
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pipeline import provenance

_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
_CACHE_DIR = Path("data/cache")

# Columns we pull for every planet.
_COLUMNS = (
    "pl_name",
    "hostname",
    "pl_eqt",
    "pl_rade",
    "pl_bmasse",
    "pl_orbsmax",
    "pl_orbeccen",
    "st_teff",
    "st_rad",
    "st_spectype",
    "sy_dist",
    "ra",
    "dec",
    "sy_vmag",
    "disc_method",
    "disc_year",
    "disc_facility",
)

_R_SUN_IN_AU = 0.00465047  # solar radius in AU


@dataclass(frozen=True)
class ArchiveRecord:
    pl_name: str
    hostname: str | None
    pl_eqt: float | None
    pl_rade: float | None
    pl_bmasse: float | None
    pl_orbsmax: float | None
    pl_orbeccen: float | None
    st_teff: float | None
    st_rad: float | None
    st_spectype: str | None
    disc_method: str | None
    disc_year: int | None
    disc_facility: str | None
    sy_dist: float | None = None  # distance from Earth, parsecs (system distance)
    ra: float | None = None  # J2000 right ascension, degrees
    dec: float | None = None  # J2000 declination, degrees
    sy_vmag: float | None = None  # system V (Johnson) magnitude — how bright in our sky

    def equilibrium_temp_k(self, bond_albedo: float = 0.3) -> float | None:
        """Archive value if present, else compute from Teff, R_star and a.

        T_eq = T_star * sqrt(R_star / (2 a)) * (1 - A_bond)^(1/4)
        """
        if self.pl_eqt is not None:
            return self.pl_eqt
        return self.irradiation_temp_k(bond_albedo)

    def irradiation_temp_k(self, bond_albedo: float = 0.3) -> float | None:
        """The IRRADIATION equilibrium temperature, always computed from the star and orbit
        (never the archive pl_eqt). For most planets this equals pl_eqt, but for young,
        self-luminous *imaged* giants the archive pl_eqt reflects INTERNAL heat, not
        irradiation — e.g. HR 8799 b's pl_eqt is ~1200 K but at ~68 AU its irradiation temp is
        ~45 K. The reflected-light regime (clouds/chemistry we actually see) is set by
        irradiation, so this is the right temperature for engine routing. None if inputs missing.
        """
        if self.st_teff is None or self.st_rad is None or self.pl_orbsmax is None:
            return None
        if self.pl_orbsmax <= 0:
            return None
        r_star_au = self.st_rad * _R_SUN_IN_AU
        return (
            self.st_teff
            * math.sqrt(r_star_au / (2.0 * self.pl_orbsmax))
            * (1.0 - bond_albedo) ** 0.25
        )


def _adql_in_clause(names: list[str]) -> str:
    quoted = ",".join("'" + n.replace("'", "''") + "'" for n in names)
    cols = ",".join(_COLUMNS)
    return f"select {cols} from pscomppars where pl_name in ({quoted})"


# The coarse server-side filter the bulk pull applies before the completeness gate runs: a
# distance (needed to order by proximity) and some size measurement. Exported because the drift
# probe must count exactly the rows a bulk build would ingest — see `pipeline.drift`.
BULK_PREFILTER_ADQL = "sy_dist is not null and (pl_rade is not null or pl_bmasse is not null)"

TABLE = "pscomppars"


def _adql_bulk(limit: int) -> str:
    """The `limit` nearest planets (by distance) with the bare minimum to be worth considering:
    a size measurement (radius or mass) and a known distance to order by. Everything else — a
    real host-star temperature, a usable planet temperature — is left to the completeness gate
    downstream, so the gate does the real filtering and its keep/exclude ratio is meaningful."""
    cols = ",".join(_COLUMNS)
    return (
        f"select top {int(limit)} {cols} from {TABLE} "
        f"where {BULK_PREFILTER_ADQL} "
        "order by sy_dist asc"
    )


def _row_to_record(row: dict) -> ArchiveRecord:
    return ArchiveRecord(
        pl_name=row["pl_name"],
        hostname=row.get("hostname"),
        pl_eqt=row.get("pl_eqt"),
        pl_rade=row.get("pl_rade"),
        pl_bmasse=row.get("pl_bmasse"),
        pl_orbsmax=row.get("pl_orbsmax"),
        pl_orbeccen=row.get("pl_orbeccen"),
        st_teff=row.get("st_teff"),
        st_rad=row.get("st_rad"),
        st_spectype=row.get("st_spectype"),
        sy_dist=row.get("sy_dist"),
        ra=row.get("ra"),
        dec=row.get("dec"),
        sy_vmag=row.get("sy_vmag"),
        disc_method=row.get("disc_method"),
        disc_year=row.get("disc_year"),
        disc_facility=row.get("disc_facility"),
    )


def _cache_path(query: str) -> Path:
    digest = hashlib.sha256(query.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"tap_{digest}.json"


def _cache_meta_path(query: str) -> Path:
    """Sidecar recording WHEN a cached response was fetched. A cache hit must not inherit the
    build's timestamp — a rebuild today off a two-month-old cache is a two-month-old snapshot,
    and `pipeline.provenance` reports it as one. Kept beside the payload rather than wrapped
    around it so caches written before this existed stay readable."""
    return _cache_path(query).with_suffix(".meta.json")


def _cached_fetched_at(query: str, cache: Path) -> tuple[str, str]:
    """(timestamp, how we know it) for an existing cache entry."""
    meta = _cache_meta_path(query)
    if meta.exists():
        try:
            recorded = json.loads(meta.read_text()).get("fetched_at")
        except (OSError, json.JSONDecodeError):
            recorded = None
        if recorded:
            return str(recorded), provenance.FETCHED_AT_RECORDED
    try:
        mtime = datetime.fromtimestamp(cache.stat().st_mtime, UTC)
    except OSError:
        return "", provenance.FETCHED_AT_UNKNOWN
    return mtime.replace(microsecond=0).isoformat(), provenance.FETCHED_AT_CACHE_MTIME


def _run_query(query: str, *, use_cache: bool = True) -> list[dict]:
    cache = _cache_path(query)
    if use_cache and cache.exists():
        rows = json.loads(cache.read_text())
        fetched_at, source = _cached_fetched_at(query, cache)
        _record(query, rows, fetched_at=fetched_at, source=source, from_cache=True)
        return rows
    params = urllib.parse.urlencode(
        {"request": "doQuery", "lang": "ADQL", "format": "json", "query": query}
    )
    url = f"{_TAP_URL}?{params}"
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (trusted host)
        payload = json.loads(resp.read().decode())
    fetched_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload, indent=2))
    _cache_meta_path(query).write_text(
        json.dumps({"query": query, "fetched_at": fetched_at}, indent=2)
    )
    _record(
        query,
        payload,
        fetched_at=fetched_at,
        source=provenance.FETCHED_AT_RECORDED,
        from_cache=False,
    )
    return payload


def _record(
    query: str, rows: object, *, fetched_at: str, source: str, from_cache: bool
) -> None:
    """Hand the query to the provenance collector so it reaches the file header verbatim."""
    provenance.record_query(
        service=_TAP_URL,
        table=TABLE,
        adql=query,
        fetched_at=fetched_at,
        fetched_at_source=source,
        rows=len(rows) if isinstance(rows, list) else 0,
        from_cache=from_cache,
    )


def run_adql(query: str, *, use_cache: bool = False) -> list[dict]:
    """Run an arbitrary ADQL query against the Archive's TAP service and return its rows.

    Defaults to `use_cache=False`, the opposite of the record fetchers: callers of this are
    asking "what does the Archive say *right now*", and a cache hit would answer with whatever
    it said last time — silently, and forever.
    """
    return _run_query(query, use_cache=use_cache)


def fetch_by_names(names: list[str], *, use_cache: bool = True) -> list[ArchiveRecord]:
    """Fetch a batch of planets by exact `pl_name`. One TAP call, cached to disk."""
    rows = _run_query(_adql_in_clause(names), use_cache=use_cache)
    by_name = {row["pl_name"]: row for row in rows}
    return [_row_to_record(by_name[name]) for name in names if name in by_name]


def fetch_bulk(limit: int, *, use_cache: bool = True) -> list[ArchiveRecord]:
    """Fetch up to `limit` well-characterised planets (nearest first) for the scaled catalog.
    Coarse-filtered in ADQL; the completeness gate applies the real thresholds downstream."""
    rows = _run_query(_adql_bulk(limit), use_cache=use_cache)
    return [_row_to_record(row) for row in rows]
