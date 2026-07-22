"""Validate + write data/planets.json."""

from __future__ import annotations

from pathlib import Path

from pipeline.config import GRID_ID, SCHEMA_VERSION
from pipeline.models import PlanetRecord, PlanetsFile

DEFAULT_OUT = Path("data/planets.json")


def write_planets(records: list[PlanetRecord], generated_at: str, out: Path = DEFAULT_OUT) -> Path:
    doc = PlanetsFile(
        schema_version=SCHEMA_VERSION,
        grid=GRID_ID,
        generated_at=generated_at,
        planets=records,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc.model_dump_json(indent=2))
    return out
