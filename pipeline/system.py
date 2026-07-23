"""Group built records into stellar systems and attach each planet's siblings.

A batch-level pass (needs every record to see who shares a host), deliberately separate from
the per-planet `build_record`. Grouping is by shared host star only — physically meaningful
and unambiguous — never by sky proximity. Works for any dataset size; with only one planet
per host (the common case) every `siblings` list is simply empty.
"""

from __future__ import annotations

from collections import defaultdict

from pipeline.models import PlanetRecord, PlanetSystem, SystemSibling


def _letter(name: str) -> str | None:
    """The trailing planet letter of a name ("HR 8799 b" -> "b"), if it has one."""
    tail = name.rsplit(" ", 1)[-1]
    return tail if len(tail) == 1 and tail.isalpha() else None


def _sort_key(rec: PlanetRecord) -> tuple[int, float, str]:
    """Inner → outer by semi-major axis; planets with no axis sink to the end, then by name
    so the order is stable and deterministic."""
    a = rec.params.semi_major_axis_au
    return (0, a, rec.name) if a is not None else (1, 0.0, rec.name)


def _sibling(rec: PlanetRecord) -> SystemSibling:
    return SystemSibling(
        id=rec.id,
        name=rec.name,
        letter=_letter(rec.name),
        semi_major_axis_au=rec.params.semi_major_axis_au,
        base_hex=rec.true_colour.hex if rec.true_colour else None,
    )


def attach_systems(records: list[PlanetRecord]) -> None:
    """Populate `record.system` for every record, in place, by grouping on host-star name."""
    by_host: dict[str, list[PlanetRecord]] = defaultdict(list)
    for rec in records:
        by_host[rec.host_star.name].append(rec)

    for rec in records:
        group = by_host[rec.host_star.name]
        siblings = sorted((r for r in group if r.id != rec.id), key=_sort_key)
        rec.system = PlanetSystem(
            hostname=rec.host_star.name,
            member_count=len(group),
            siblings=[_sibling(r) for r in siblings],
        )
