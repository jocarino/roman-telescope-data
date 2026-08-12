"""The gallery's default order — the front door of the whole project.

Alphabetical is the obvious default and the wrong one. The catalogue's spread is genuinely
striking (deep cobalts, teals, a handful of golds), but sorted by name the first two screens are
"11 Comae Berenices b" and a wall of near-identical cream giants: the beige tail, first. Nobody
scrolls two thousand pixels to find out that it gets better.

So the default order is dealt, not sorted:

1. **A hue-diverse deal.** Every planet is grouped by colour family and the families are dealt
   from round-robin in hue order, best example of each first. The opening screens become one
   card of every colour the catalogue contains instead of nine hundred creams, and the rare
   families (21 golds, 3 reds, 2 pinks) are visible from the start rather than being
   statistically impossible to stumble on.
2. **And diverse *within* each family too.** Ordering a family by "best" alone deals its top
   three in a row as visual triplets — TRAPPIST-1 h, g and f are the same #ffaa56 to the eye,
   and three rounds of that look like a stuck grid, not a spread. So each family is walked
   farthest-point: after the best example, every next card is the one most unlike the cards
   already dealt from it. Any prefix of the gallery is then a spread of the whole catalogue.
3. **Then the solar-system anchors**, once the catalogue has introduced itself. Five worlds
   whose reflected-light spectra were really measured rather than modelled, run through exactly
   the same maths as every exoplanet here, coming out the colours we already know they are.
   They used to open the gallery, on the argument that this agreement is the reason to trust
   the other several thousand. The argument holds — but it is an argument, and made silently by
   five unlabelled cards it just reads as a site about the solar system. This one is about
   exoplanets, so the deal introduces those first and brings the anchors in a few rows down,
   as one run, still ordered outward from the Sun. The argument itself is made where it can
   be made in words: the "Start here: five worlds we can check" tour, linked from the grid.

The ordering is computed here, at build time, and shipped as one small integer per planet
(`c` in the gallery index). The browser only ever sorts by that integer, so there is exactly one
implementation of this rule and no chance of the build and the client disagreeing about it —
unlike the name sort, which is mirrored in two languages and has to be kept in step by hand.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np
from colour import XYZ_to_Lab

from pipeline.colour.family import FAMILY_ORDER, colour_family
from pipeline.models import PlanetRecord

#: Planets whose spectrum is a real measurement, not a model. These are the five solar-system
#: anchors — dealt in as a block partway down the order, not at the head of it. See the module
#: docstring for why they no longer lead.
ANCHOR_PROVENANCE = "measured-albedo"

# How many exoplanets are dealt before the anchors. The grid is `minmax(188px, 1fr)` tracks, so
# 24 cards is four full rows on a laptop and rather more on a phone: past the opening screen
# everywhere, which is the whole requirement — the site introduces itself with the planets it is
# actually about before showing anyone a world they could have looked up in an atlas. A count
# rather than "N rounds of the deal", because rounds scale with how many colour families happen
# to be populated and would quietly mean something different on a smaller catalogue.
_ANCHOR_AFTER_CARDS = 24

# How the "best example of this colour family" score is weighted. Chroma dominates: within a
# family, the vivid member is the one that shows what that family IS, and the washed-out one
# reads as another beige card. The rest are nudges, not overrides.
_CHROMA_FULL = 60.0  # Lab C* at which the chroma term saturates (very few planets reach it)
_W_LUM = 0.35  # a colour too dark to see on a card is a poor advertisement for its family
_W_BOOST = 0.50  # planets the site already treats as notable (fiction, Roman's own targets)
_W_NEAR = 0.25  # nearby worlds carry recognisable names and are the ones Roman could observe
_NEAR_PC = 25.0  # "next door", in parsecs
_LUM_FULL = 0.45  # luminance at which the brightness term saturates

# What a point of showcase score is worth, in ΔE units of novelty, when walking a family
# farthest-point. Roughly: a maximally vivid planet can jump ahead of one that is ~6 ΔE more
# unlike what has already been dealt — enough to break the near-ties that dominate a family of
# a thousand modelled giants, nowhere near enough to override real visual difference.
_SCORE_IN_DELTA_E = 6.0


def _lab(rec: PlanetRecord) -> np.ndarray:
    return np.asarray(XYZ_to_Lab(np.array(rec.true_colour.xyz)), dtype=float)


def _chroma(rec: PlanetRecord) -> float:
    """Lab C* of the planet's true colour — how far from grey it is, perceptually."""
    lab = _lab(rec)
    return float(math.hypot(float(lab[1]), float(lab[2])))


def _showcase_score(rec: PlanetRecord, boost: frozenset[str]) -> float:
    """How well this planet represents its colour family, as a 0-ish..2 score."""
    score = min(_chroma(rec) / _CHROMA_FULL, 1.0)
    score += _W_LUM * min((rec.true_colour.luminance_y or 0.0) / _LUM_FULL, 1.0)
    if rec.id in boost:
        score += _W_BOOST
    dist = rec.params.distance_pc
    if dist is not None and dist <= _NEAR_PC:
        score += _W_NEAR
    return score


def _anchor_key(rec: PlanetRecord) -> tuple[float, str]:
    """Outward from the Sun; anything without an orbit falls to the end of the anchors."""
    sma = rec.params.semi_major_axis_au
    return (sma if sma is not None else math.inf, rec.name)


def _spread(records: list[PlanetRecord], scores: dict[str, float]) -> list[PlanetRecord]:
    """Order one colour family so that every prefix is a spread of it, not a run of clones.

    A farthest-point walk over CIELAB: start from the best-scoring member, then repeatedly take
    whichever planet is furthest (ΔE76) from everything already taken, with its showcase score
    worth `_SCORE_IN_DELTA_E` as a nudge. Near-duplicate colours — and a modelled catalogue is
    full of them — sink to the back on their own, because their distance to an already-dealt
    twin is ~0.
    """
    if len(records) <= 2:
        return sorted(records, key=lambda r: (-scores[r.id], r.name.lower(), r.name))
    # Name is in the sort key so the seed, and every tie after it, is deterministic.
    pool = sorted(records, key=lambda r: (-scores[r.id], r.name.lower(), r.name))
    labs = np.array([_lab(r) for r in pool])
    bonus = np.array([scores[r.id] for r in pool]) * _SCORE_IN_DELTA_E
    taken = np.zeros(len(pool), dtype=bool)
    # Distance from each candidate to the nearest already-dealt card. Seeded at +inf so the
    # first pick is decided by score alone (pool is score-ordered, so that is pool[0]).
    nearest = np.full(len(pool), np.inf)
    out: list[PlanetRecord] = []
    for _ in range(len(pool)):
        value = np.where(taken, -np.inf, nearest + bonus)
        i = int(np.argmax(value))
        taken[i] = True
        out.append(pool[i])
        nearest = np.minimum(nearest, np.linalg.norm(labs - labs[i], axis=1))
    return out


def curated_order(
    records: Sequence[PlanetRecord], *, boost: Iterable[str] = ()
) -> list[PlanetRecord]:
    """The records in gallery-default order: a hue-diverse deal, with the anchors dealt in
    after the first `_ANCHOR_AFTER_CARDS` of it.

    `boost` names planet ids that deserve to lead their colour family where the physics leaves
    the choice open — the ones the site already tells stories about (a fiction reference, one of
    Roman's own tech-demo targets). It only reorders within a family; it never promotes a planet
    past a family that would otherwise come first.
    """
    boosted = frozenset(boost)
    anchors = sorted((r for r in records if r.provenance == ANCHOR_PROVENANCE), key=_anchor_key)
    anchor_ids = {r.id for r in anchors}

    # Group the rest by colour family, then order each family best-first and spread out (see
    # _spread). Everything downstream of here is deterministic — two builds of the same data
    # deal the same cards in the same order.
    grouped: dict[str, list[PlanetRecord]] = {}
    for rec in records:
        if rec.id in anchor_ids:
            continue
        grouped.setdefault(colour_family(tuple(rec.true_colour.srgb)), []).append(rec)
    scores = {r.id: _showcase_score(r, boosted) for r in records}
    by_family = {name: _spread(bucket, scores) for name, bucket in grouped.items()}

    # Deal one card from each family in turn, in the canonical hue order the filter chips use,
    # skipping families that have run out. Rare families are exhausted early and the tail
    # necessarily thins out to the big ones — but the opening screens, which are the whole point,
    # hold every colour the catalogue has.
    dealt: list[PlanetRecord] = []
    cursors = dict.fromkeys(FAMILY_ORDER, 0)
    remaining = sum(len(v) for v in by_family.values())
    while remaining:
        for name in FAMILY_ORDER:
            bucket = by_family.get(name)
            if not bucket:
                continue
            i = cursors[name]
            if i < len(bucket):
                dealt.append(bucket[i])
                cursors[name] = i + 1
                remaining -= 1

    # Slot the anchors in as one run. A catalogue smaller than the offset — every test fixture,
    # and nothing that ever ships — puts them last rather than back at the front.
    at = min(_ANCHOR_AFTER_CARDS, len(dealt))
    return [*dealt[:at], *anchors, *dealt[at:]]


def curated_ranks(records: Sequence[PlanetRecord], *, boost: Iterable[str] = ()) -> dict[str, int]:
    """Planet id -> its position in the curated order (0 = first card on the front page)."""
    return {rec.id: i for i, rec in enumerate(curated_order(records, boost=boost))}
