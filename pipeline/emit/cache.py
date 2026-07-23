"""Incremental record cache: skip recomputing a planet whose modelling inputs are unchanged.

Keyed by a hash of the planet's inputs (params, engine, illuminant, instruments) plus the
pipeline + schema versions, so a version bump or any input change busts the entry. The heavy
providers (PICASO especially) are deterministic in their inputs, so a cache hit is exact. This
turns a re-run over N planets into "recompute only what changed", which is what makes scaling
past the curated set — 200, then more — practical instead of a full recompute every time.

Scope note: measured band-sample files and static observation data are not part of the key,
so bump PIPELINE_VERSION (or pass --no-cache) if those change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline.config import PIPELINE_VERSION, SCHEMA_VERSION, Instrument
from pipeline.emit.build import PlanetInput, build_record
from pipeline.models import PlanetRecord

_CACHE_DIR = Path("data/cache/records")


def _key(pin: PlanetInput, instruments: list[Instrument]) -> str:
    payload = {
        "id": pin.id,
        "name": pin.name,
        "params": pin.params.model_dump(),
        "host": pin.host_star.model_dump(),
        "discovery": pin.discovery.model_dump(),
        "is_light_isolable": pin.is_light_isolable,
        "is_cgi_target": pin.is_cgi_target,
        "instruments": [i.id for i in instruments],
        "pipeline_version": PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:20]


def cached_build_record(
    pin: PlanetInput,
    instruments: list[Instrument],
    generated_at: str,
    *,
    use_cache: bool = True,
) -> tuple[PlanetRecord, bool]:
    """Return (record, was_cache_hit). Rebuilds and caches on a miss or corrupt entry."""
    key = _key(pin, instruments)
    path = _CACHE_DIR / f"{pin.id}.{key}.json"
    if use_cache and path.exists():
        try:
            rec = PlanetRecord.model_validate_json(path.read_text())
            rec.meta.generated_at = generated_at  # keep the run's timestamp fresh
            return rec, True
        except Exception:  # noqa: BLE001 - a corrupt cache entry simply rebuilds
            pass
    rec = build_record(pin, instruments, generated_at)
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Drop stale entries for this planet (a different key) so the cache dir stays tidy.
    for old in _CACHE_DIR.glob(f"{pin.id}.*.json"):
        if old != path:
            old.unlink(missing_ok=True)
    path.write_text(rec.model_dump_json(indent=2))
    return rec, False
