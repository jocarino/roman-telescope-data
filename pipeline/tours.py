"""Guided tours — the editorial layer over the catalogue.

A tour is an ordered walk through a handful of planets with a plain-English reason for each
stop: "the ten strangest colours", "the darkest worlds", "planets of dead stars". It is meant
for someone who has never heard of an exoplanet, while staying true for someone who has.

Two halves, deliberately split:

* The **words** live in `data/tours.json` — hand-written titles, intros and honesty notes.
  That file is curated, kept out of planets.json, and never generated.
* The **planet lists** are resolved HERE, against the planets.json of the moment. A tour that
  claims to hold the ten darkest worlds would quietly start lying the first time the catalogue
  grew, so data-driven tours declare a `select` rule instead of a frozen list of ids, and get
  re-derived on every build. Tours whose membership is a genuine editorial choice (the five
  solar-system anchors) still list explicit ids.

Stop captions are generated from the record, so the reason a planet is on a tour is always the
data's reason, not a remembered one.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from colour import XYZ_to_Lab, delta_E

from pipeline.models import PlanetRecord

_DEFAULT_PATH = Path("data/tours.json")

# Light-years per parsec — distances are stored in parsecs, shown in light-years everywhere.
_LY_PER_PC = 3.26156


@dataclass(frozen=True)
class TourStop:
    """One planet on a tour, with the reason it earned its place."""

    planet: PlanetRecord
    #: Short mono readout of the quantity that put this planet on the tour ("ΔE 47", "4.5 %").
    metric: str
    #: Generated sentence explaining, in plain English, why this stop is here.
    caption: str
    #: Hand-written editorial note from tours.json (curated tours only).
    note: str | None = None
    #: Automatic honesty flag about the swatch itself (e.g. a colour a screen cannot show).
    caveat: str | None = None


@dataclass(frozen=True)
class Tour:
    id: str
    title: str
    kicker: str
    intro: str
    stops: list[TourStop]
    #: How the list was chosen, stated plainly on the page (honesty about curation).
    basis: str
    honesty: str | None = None
    epilogue: str | None = None

    @property
    def swatches(self) -> list[str]:
        return [s.planet.true_colour.hex for s in self.stops]


# ── colour helpers ────────────────────────────────────────────────────────────────────────
# CIELAB (via the stored XYZ) is the space to reason about "how different do these two colours
# look", which is what every colour-driven tour rule needs.


def _lab(rec: PlanetRecord) -> np.ndarray:
    return XYZ_to_Lab(np.array(rec.true_colour.xyz))


def _de(a: np.ndarray, b: np.ndarray) -> float:
    return float(delta_E(a, b, method="CIE 2000"))


def _labs(records: list[PlanetRecord]) -> dict[str, np.ndarray]:
    return {r.id: _lab(r) for r in records}


# ── plain-English physics ─────────────────────────────────────────────────────────────────


def colour_reason(rec: PlanetRecord, *, brief: bool = False) -> str:
    """One clause explaining what drives this planet's modelled colour, in plain English.

    Keyed off the archetype the pipeline assumed (cloud state) plus the host star, because
    those two are exactly what the colour computation used. `brief` drops the host-star clause,
    for tours that already say something about the star in their own words."""
    cloud = (rec.params.assumed_cloud_state or "").lower()
    teff = rec.host_star.teff_k
    if "ultra-hot" in cloud:
        base = (
            "it is too hot for clouds to survive, so almost nothing comes back; the little that "
            "does is blue light scattered off bare hydrogen, the way our own sky is blue"
        )
    elif "alkali" in cloud or "sodium" in cloud:
        base = "sodium vapour in its cloud-free air swallows the yellow out of the reflected light"
    elif "methane" in cloud:
        base = "methane in its cold air absorbs the red end of the spectrum, leaving blue-green"
    elif "rocky" in cloud:
        base = "a bare rocky surface hands its star's light back with barely any change"
    elif "temperate" in cloud or "partial cloud" in cloud:
        base = "bright water clouds scatter most of the starlight straight back"
    elif "as observed" in cloud:
        base = "its measured spectrum does the work — no archetype assumed"
    else:
        base = "its modelled atmosphere shapes the reflected light"

    if teff is not None and teff < 3000:
        # A very cool host emits almost nothing in the visible except red, so the reflected
        # colour is mostly the STAR's colour. Leading with the atmosphere here would read as a
        # contradiction — "methane leaves blue-green" beside an amber swatch.
        # Below ~2,400 K nothing fuses hydrogen: that is a brown dwarf, not a red dwarf.
        lead = (
            (
                f"its host is not a star at all but a brown dwarf at {round(teff):,} K, which "
                "puts out almost nothing except red and infrared light"
            )
            if teff < 2400
            else (
                f"its {round(teff):,} K red-dwarf sun puts out almost nothing except red and "
                "infrared light"
            )
        ) + ", so the colour owes more to the star than to the planet"
        return lead if brief else f"{lead}; underneath that, {base}"

    if brief or teff is None:
        return base
    if teff < 3900:
        return f"{base}, and its {round(teff):,} K red-dwarf sun tilts the whole colour warmer"
    if teff > 7000:
        return f"{base}, and its {round(teff):,} K blue-white sun pushes it cooler"
    return base


def _gamut_caveat(rec: PlanetRecord) -> str | None:
    """Roughly a third of modelled colours land outside sRGB. The swatch is then the nearest
    colour a screen can show, and saying so is the difference between a swatch and a claim."""
    if not rec.true_colour.out_of_gamut:
        return None
    return (
        "This colour falls outside the range a screen can display — the swatch is the closest "
        "your screen can get."
    )


def _size_temp(rec: PlanetRecord) -> str:
    """"a 12.9 R⊕ giant at 2,470 K" — the two numbers that most shape a reflected-light colour."""
    r = rec.params.radius_r_earth
    t = rec.params.equilibrium_temp_k
    article = "an" if r and f"{r:.1f}".startswith(("8", "11", "18")) else "a"
    size = f"{article} {r:.1f} R⊕ world" if r else "a world"
    return f"{size} at {round(t):,} K" if t else size


def _ly(rec: PlanetRecord) -> float | None:
    d = rec.params.distance_pc
    return round(d * _LY_PER_PC, 1) if d else None


def _pct(rec: PlanetRecord) -> str:
    return f"{rec.true_colour.luminance_y * 100:.1f} %"


def _roman_de(rec: PlanetRecord) -> float | None:
    view = rec.instrument_views[0] if rec.instrument_views else None
    err = view.reconstruction_error if view else None
    return err.delta_e2000 if err else None


# ── selection rules ───────────────────────────────────────────────────────────────────────
# Each rule returns the ordered planets for a tour. Rules never invent membership: they sort
# or filter the catalogue on a stated quantity, so the page can say exactly how it was picked.


def _one_per_host(records: list[PlanetRecord]) -> list[PlanetRecord]:
    """Keep the first planet of each host system. Without this, "the nearest worlds" is four
    Barnard's Star planets and the walk stops feeling like a walk."""
    seen: set[str] = set()
    out: list[PlanetRecord] = []
    for r in records:
        if r.host_star.name in seen:
            continue
        seen.add(r.host_star.name)
        out.append(r)
    return out


def _rule_colour_outliers(
    records: list[PlanetRecord], *, limit: int = 10, min_separation_de: float = 9.0
) -> list[TourStop]:
    """Furthest from the catalogue's median colour — but each stop also has to look different
    from the ones already picked, or the "ten strangest" is ten near-identical amber worlds
    around ten different red dwarfs."""
    labs = _labs(records)
    median = np.median(np.stack(list(labs.values())), axis=0)
    ranked = sorted(records, key=lambda r: -_de(labs[r.id], median))
    chosen: list[PlanetRecord] = []
    hosts: set[str] = set()
    for rec in ranked:
        if rec.host_star.name in hosts:
            continue
        if any(_de(labs[rec.id], labs[c.id]) < min_separation_de for c in chosen):
            continue
        chosen.append(rec)
        hosts.add(rec.host_star.name)
        if len(chosen) == limit:
            break
    return [
        TourStop(
            planet=rec,
            metric=f"ΔE {_de(labs[rec.id], median):.0f} from average",
            caption=(
                f"Its modelled colour sits ΔE {_de(labs[rec.id], median):.0f} from the "
                f"catalogue's median — {colour_reason(rec)}."
            ),
            caveat=_gamut_caveat(rec),
        )
        for rec in chosen
    ]


def _rule_dimmest(records: list[PlanetRecord], *, limit: int = 10) -> list[TourStop]:
    ranked = _one_per_host(sorted(records, key=lambda r: r.true_colour.luminance_y))[:limit]
    return [
        TourStop(
            planet=rec,
            metric=f"{_pct(rec)} reflected",
            caption=(
                f"Reflects only {_pct(rec)} of the light that reaches it: {_size_temp(rec)}, "
                f"where {colour_reason(rec, brief=True)}."
            ),
            caveat=_gamut_caveat(rec),
        )
        for rec in ranked
    ]


def _rule_roman_gap(records: list[PlanetRecord], *, limit: int = 10) -> list[TourStop]:
    """Where Roman's four bands land furthest from the full-spectrum colour."""
    with_de = [(r, _roman_de(r)) for r in records]
    ranked = _one_per_host(
        [r for r, de in sorted(with_de, key=lambda p: -(p[1] or 0.0)) if de is not None]
    )[:limit]
    stops = []
    for rec in ranked:
        de = _roman_de(rec) or 0.0
        roman_hex = rec.instrument_views[0].colour.hex
        stops.append(
            TourStop(
                planet=rec,
                metric=f"ΔE {de:.0f} lost",
                caption=(
                    f"Full spectrum says {rec.true_colour.hex}; Roman's four bands reconstruct "
                    f"{roman_hex} — ΔE {de:.0f} apart, which the eye reads as a different colour "
                    "altogether. The features that carry its colour fall mostly between Roman's "
                    f"four filters, because {colour_reason(rec, brief=True)}."
                ),
                caveat=_gamut_caveat(rec),
            )
        )
    return stops


def _rule_nearest(records: list[PlanetRecord], *, limit: int = 10) -> list[TourStop]:
    """Closest first, exoplanets only. The solar-system anchors sit a few ten-thousandths of a
    parsec away and would otherwise take the first five places — they have their own tour."""
    candidates = [
        r for r in records if r.params.distance_pc and r.host_star.name.lower() != "sun"
    ]
    ranked = _one_per_host(sorted(candidates, key=lambda r: r.params.distance_pc or 0.0))[:limit]
    stops = []
    for i, rec in enumerate(ranked):
        ly = _ly(rec)
        where = f", in {rec.sky.constellation}" if rec.sky else ""
        lead = (
            "The closest known planet outside the solar system: "
            if i == 0
            else f"{ly:,.1f} light-years away{where}. "
        )
        stops.append(
            TourStop(
                planet=rec,
                metric=f"{ly:,.1f} ly" if ly else "distance n/a",
                caption=(
                    f"{lead}{ly:,.1f} light-years{where}, orbiting {rec.host_star.name}. "
                    f"Its modelled colour: {colour_reason(rec)}."
                    if i == 0
                    else f"{lead}It orbits {rec.host_star.name}; {colour_reason(rec)}."
                ),
                caveat=_gamut_caveat(rec),
            )
        )
    return stops


def _is_white_dwarf(rec: PlanetRecord) -> bool:
    """White-dwarf hosts carry a spectral type in the D-sequence (DA/DB/DC/DQ/DZ) or a WD
    catalogue designation. Note the deliberate absence of pulsars and hot subdwarfs: the
    catalogue's completeness gate drops hosts above 12,000 K, whose light is UV-dominated and
    whose "reflected visible colour" would be meaningless."""
    stype = (rec.host_star.spectral_type or "").strip()
    if stype[:1] == "D" and stype[:2] not in {"DA?"}:
        return True
    return rec.host_star.name.upper().startswith(("WD ", "GD ", "LP 40-"))


def _rule_remnant_hosts(records: list[PlanetRecord], *, limit: int = 10) -> list[TourStop]:
    ranked = sorted(
        (r for r in records if _is_white_dwarf(r)),
        key=lambda r: r.host_star.teff_k or 0.0,
        reverse=True,
    )[:limit]
    stops = []
    for rec in ranked:
        teff = rec.host_star.teff_k
        stops.append(
            TourStop(
                planet=rec,
                metric=f"host {round(teff):,} K" if teff else "white dwarf host",
                caption=(
                    f"Its sun is a white dwarf: an Earth-sized cinder of a burnt-out star, still "
                    f"glowing at {round(teff):,} K off leftover heat with no fuel left to burn. "
                    f"The planet's modelled colour comes from that dying light: "
                    f"{colour_reason(rec, brief=True)}."
                ),
                caveat=_gamut_caveat(rec),
            )
        )
    return stops


def _rule_blue_two_ways(records: list[PlanetRecord], *, limit: int = 8) -> list[TourStop]:
    """Alternate cold methane blues with ultra-hot cloud-free blues: the same colour arrived at
    from opposite physics, walked side by side."""
    labs = _labs(records)

    def bluest(pred: Callable[[PlanetRecord], bool]) -> list[PlanetRecord]:
        return _one_per_host(
            sorted((r for r in records if pred(r)), key=lambda r: labs[r.id][2])
        )

    cold = bluest(lambda r: "methane" in (r.params.assumed_cloud_state or "").lower())
    hot = bluest(lambda r: "ultra-hot" in (r.params.assumed_cloud_state or "").lower())
    order: list[PlanetRecord] = []
    for i in range(limit):
        pool = cold if i % 2 == 0 else hot
        idx = i // 2
        if idx < len(pool):
            order.append(pool[idx])
    stops = []
    for rec in order:
        methane = "methane" in (rec.params.assumed_cloud_state or "").lower()
        stops.append(
            TourStop(
                planet=rec,
                metric="cold · methane" if methane else "ultra-hot · cloud-free",
                caption=(
                    (
                        f"A cold world, {round(rec.params.equilibrium_temp_k or 0):,} K: "
                        if methane
                        else f"A furnace, {round(rec.params.equilibrium_temp_k or 0):,} K: "
                    )
                    + colour_reason(rec)
                    + "."
                ),
                caveat=_gamut_caveat(rec),
            )
        )
    return stops


_RULES: dict[str, Callable[..., list[TourStop]]] = {
    "colour-outliers": _rule_colour_outliers,
    "dimmest": _rule_dimmest,
    "roman-gap": _rule_roman_gap,
    "nearest": _rule_nearest,
    "remnant-hosts": _rule_remnant_hosts,
    "blue-two-ways": _rule_blue_two_ways,
}


def _explicit_stops(defn: dict, by_id: dict[str, PlanetRecord]) -> list[TourStop]:
    """Curated tours: the ids ARE the editorial choice. Ids missing from this data release are
    dropped rather than fatal — the catalogue is rebuilt independently of this file."""
    stops = []
    for raw in defn.get("stops", []):
        entry = {"id": raw} if isinstance(raw, str) else raw
        rec = by_id.get(entry["id"])
        if rec is None:
            continue
        stops.append(
            TourStop(
                planet=rec,
                metric=entry.get("metric", ""),
                caption=entry.get("caption") or colour_reason(rec).capitalize() + ".",
                note=entry.get("note"),
                caveat=_gamut_caveat(rec),
            )
        )
    return stops


def load_definitions(path: Path = _DEFAULT_PATH) -> list[dict]:
    """Raw tour definitions from the curated JSON. Missing file → no tours (the site builds
    fine without them)."""
    if not path.exists():
        return []
    doc = json.loads(path.read_text())
    return [t for t in doc.get("tours", []) if not t.get("draft")]


def resolve(
    records: list[PlanetRecord], path: Path = _DEFAULT_PATH, *, min_stops: int = 2
) -> list[Tour]:
    """Turn the curated definitions plus the current catalogue into rendered-ready tours.

    A tour whose rule finds fewer than `min_stops` planets is dropped: a "tour" of one planet
    is a link, and shipping an empty one would be a broken promise on the index page."""
    # Every rule reasons about colour, and `true_colour` is optional on the model (a record can
    # in principle carry parameters but no computed colour) — filter once, here.
    records = [r for r in records if r.true_colour is not None]
    by_id = {r.id: r for r in records}
    tours: list[Tour] = []
    for defn in load_definitions(path):
        select = defn.get("select")
        if select:
            rule = _RULES.get(select["rule"])
            if rule is None:
                raise ValueError(f"tour {defn['id']}: unknown select rule {select['rule']!r}")
            opts = {k: v for k, v in select.items() if k != "rule"}
            stops = rule(records, **opts)
            # Hand-written notes can still be attached to a rule-picked planet by id.
            notes = {n["id"]: n["note"] for n in defn.get("notes", [])}
            stops = [
                TourStop(s.planet, s.metric, s.caption, notes.get(s.planet.id), s.caveat)
                for s in stops
            ]
        else:
            stops = _explicit_stops(defn, by_id)
        if len(stops) < min_stops:
            continue
        tours.append(
            Tour(
                id=defn["id"],
                title=defn["title"],
                kicker=defn["kicker"],
                intro=defn["intro"],
                basis=defn["basis"],
                honesty=defn.get("honesty"),
                epilogue=defn.get("epilogue"),
                stops=stops,
            )
        )
    return tours
