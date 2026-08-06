"""Sources and credits: everything this site stands on, on the site itself.

The repository already knew all of this — `pipeline.rights` is stamped into `planets.json`,
LICENSE-DATA spells it out, CITATION.cff names the papers — but a visitor saw none of it. The
Archive's requested acknowledgement, the papers behind every measured spectrum, the licence on
the surface maps: all of it lived in files you had to clone the repo to read. A credit nobody
can see is not a credit.

So this module renders the credits page FROM those same structures rather than retyping them:
`pipeline.rights.SOURCES` and `CARRIED_ASSETS` for the science inputs and the files we serve,
`web.textures.SURFACE_MAPS` and `pipeline.observations.OBSERVATIONS` for the imagery. Add a
source anywhere in the pipeline and it appears here without anyone remembering to; that is the
whole point, and `tests/test_credits.py` holds it to it.

The only thing written here is PLAIN: one sentence per source saying, for a reader who has
never opened a journal, what that source actually gives this site. The formal citation sits
beside it, never instead of it — the dual-audience rule applies to credits too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.observations import OBSERVATIONS
from pipeline.rights import CARRIED_ASSETS, RIGHTS, Source
from web.textures import SURFACE_MAPS

# What each scientific input does for this site, in plain English. Keyed by `Source.name` —
# tests/test_credits.py asserts the keys and `pipeline.rights` never drift apart, so a new
# source cannot ship with a citation and no explanation.
PLAIN: dict[str, str] = {
    "NASA Exoplanet Archive (pscomppars)": (
        "Every number about a planet and its star — how big, how hot, how far out, what "
        "kind of star it orbits — comes from here. It is the catalogue the whole site is "
        "built on: without it there is nothing to compute a colour for."
    ),
    "Cahoy et al. (2010) albedo grid": (
        "A set of precomputed model atmospheres: what fraction of light a Jupiter- or "
        "Neptune-like planet reflects at each wavelength, worked out for a range of "
        "distances from the star and cloud states. One of the two engines behind the "
        "modelled spectra, and the reference marks under the model-space slider."
    ),
    "Karkoschka (1998)": (
        "Real measurements — Jupiter, Saturn, Uranus and Neptune, recorded through a "
        "telescope at ESO in 1995. Four of the five solar-system anchors that let you check "
        "this site's method against planets whose colours we already know."
    ),
    "Payne et al. (2026)": (
        "The measured spectrum of Earth, assembled from spacecraft and earthshine "
        "observations. It is the fifth anchor, and the strictest test on the site: if our "
        "pipeline got Earth's colour wrong, nothing else here would be worth reading."
    ),
    "PICASO": (
        "NASA's open-source radiative-transfer code. Given a planet's gravity, temperature "
        "and atmosphere it computes the reflected-light spectrum properly, from physics "
        "rather than from a lookup table. Used for selected targets."
    ),
    "colour-science": (
        "The library that turns a spectrum into a colour: it carries the CIE 1931 "
        "colour-matching functions — the measured response of human vision — and the "
        "standard transform into sRGB. We use it rather than hand-rolled maths so the "
        "colour step is a published standard, not our arithmetic."
    ),
    "Thorngren et al. (2016)": (
        "The finding that smaller giant planets hold more metal-rich atmospheres than bigger "
        "ones. It is what stops every modelled planet at the same temperature coming out the "
        "same colour — for most of the catalogue, this paper is quietly setting the chemistry."
    ),
    "Kopparapu et al. (2014)": (
        "The climate-model calculation of where a star's habitable zone begins and ends. It is "
        "the arithmetic behind the 'could there be liquid water' filter — which is about "
        "orbital distance only, and never about an atmosphere anyone has measured."
    ),
    "Carrión-González et al. (2021)": (
        "The study that worked out which known exoplanets Roman's coronagraph could actually "
        "catch in reflected light. Its Table 4 is the target board: the shortlist, and the "
        "counts quoted on that page."
    ),
    "Roman Coronagraph Instrument Primer (CPP)": (
        "NASA's own specification of the Roman coronagraph's filters — which colours of light "
        "each one lets through. Every 'as Roman would see it' swatch on this site is the model "
        "spectrum pushed through those three filters and reassembled."
    ),
    "NASA planetary fact sheets (NSSDC)": (
        "The reference numbers for the solar system's own planets — size, orbit, distance from "
        "the Sun. The five anchors are not in the exoplanet catalogue, so theirs come here."
    ),
    "IAU constellation boundaries (Roman 1987), via VizieR / CDS": (
        "The official map of which patch of sky belongs to which constellation. It is why a "
        "planet page can tell you its host star is in Lyra, and why the sky chart can point "
        "you at the right part of the night."
    ),
    "Silkscreen (Jason Kottke)": (
        "The pixel face this site's labels, readouts and captions are set in — most of what "
        "makes it look like an instrument rather than a web page."
    ),
    "Alpine.js v3.14.8": (
        "The small JavaScript library behind the menus, toggles and sliders. Everything "
        "important still renders without it."
    ),
}

# doi:10.xxxx/yyy anywhere in a citation string, so the page can link it without the citation
# having to carry a URL as well.
_DOI = re.compile(r"\bdoi:(10\.\d{4,9}/\S+?)(?=[\s,;]|$)")

# Licences `pipeline.rights` records as a URL, and what a reader should see instead.
_LICENCE_NAMES = {
    "https://creativecommons.org/licenses/by/4.0/": "CC BY 4.0",
}


@dataclass(frozen=True)
class CreditEntry:
    """One credited input, ready for the template."""

    name: str
    plain: str  # what it gives this site, for someone who has never read a paper
    role: str  # the one-line technical role, from pipeline.rights
    url: str
    licence: str  # human-readable, always: a bare URL is turned into its licence's name
    licence_url: str  # where that licence is, or "" — the template links it
    citation: str
    note: str
    doi: str  # bare DOI, or "" — the template links it


@dataclass(frozen=True)
class ImageCredit:
    """One picture credit, collapsed across every planet that uses the same source.

    `uses` is (planet name, the image's own source page) — one rightsholder can supply several
    images from several release pages (the same JWST team credit covers 51 Eri b and the HR
    8799 system, released separately), so the link belongs on each planet rather than on the
    credit. Repeating a credit line per image would read as sloppiness, and hiding all but one
    source page would break the trail back to the original.
    """

    credit: str
    licence: str
    kind: str  # "map" (surface maps on the renders) or "photo" (real telescope images)
    uses: tuple[tuple[str, str], ...]

    @property
    def used_for(self) -> str:
        return ", ".join(name for name, _ in self.uses)


def _licence(raw: str) -> tuple[str, str]:
    """(what to print, where to link). `pipeline.rights` stores some licences as the licence's
    own URL, which is exactly right in a machine-readable header and unreadable as a chip on a
    page — nobody wants to read `https://creativecommons.org/licenses/by/4.0/` in 9px caps."""
    if raw.startswith("http"):
        return (_LICENCE_NAMES.get(raw.rstrip("/") + "/", "See licence"), raw)
    return (raw, "")


def _entry(src: Source) -> CreditEntry:
    doi = _DOI.search(src.citation)
    licence, licence_url = _licence(src.licence)
    return CreditEntry(
        name=src.name,
        # A missing blurb is a test failure, not a page failure: fall back to the technical
        # role so a source can never be silently dropped from the page it belongs on.
        plain=PLAIN.get(src.name, src.role),
        role=src.role,
        url=src.url,
        licence=licence,
        licence_url=licence_url,
        citation=src.citation,
        note=src.note,
        doi=doi.group(1).rstrip(".") if doi else "",
    )


def science_sources() -> list[CreditEntry]:
    """The scientific inputs: data, models, code. Straight from `pipeline.rights.SOURCES`."""
    return [_entry(s) for s in RIGHTS.sources]


def carried_assets() -> list[CreditEntry]:
    """Third-party files served to the browser (the typeface, the JS library)."""
    return [_entry(s) for s in CARRIED_ASSETS]


def _title(planet_id: str, names: dict[str, str]) -> str:
    """The planet's real catalogue name where the build knows it, else a readable fallback.

    De-slugging is lossy — `bet-pic-b` is Beta Pictoris b, which no rule recovers — so the
    build passes the real names in and this only has to cope with a records-free caller
    (the tests).
    """
    if planet_id in names:
        return names[planet_id]
    return " ".join(
        w.upper() if len(w) <= 2 and w.isalpha() else w.title() for w in planet_id.split("-")
    )


def image_credits(names: dict[str, str] | None = None) -> list[ImageCredit]:
    """Every picture on the site that is not ours, grouped by who it belongs to.

    Each of these is already credited where it appears — under the render, in the photo
    lightbox — but a reader who wants to know what this site did and did not make should not
    have to open forty planet pages to find out.
    """
    names = names or {}
    groups: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    for pid, sm in SURFACE_MAPS.items():
        groups.setdefault((sm.credit, sm.license, "map"), []).append(
            (_title(pid, names), sm.source_url)
        )
    for pid, obs in OBSERVATIONS.items():
        for o in obs:
            groups.setdefault((o.credit, o.license, "photo"), []).append(
                (_title(pid, names), o.source_url)
            )

    out = [
        ImageCredit(credit=credit, licence=licence, kind=kind, uses=tuple(sorted(set(uses))))
        for (credit, licence, kind), uses in groups.items()
    ]
    # Maps first (they are on the swatch itself), then photographs, each alphabetical — a
    # stable order, so the page does not reshuffle between builds.
    return sorted(out, key=lambda c: (c.kind != "map", c.credit))


def credits_context(names: dict[str, str] | None = None) -> dict:
    """Everything the template needs. `rights` is the same object stamped into planets.json."""
    return {
        "sources": science_sources(),
        "assets": carried_assets(),
        "images": image_credits(names),
        "rights": RIGHTS,
    }
