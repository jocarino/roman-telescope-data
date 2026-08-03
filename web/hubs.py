"""Colour-family hub pages: the crawlable spine of the catalogue.

The gallery is an infinite-scroll grid built in JS, so its planet links do not exist in the
served HTML — a crawler that renders but does not scroll sees the first batch and nothing else.
Before these pages, static `<a href>` into /planet/ existed only on the seven tour pages, the
Roman board's slots, one link on /how and the same-system sibling strip: order of a hundred
planets in the link graph, and roughly 97% of the catalogue reachable only from sitemap.xml —
which is itself skipped entirely when the build has no --base-url.

One page per colour family fixes that without a link dump. Each hub carries the family's real
count, the physics of why planets land in it, a representative set as cards, and then every
remaining member as a plain anchor. So every planet is two clicks from the front page, on a page
that has a reason to exist for a reader as well as a crawler.

The families themselves are NOT invented here: `pipeline.colour.family.colour_family` already
buckets every planet for the gallery's colour filter, and these pages are that same partition
made addressable. Nothing is hand-assigned, so a hub cannot disagree with the chip it mirrors.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.colour.family import FAMILY_ORDER, colour_family
from pipeline.models import PlanetRecord

# Plain-English display names. Two families are lightness buckets rather than hues, so their
# names have to hedge — "white planets" would claim a hue the bucket does not assert.
FAMILY_LABEL = {
    "teal": "Teal",
    "azure": "Azure",
    "blue": "Blue",
    "periwinkle": "Periwinkle",
    "green": "Green",
    "gold": "Gold",
    "orange": "Orange",
    "red": "Red",
    "pink": "Pink",
    "violet": "Violet",
    "brown": "Brown",
    "grey": "Grey",
    "white": "Near-white",
    "dark": "Near-black",
}

# Why a modelled planet lands in each bucket. These describe the physics the pipeline actually
# encodes -- albedo spectrum times host-star spectrum -- and deliberately stop short of claiming
# any individual planet has been observed to be this colour.
FAMILY_WHY = {
    "teal": (
        "Methane absorbs strongly at the red end of the visible, so a cool, methane-rich "
        "atmosphere returns the blue-green half of the spectrum and swallows the rest. This is "
        "the Neptune signature, and it is the clearest case in the catalogue of a colour that "
        "comes from a named molecule rather than from the star."
    ),
    "azure": (
        "Rayleigh scattering — the same physics that makes Earth's sky blue — sends short "
        "wavelengths back preferentially from a clear atmosphere. Where there is little cloud "
        "and little red absorption, what returns is dominated by the blue end."
    ),
    "blue": (
        "A deep blue needs both strong red absorption and something to scatter the blue back. "
        "The one exoplanet whose colour has actually been measured, HD 189733 b, is a deep "
        "cobalt widely attributed to silicate cloud particles — everything else in this family "
        "is modelled, not observed."
    ),
    "periwinkle": (
        "Pale blue-violet: Rayleigh scattering diluted by a bright cloud deck, so the blue "
        "preference survives but the colour is washed toward white."
    ),
    "green": (
        "Rare, and it has to be earned: green needs absorption at both ends of the visible with "
        "a window left open in the middle. Few modelled atmospheres do that, which is why this "
        "family is one of the smallest."
    ),
    "gold": (
        "Thick, bright cloud decks reflect most of what falls on them, so the planet returns "
        "close to its star's own light with a mild warm slope. Jupiter sits here — and Jupiter "
        "is one of the five worlds on this site whose spectrum was really measured."
    ),
    "orange": (
        "A bright reflector under a cooler star. The atmosphere is doing less of the work here "
        "than the illuminant is: swap the host for the Sun and much of the orange goes with it."
    ),
    "red": (
        "Either strong absorption at the blue end, or a very cool host star whose own light is "
        "already red. The 'Light source' knob on each planet page separates the two."
    ),
    "pink": (
        "Bright cloud under a cool star: enough reflectance to stay pale, enough of the star's "
        "warmth to pull away from neutral."
    ),
    "violet": (
        "Unusual — blue scattering with a red tail surviving underneath it, so the result lands "
        "between the two rather than at either end."
    ),
    "brown": (
        "Dim and warm: an absorbing haze over a modest cloud deck returns little light, and what "
        "does come back is weighted red."
    ),
    "grey": (
        "A flat albedo spectrum reflects the star's light back with almost no modification, so "
        "the planet takes the star's colour and little else. Grey is the honest answer for a "
        "great many worlds whose atmospheres the model cannot distinguish."
    ),
    "white": (
        "A thick, bright, spectrally flat cloud deck reflects nearly everything, nearly evenly. "
        "This is a lightness bucket, not a hue — these planets are near-white rather than "
        "assertively any colour."
    ),
    "dark": (
        "Cloud-free and absorbing: alkali metals, mostly sodium and potassium, eat the visible "
        "and very little comes back. Also a lightness bucket rather than a hue. **These swatches "
        "are shown far lighter than the planets would really appear** — every base swatch on the "
        "site is normalised to the same luminance so the darkest worlds are not rendered as "
        "identical black squares. The colour is honest; the brightness is a display convention."
    ),
}

# How many planets get a full card before the page falls back to a plain list of names.
FEATURED = 24


@dataclass(frozen=True)
class HubPlanet:
    id: str
    name: str
    hex: str
    roman_hex: str | None
    ly: int | None
    type_label: str


@dataclass(frozen=True)
class ColourHub:
    family: str
    label: str
    why: str
    planets: list[HubPlanet]
    swatches: list[str]
    prev_family: str | None
    next_family: str | None

    @property
    def count(self) -> int:
        return len(self.planets)

    @property
    def featured(self) -> list[HubPlanet]:
        return self.planets[:FEATURED]

    @property
    def rest(self) -> list[HubPlanet]:
        return self.planets[FEATURED:]


def _ly(distance_pc: float | None) -> int | None:
    if not distance_pc or distance_pc <= 0:
        return None
    return int(round(distance_pc * 3.26156))


def build_colour_hubs(records: list[PlanetRecord]) -> list[ColourHub]:
    """One hub per family that has members, in the gallery's chip order.

    Planets are ordered nearest-first so the cards at the top are the ones a reader has the best
    chance of having heard of, with distance-unknown members falling to the end by name. Every
    member of the family appears on its hub — the ordering only decides which get a card.
    """
    from pipeline.classify import TYPE_LABELS, planet_type

    buckets: dict[str, list[HubPlanet]] = {}
    for rec in records:
        fam = colour_family(tuple(rec.true_colour.srgb))
        view = rec.instrument_views[0] if rec.instrument_views else None
        buckets.setdefault(fam, []).append(
            HubPlanet(
                id=rec.id,
                name=rec.name,
                hex=rec.true_colour.hex,
                roman_hex=view.colour.hex if view else None,
                ly=_ly(rec.params.distance_pc),
                type_label=TYPE_LABELS.get(
                    planet_type(
                        rec.params.radius_r_earth,
                        rec.params.mass_m_earth,
                        rec.params.equilibrium_temp_k,
                    ),
                    "Planet",
                ),
            )
        )

    present = [f for f in FAMILY_ORDER if buckets.get(f)]
    hubs: list[ColourHub] = []
    for i, fam in enumerate(present):
        planets = sorted(buckets[fam], key=lambda p: (p.ly is None, p.ly or 0, p.name))
        # A representative strip: spread across the family rather than the first few, so the
        # band shows its range instead of five near-identical swatches.
        step = max(1, len(planets) // 6)
        hubs.append(
            ColourHub(
                family=fam,
                label=FAMILY_LABEL.get(fam, fam.title()),
                why=FAMILY_WHY.get(fam, ""),
                planets=planets,
                swatches=[p.hex for p in planets[::step]][:6],
                prev_family=present[i - 1] if i else None,
                next_family=present[i + 1] if i + 1 < len(present) else None,
            )
        )
    return hubs
