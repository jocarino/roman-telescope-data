"""Related-planet rails: the interior structure of the catalogue's link graph.

The colour hubs (web/hubs.py) put every planet back in the crawlable graph — one static link
each, from the tail list of its family's hub. That fixed reachability and nothing else: a
crawl of the full build shows all 5,764 planet pages reachable, but 3,245 of them with exactly
one inbound link, and that link sitting somewhere inside a page carrying up to 1,830 anchors.
Technically not an orphan; practically close to one, and a dead end for a reader too — the only
way onward from a planet was back to a 1,800-item index.

These rails add interior edges: from each planet to a handful of others that are related for a
stated reason. Three rails, each a *ring* rather than a nearest-neighbour list, which is the
load-bearing choice here:

    nearest-neighbour is asymmetric — B can be A's closest match while A is nobody's, so some
    planets gain no inbound links at all and the tail stays as thin as it was. A ring is
    symmetric by construction: order a bucket, and each member links to the k on either side
    of it. If B is A's next-along, A is B's previous-along, so every planet ends with exactly
    as many inbound links as outbound, no matter how the colours happen to be distributed.

That property is what tests/test_related.py pins, and it is why the counts are predictable
instead of emergent.

Rails are labelled in plain English ("Closest in colour", not "ΔE neighbours") per the
dual-audience rule in CLAUDE.md — each says what the relation is, so a newcomer can tell why
these four planets are sitting at the bottom of the page.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

from pipeline.classify import planet_type
from pipeline.models import PlanetRecord

# Neighbours per side, per rail. Colour gets the widest ring: it is the one relation this whole
# site is about, and the one a reader is most likely to want another example of.
RING = {"colour": 2, "kind": 1, "sky": 1}


@dataclass(frozen=True)
class RelatedPlanet:
    id: str
    name: str
    hex: str
    note: str  # the shared attribute, shown on hover: "1,204 K", "Pegasus", the hex itself


@dataclass(frozen=True)
class RelatedRail:
    key: str
    label: str
    blurb: str  # one plain sentence: what these planets have in common with this one
    planets: list[RelatedPlanet]


def _colour_key(rec: PlanetRecord) -> tuple[float, float, str]:
    """Order a colour family by hue, then lightness. Adjacent in this order means adjacent to
    the eye, which is what makes the ring's neighbours a real answer to 'more like this one'."""
    r, g, b = (c / 255.0 for c in rec.true_colour.srgb)
    h, lightness, _ = colorsys.rgb_to_hls(r, g, b)
    return (round(h, 4), round(lightness, 4), rec.name)


def _kind(rec: PlanetRecord) -> str:
    return planet_type(
        rec.params.radius_r_earth, rec.params.mass_m_earth, rec.params.equilibrium_temp_k
    )


def _temp_key(rec: PlanetRecord) -> tuple[float, str]:
    # Unmeasured temperatures sort to the end rather than to 0 K, where they would sit among
    # the coldest worlds and claim a similarity the data does not support.
    return (rec.params.equilibrium_temp_k or float("inf"), rec.name)


def _ring_neighbours(ordered: list[str], k: int) -> dict[str, list[str]]:
    """Each element linked to the k on either side of it, wrapping at the ends.

    Symmetric by construction, and duplicate-free for short rings: a bucket of three with k=2
    would otherwise list each neighbour twice via the wrap.
    """
    n = len(ordered)
    if n < 2:
        return {item: [] for item in ordered}
    out: dict[str, list[str]] = {}
    for i, item in enumerate(ordered):
        picked: list[str] = []
        seen = {item}
        # Alternate sides so a truncated ring stays balanced rather than all-forward.
        for offset in range(1, k + 1):
            for j in (i + offset, i - offset):
                other = ordered[j % n]
                if other not in seen:
                    seen.add(other)
                    picked.append(other)
        out[item] = picked
    return out


def _bucket(records: list[PlanetRecord], key) -> dict[str, list[PlanetRecord]]:
    buckets: dict[str, list[PlanetRecord]] = {}
    for rec in records:
        name = key(rec)
        if name is not None:
            buckets.setdefault(name, []).append(rec)
    return buckets


def build_related(records: list[PlanetRecord]) -> dict[str, list[RelatedRail]]:
    """Rails for every planet, keyed by planet id. Deterministic: same data, same links."""
    from pipeline.colour.family import colour_family

    by_id = {rec.id: rec for rec in records}
    # Siblings already have their own strip higher up the page. Listing them again here would
    # spend a rail on a link the reader has just been given. Dropped symmetrically (the sibling
    # relation is mutual), so the ring's reciprocity survives the exclusion.
    siblings = {
        rec.id: {s.id for s in rec.system.siblings} if rec.system else set() for rec in records
    }

    rails: dict[str, dict[str, list[str]]] = {}
    rails["colour"] = _merge(
        _bucket(records, lambda r: colour_family(tuple(r.true_colour.srgb))),
        sort_key=_colour_key,
        k=RING["colour"],
    )
    rails["kind"] = _merge(_bucket(records, _kind), sort_key=_temp_key, k=RING["kind"])
    rails["sky"] = _merge(
        _bucket(records, lambda r: r.sky.constellation if r.sky else None),
        sort_key=lambda r: (r.sky.ra_deg, r.name),
        k=RING["sky"],
    )

    notes = {
        "colour": lambda r: r.true_colour.hex,
        "kind": lambda r: (
            f"{r.params.equilibrium_temp_k:,.0f} K" if r.params.equilibrium_temp_k else "—"
        ),
        "sky": lambda r: r.sky.constellation if r.sky else "—",
    }
    labels = {
        "colour": ("Closest in colour", "The nearest colours to this one in the whole catalogue."),
        "kind": ("Same kind of world", "Planets of the same size class at a similar temperature."),
        "sky": ("Next in the sky", "Other worlds in the same constellation, seen from Earth."),
    }

    out: dict[str, list[RelatedRail]] = {}
    for rec in records:
        used = set(siblings[rec.id]) | {rec.id}
        built: list[RelatedRail] = []
        for key in ("colour", "kind", "sky"):
            # Dedupe across rails as well as within one: a planet that is both the closest
            # colour and the nearest in the sky is one link, on the rail that explains it best.
            # Both operations are symmetric, so this cannot break the ring's reciprocity.
            picked = [i for i in rails[key].get(rec.id, ()) if i not in used]
            used |= set(picked)
            if not picked:
                continue
            label, blurb = labels[key]
            built.append(
                RelatedRail(
                    key=key,
                    label=label,
                    blurb=blurb,
                    planets=[
                        RelatedPlanet(
                            id=by_id[i].id,
                            name=by_id[i].name,
                            hex=by_id[i].true_colour.hex,
                            note=notes[key](by_id[i]),
                        )
                        for i in picked
                    ],
                )
            )
        out[rec.id] = built
    return out


def _merge(buckets: dict[str, list[PlanetRecord]], sort_key, k: int) -> dict[str, list[str]]:
    """Ring each bucket independently, then flatten to one id -> neighbour-ids map."""
    merged: dict[str, list[str]] = {}
    for members in buckets.values():
        ordered = [rec.id for rec in sorted(members, key=sort_key)]
        merged.update(_ring_neighbours(ordered, k))
    return merged


def rail_stats(related: dict[str, list[RelatedRail]]) -> dict[str, int]:
    """Build-time summary, printed by the build so a regression is visible in the log."""
    counts = [sum(len(rail.planets) for rail in rails) for rails in related.values()]
    return {
        "planets": len(counts),
        "links": sum(counts),
        "min_per_planet": min(counts, default=0),
        "max_per_planet": max(counts, default=0),
    }


__all__ = [
    "RING",
    "RelatedPlanet",
    "RelatedRail",
    "build_related",
    "rail_stats",
]
