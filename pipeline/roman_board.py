"""The Roman target board — the project's namesake, and the one page that is waiting.

Roman's coronagraph is a technology demonstration: a shortlist of nearby giant planets it
could plausibly catch in reflected light. For those planets, and only those, the four-band
colour this site shows today can one day be replaced by a real measurement. This module turns
the curated shortlist in `data/roman-targets.json` into a board of slots, each holding what we
predict and — pointedly empty until the day it isn't — what Roman measured.

Same split as guided tours (pipeline/tours.py): the WORDS are curated and live in the JSON;
the PLANET DATA is re-joined against the planets.json of the moment on every build. Nothing
here is frozen, so the board cannot quietly start lying as the catalogue changes.

Two things this module deliberately computes rather than transcribes:

* **Maximum angular separation.** How far the planet can ever appear from its star, in
  milliarcseconds: `1000 · a / d` for semi-major axis in AU and distance in parsecs. This is
  the number that decides whether a coronagraph can see a planet at all, and both inputs are
  already on every record — so it is derived here instead of copied out of a paper's table,
  where a mistyped digit would live forever. It is a MAXIMUM: a real orbit is tilted and the
  planet moves, so being wide enough on paper is necessary, not sufficient.

* **Measured vs predicted.** A slot flips from predicted to measured when the record's own
  provenance says so — `measured-cgi`, set by the swap seam in pipeline/emit/build.py the
  moment a real photometry file lands (docs/roman-measured-data.md). No edit here, no edit to
  the template: drop the file, rebuild, and the empty half of the slot fills in.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.models import PlanetRecord

_DEFAULT_PATH = Path("data/roman-targets.json")

# The separation bar's span, in milliarcseconds. The targets run from 33 mas to about 1,100,
# so the scale is logarithmic — on a linear one the whole shortlist would pile up in the first
# third and the coronagraph's 150–450 mas annulus would be an unreadable sliver. The bounds sit
# clear of both extremes so no marker lands on an edge.
SCALE_MIN_MAS = 20.0
SCALE_MAX_MAS = 1600.0


def scale_pos(mas: float | None) -> float | None:
    """Position of a separation on the bar, 0–100 %. None passes through (no marker drawn)."""
    if not mas or mas <= 0:
        return None
    import math

    lo, hi = math.log10(SCALE_MIN_MAS), math.log10(SCALE_MAX_MAS)
    frac = (math.log10(mas) - lo) / (hi - lo)
    return round(100.0 * min(max(frac, 0.0), 1.0), 2)


@dataclass(frozen=True)
class TargetSlot:
    """One planet on the board: what we predict, and what Roman has measured (so far, nothing).

    `record` is None when the shortlist names a planet our catalogue does not carry. That slot
    stays on the board rather than being quietly dropped — an honest gap is more informative
    than a tidy list, and `absent_note` says why it is empty.
    """

    name: str
    catalog_id: str | None
    record: PlanetRecord | None
    #: Named by the source paper as accessible under every one of its three scenarios.
    all_scenarios: bool = False
    #: Hand-written note from the curated JSON, if any.
    note: str | None = None

    @property
    def modelled(self) -> bool:
        return self.record is not None

    @property
    def measured(self) -> bool:
        """True once real Roman photometry has been ingested for this planet."""
        return self.record is not None and self.record.provenance == "measured-cgi"

    @property
    def epoch(self) -> str | None:
        """The date Roman took the measurement, once there is one."""
        if self.record is None:
            return None
        for view in self.record.instrument_views:
            if view.band_samples.source == "measured":
                return view.band_samples.epoch
        return None

    @property
    def predicted_hex(self) -> str | None:
        """Our four-band prediction — what this site says Roman should report."""
        if self.record is None or not self.record.instrument_views:
            return None
        return self.record.instrument_views[0].colour.hex

    @property
    def true_hex(self) -> str | None:
        """The full-spectrum colour, for the "what Roman's filters cost" comparison."""
        return self.record.true_colour.hex if self.record is not None else None

    @property
    def measured_hex(self) -> str | None:
        """The colour reconstructed from REAL photometry, or None while the slot is empty."""
        return self.predicted_hex if self.measured else None

    @property
    def host(self) -> str | None:
        return self.record.host_star.name if self.record is not None else None

    @property
    def separation_mas(self) -> float | None:
        """Maximum angular separation from its star, in milliarcseconds — see module docstring.

        None when either input is missing; the board then shows no bar rather than a guess.
        """
        if self.record is None:
            return None
        a = self.record.params.semi_major_axis_au
        d = self.record.params.distance_pc
        if not a or not d:
            return None
        return 1000.0 * a / d

    @property
    def distance_ly(self) -> float | None:
        d = self.record.params.distance_pc if self.record is not None else None
        return round(d * 3.26156, 1) if d else None

    @property
    def bar_pos(self) -> float | None:
        """Where this planet's widest separation falls on the shared bar, 0–100 %."""
        return scale_pos(self.separation_mas)

    @property
    def reach(self) -> str:
        """Plain-English verdict on the geometry alone — never on whether Roman will look.

        "inside"/"beyond" describe where the planet can get to at its widest, which is the
        necessary condition for a coronagraph to separate it from its star. It is not a
        prediction: a tilted orbit, and a planet that spends most of its time nearer in, decide
        the rest. The source paper's access probabilities are what actually model that.
        """
        sep = self.separation_mas
        if sep is None:
            return "unknown"
        if sep < 150.0:
            return "inside"
        if sep > 450.0:
            return "beyond"
        return "within"


@dataclass(frozen=True)
class Board:
    mission: dict
    instrument: dict
    source: dict
    slots: list[TargetSlot]

    @property
    def n_targets(self) -> int:
        return len(self.slots)

    @property
    def n_modelled(self) -> int:
        return sum(1 for s in self.slots if s.modelled)

    @property
    def n_measured(self) -> int:
        """The headline number, and for now the honest answer is zero."""
        return sum(1 for s in self.slots if s.measured)

    @property
    def n_awaiting(self) -> int:
        return self.n_modelled - self.n_measured

    @property
    def any_measured(self) -> bool:
        return self.n_measured > 0

    @property
    def dark_hole_span(self) -> tuple[float, float]:
        """The coronagraph's working annulus as a (left %, width %) band on the shared bar."""
        lo = scale_pos(self.instrument.get("dark_hole_inner_mas")) or 0.0
        hi = scale_pos(self.instrument.get("dark_hole_outer_mas")) or 100.0
        return lo, hi - lo

    @property
    def n_within(self) -> int:
        """Modelled targets whose widest separation lands inside the working annulus."""
        return sum(1 for s in self.slots if s.modelled and s.reach == "within")


def load_document(path: Path = _DEFAULT_PATH) -> dict | None:
    """The curated board document. Missing file → no board page at all, never a broken build
    (same contract as tours and the fiction overlay)."""
    if not path.exists():
        return None
    return json.loads(path.read_text())


def resolve(records: list[PlanetRecord], path: Path = _DEFAULT_PATH) -> Board | None:
    """Join the curated shortlist onto this build's catalogue.

    Ordering is the board's argument, made structural: the three planets the source paper names
    as accessible under every scenario come first, then everything else by how wide it opens on
    the sky — which is the property that got it onto the list. Unmodelled slots sink to the
    bottom, where they read as the gaps they are.
    """
    doc = load_document(path)
    if doc is None:
        return None
    by_id = {r.id: r for r in records}
    slots = [
        TargetSlot(
            name=t["name"],
            catalog_id=t.get("catalog_id"),
            # A curated id that no longer resolves (a planet dropped from a later data release)
            # degrades to an unmodelled slot rather than raising — the catalogue is rebuilt
            # independently of this file.
            record=by_id.get(t["catalog_id"]) if t.get("catalog_id") else None,
            all_scenarios=bool(t.get("all_scenarios")),
            note=t.get("note"),
        )
        for t in doc.get("targets", [])
    ]
    slots.sort(
        key=lambda s: (
            not s.modelled,
            not s.all_scenarios,
            -(s.separation_mas or 0.0),
        )
    )
    return Board(
        mission=doc.get("mission", {}),
        instrument=doc.get("instrument", {}),
        source=doc.get("source", {}),
        slots=slots,
    )
