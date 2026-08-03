"""Validate + write data/planets.json."""

from __future__ import annotations

from pathlib import Path

from pipeline.config import GRID_ID, INSTRUMENTS, SCHEMA_VERSION, Instrument
from pipeline.models import BandpassHeader, InstrumentHeader, PlanetRecord, PlanetsFile
from pipeline.rights import RIGHTS

DEFAULT_OUT = Path("data/planets.json")


def _instrument_header(inst: Instrument) -> InstrumentHeader:
    """Snapshot an instrument definition into the file header. Bounds are emitted alongside
    centre + fractional width because `lo_nm`/`hi_nm` are what a reader actually needs to know
    whether a band falls inside the CIE range, and deriving them means re-implementing our
    top-hat convention."""
    return InstrumentHeader(
        id=inst.id,
        name=inst.name,
        mission=inst.mission,
        bands=[
            BandpassHeader(
                id=b.id,
                center_nm=b.center_nm,
                bandwidth_frac=b.bandwidth_frac,
                lo_nm=round(b.lo_nm, 3),
                hi_nm=round(b.hi_nm, 3),
                shape=b.shape,
                role=b.role,
            )
            for b in inst.bands
        ],
    )


def write_planets(records: list[PlanetRecord], generated_at: str, out: Path = DEFAULT_OUT) -> Path:
    doc = PlanetsFile(
        schema_version=SCHEMA_VERSION,
        grid=GRID_ID,
        generated_at=generated_at,
        instruments=[_instrument_header(i) for i in INSTRUMENTS.values()],
        rights=RIGHTS.as_dict(),
        planets=records,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc.model_dump_json(indent=2))
    return out
