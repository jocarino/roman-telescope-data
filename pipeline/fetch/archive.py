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
from pathlib import Path

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

    def equilibrium_temp_k(self, bond_albedo: float = 0.3) -> float | None:
        """Archive value if present, else compute from Teff, R_star and a.

        T_eq = T_star * sqrt(R_star / (2 a)) * (1 - A_bond)^(1/4)
        """
        if self.pl_eqt is not None:
            return self.pl_eqt
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


def _cache_path(query: str) -> Path:
    digest = hashlib.sha256(query.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"tap_{digest}.json"


def _run_query(query: str, *, use_cache: bool = True) -> list[dict]:
    cache = _cache_path(query)
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    params = urllib.parse.urlencode(
        {"request": "doQuery", "lang": "ADQL", "format": "json", "query": query}
    )
    url = f"{_TAP_URL}?{params}"
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (trusted host)
        payload = json.loads(resp.read().decode())
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload, indent=2))
    return payload


def fetch_by_names(names: list[str], *, use_cache: bool = True) -> list[ArchiveRecord]:
    """Fetch a batch of planets by exact `pl_name`. One TAP call, cached to disk."""
    rows = _run_query(_adql_in_clause(names), use_cache=use_cache)
    by_name = {row["pl_name"]: row for row in rows}
    records: list[ArchiveRecord] = []
    for name in names:
        row = by_name.get(name)
        if row is None:
            continue
        records.append(
            ArchiveRecord(
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
                disc_method=row.get("disc_method"),
                disc_year=row.get("disc_year"),
                disc_facility=row.get("disc_facility"),
            )
        )
    return records
