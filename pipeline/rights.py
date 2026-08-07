"""Who owns what, and what we owe them — as data, not prose.

`planets.json` used to travel with no rights statement at all: a downloaded copy said nothing
about its licence, its sources, or the acknowledgement the NASA Exoplanet Archive asks for.
A licence stated only in a README is a licence no machine can honour, and a reader who did not
clone the repo never sees it.

This module is the single source of truth. `pipeline/emit/writer.py` stamps it into the file
header, and it is the natural thing for a future credits page to render from — one list, one
place to keep true. LICENSE-DATA carries the same information for humans; if you change one,
change both.

The important structural point: the file is TWO RIGHTS LAYERS. `DERIVED_FIELDS` are ours and
are CC BY 4.0. `REPUBLISHED_FIELDS` are upstream facts we pass through and cannot license to
anyone. Claiming the whole file would assert rights we do not hold.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

CC_BY_4 = "https://creativecommons.org/licenses/by/4.0/"

# Ours: computed by this pipeline.
DERIVED_FIELDS = (
    "true_colour",
    "spectrum",
    "palette",
    "instrument_views",
    "phase_colours",
    "sun_swap",
    "habitability",
    "meta",
)

# Not ours: upstream facts, passed through essentially unchanged.
REPUBLISHED_FIELDS = ("params", "host_star", "sky", "discovery")

# The Archive asks for this wording. Reproduced verbatim, and inherited by anything built on
# this file — which is exactly why it has to travel inside the file.
ARCHIVE_ACKNOWLEDGEMENT = (
    "This research has made use of the NASA Exoplanet Archive, which is operated by the "
    "California Institute of Technology, under contract with the National Aeronautics and "
    "Space Administration under the Exoplanet Exploration Program."
)

# CDS asks for this wording wherever a VizieR catalogue is used — and separately requires the
# original catalogue's own authors to be cited, which is Roman (1987) below. Two sentences,
# both theirs, both verbatim.
VIZIER_ACKNOWLEDGEMENT = (
    "This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France "
    "(DOI : 10.26093/cds/vizier). The original description of the VizieR service was published "
    "in 2000, A&AS 143, 23."
)

# Every acknowledgement we owe verbatim, in the order they appear on the credits page.
ACKNOWLEDGEMENTS: tuple[tuple[str, str], ...] = (
    ("NASA Exoplanet Archive", ARCHIVE_ACKNOWLEDGEMENT),
    ("VizieR / CDS, Strasbourg", VIZIER_ACKNOWLEDGEMENT),
)


@dataclass(frozen=True)
class Source:
    name: str
    role: str  # what it contributes here
    url: str
    licence: str
    citation: str = ""
    note: str = ""


SOURCES: tuple[Source, ...] = (
    Source(
        name="NASA Exoplanet Archive (pscomppars)",
        role="planet and host-star parameters",
        url="https://exoplanetarchive.ipac.caltech.edu",
        licence="no explicit data licence; acknowledgement requested",
        citation="Christiansen et al. (2025), PSJ, doi:10.3847/PSJ/ade3c2",
        note=ARCHIVE_ACKNOWLEDGEMENT,
    ),
    Source(
        name="Cahoy et al. (2010) albedo grid",
        role="model albedo spectra for one of the spectrum engines",
        url="https://roman.ipac.caltech.edu",
        licence="unresolved — see LICENSE-DATA section 5",
        citation="Cahoy, Marley & Fortney (2010), ApJ 724, 189, doi:10.1088/0004-637X/724/1/189",
        note="Deriving colours from it is uncontroversial; redistributing the grid files is a "
        "separate act we have not cleared. Excluded from any dataset deposit.",
    ),
    Source(
        name="Karkoschka (1998)",
        role="measured albedo spectra for Jupiter, Saturn, Uranus, Neptune",
        url="https://pds-atmospheres.nmsu.edu",
        licence="public domain (NASA PDS Atmospheres Node)",
        citation="Karkoschka (1998), Icarus 133, 134-146, doi:10.1006/icar.1998.5913",
    ),
    Source(
        name="Payne et al. (2026)",
        role="measured Earth albedo spectrum",
        url="https://zenodo.org/records/17470005",
        licence=CC_BY_4,
        citation="Payne, Villanueva, Kofman et al. (2026), PSJ, doi:10.3847/PSJ/ae2feb",
        note="Redistributed verbatim under CC BY 4.0, (c) the authors, without warranties of "
        "any kind (see section 5 of the licence). Interpolated onto our 5 nm grid; "
        "otherwise unmodified.",
    ),
    Source(
        name="PICASO",
        role="radiative-transfer spectra for selected targets",
        url="https://natashabatalha.github.io/picaso/",
        licence="imported, not redistributed",
        citation="Batalha et al. (2019), ApJ 878, 70, doi:10.3847/1538-4357/ab1b51",
        note="PICASO 4.0.1, with the opacity database from Zenodo record 14861730 — both are "
        "needed to reproduce the committed spectra, and the opacity database carries its own "
        "citation. See docs/picaso-runbook.md.",
    ),
    Source(
        name="Thorngren et al. (2016)",
        role="the mass-metallicity relation that sets atmospheric metallicity in the "
        "parametric engine — the engine behind most planets on this site",
        url="https://iopscience.iop.org/article/10.3847/0004-637X/831/1/64",
        licence="published result; citation as courtesy",
        citation="Thorngren, Fortney, Murray-Clay & Lopez (2016), ApJ 831, 64, "
        "doi:10.3847/0004-637X/831/1/64",
        note="Smaller planets get more metal-rich atmospheres, which is why a Neptune-mass "
        "world and a Jupiter-mass world at the same temperature do not come out the same "
        "colour here.",
    ),
    Source(
        name="Parmentier et al. (2016)",
        role="the cloud-condensation sequence that decides which hot planets are cloudy in the "
        "parametric engine",
        url="https://iopscience.iop.org/article/10.3847/0004-637X/828/1/22",
        licence="published result; citation as courtesy",
        citation="Parmentier, Fortney, Showman, Morley & Marley (2016), ApJ 828, 22, "
        "doi:10.3847/0004-637X/828/1/22",
        note="Clouds are not simply burned off as a planet gets hotter: each condensate is "
        "stable over its own narrow temperature range, so the sky clears and then clouds over "
        "again. This paper predicts the silicate-cloud brightening between roughly 1,600 and "
        "1,900 K that gives planets like Kepler-7 b their high measured albedo.",
    ),
    Source(
        name="Demory et al. (2011, 2013)",
        role="the measured albedo the parametric engine's silicate-cloud window is calibrated "
        "against",
        url="https://iopscience.iop.org/article/10.1088/2041-8205/735/1/L12",
        licence="published result; citation as courtesy",
        citation="Demory, Seager, Madhusudhan et al. (2011), ApJL 735, L12, "
        "doi:10.1088/2041-8205/735/1/L12; Demory, de Wit, Lewis et al. (2013), ApJL 776, L25, "
        "doi:10.1088/2041-8205/776/2/L25",
        note="Kepler-7 b's geometric albedo of 0.32 +/- 0.03 is the one measurement the hot-"
        "cloud model here is fitted to; the 2013 paper resolves the cloud as high-altitude, "
        "off-centre and probably silicate.",
    ),
    Source(
        name="Ackerman & Marley (2001)",
        role="the cloud-sedimentation picture behind the parametric engine's gravity term",
        url="https://iopscience.iop.org/article/10.1086/321540",
        licence="published result; citation as courtesy",
        citation="Ackerman & Marley (2001), ApJ 556, 872, doi:10.1086/321540",
        note="Whether a cloud deck reaches the visible atmosphere or rains out below it is a "
        "contest between settling and mixing, which is why low-gravity planets here end up "
        "cloudier than high-gravity ones at the same temperature.",
    ),
    Source(
        name="Kopparapu et al. (2014)",
        role="the habitable-zone edges behind the 'could there be liquid water' lens",
        url="https://iopscience.iop.org/article/10.1088/2041-8205/787/2/L29",
        licence="published result; citation as courtesy",
        citation="Kopparapu, Ramirez, SchottelKotte, Kasting, Domagal-Goldman & Eymet (2014), "
        "ApJL 787, L29, doi:10.1088/2041-8205/787/2/L29",
        note="Table 1 coefficients, for a 1 Earth-mass planet. The zone is orbital distance "
        "only: no atmosphere has been measured for any planet we mark.",
    ),
    Source(
        name="Carrión-González et al. (2021)",
        role="the eligible-planet list behind the Roman target board",
        url="https://doi.org/10.1051/0004-6361/202039993",
        licence="published result; citation as courtesy",
        citation="Carrión-González, García Muñoz, Santos, Cabrera, Csizmadia & Rauer (2021), "
        "A&A 651, A7, doi:10.1051/0004-6361/202039993",
        note="Table 4 — planets whose reflected light the Roman coronagraph could reach. The "
        "board quotes their scenario counts directly rather than recomputing them.",
    ),
    Source(
        name="Roman Coronagraph Instrument Primer (CPP)",
        role="the filter bandpasses the 'as Roman would see it' colour is reconstructed from",
        url="https://roman.ipac.caltech.edu/docs/RomanCoronagraphPrimer_Current.pdf",
        licence="NASA/JPL-Caltech public document",
        citation="Roman Coronagraph Instrument Primer, Community Participation Program, "
        "8 January 2025, p. 5",
        note="We model the three flight bands — 575 nm, 730 nm and 825 nm — as top-hat "
        "filters at their nominal design widths (10%, 15%, 10%). That is a CONVENTION, and it "
        "matters: real filter profiles have sloped shoulders, and the as-built widths measured "
        "on the ground run one to two points wider than the nominal figures. Band 2 (660 nm) "
        "is on the filter wheel but was never characterised as a supported observing mode, so "
        "it is not modelled here.",
    ),
    Source(
        name="NASA planetary fact sheets (NSSDC)",
        role="orbit and size data for the five solar-system anchors",
        url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/",
        licence="public domain (NASA)",
        note="The anchors are not in the Exoplanet Archive, so their orbital numbers come from "
        "here instead.",
    ),
    Source(
        name="colour-science",
        role="CIE 1931 colour-matching functions and the XYZ->sRGB transform",
        url="https://www.colour-science.org",
        licence="BSD-3-Clause (imported, not redistributed)",
        citation="doi:10.5281/zenodo.17837391",
    ),
    Source(
        name="IAU constellation boundaries (Roman 1987), via VizieR / CDS",
        role="which constellation each host star sits in, on the sky charts",
        url="https://cdsarc.cds.unistra.fr/viz-bin/cat/VI/42",
        licence="public catalogue data; acknowledgement requested",
        citation="Roman (1987), PASP 99, 695 — CDS catalogue VI/42; "
        "VizieR: doi:10.26093/cds/vizier, 2000, A&AS 143, 23",
        note="Catalogue VI/42 is redistributed verbatim as "
        "pipeline/data/constellation_boundaries.dat. VizieR's terms require the original "
        "catalogue author and publication to be cited explicitly alongside VizieR itself, "
        "which is why Roman (1987) is named first here.",
    ),
)

# Third-party files this repository CARRIES and serves to a browser, as opposed to the science
# inputs above. Separate tuple, not part of `Rights`: none of it is in `planets.json`, so
# stamping it into that file's header would be noise. The site's credits page renders both.
# LICENSE-DATA section 3 is the same list for humans; if you change one, change both.
CARRIED_ASSETS: tuple[Source, ...] = (
    Source(
        name="Silkscreen (Jason Kottke)",
        role="the pixel typeface every label on this site is set in",
        url="https://fonts.google.com/specimen/Silkscreen",
        licence="SIL Open Font License 1.1",
        note="OFL.txt ships beside both copies of the font, as section 2 of that licence "
        "requires.",
    ),
    Source(
        name="Alpine.js v3.14.8",
        role="the small amount of interactivity on these pages",
        url="https://alpinejs.dev",
        licence="MIT",
        note="Copyright and permission notice retained inside the minified file.",
    ),
)


# Which source a record's own `params.spectrum_source` tag owes its citation to, and the same
# for each instrument in `pipeline.config.INSTRUMENTS`. A reader holding `planets.json` can see
# "spectrum_source": "cahoy" on a record and resolve who to cite without reading our code —
# and, more to the point, a new engine or instrument added without a credit fails
# tests/test_credits.py rather than shipping uncredited. Values are `Source.name`.
ENGINE_CREDITS: tuple[tuple[str, str], ...] = (
    ("parametric", "Thorngren et al. (2016)"),
    ("cahoy", "Cahoy et al. (2010) albedo grid"),
    ("picaso", "PICASO"),
    ("karkoschka1998", "Karkoschka (1998)"),
    ("payne2026", "Payne et al. (2026)"),
)

INSTRUMENT_CREDITS: tuple[tuple[str, str], ...] = (
    ("roman-cgi", "Roman Coronagraph Instrument Primer (CPP)"),
)


@dataclass(frozen=True)
class Rights:
    """The rights block stamped into the file header."""

    derived_licence: str = CC_BY_4
    derived_fields: tuple[str, ...] = DERIVED_FIELDS
    republished_fields: tuple[str, ...] = REPUBLISHED_FIELDS
    attribution: str = "Exoplanet Palette (jocarino), CC BY 4.0"
    holder: str = "Copyright (c) 2026 jocarino"
    # One address for anyone who needs a human: the site footer renders it and the data
    # header carries it, so a journalist on the site and a consumer of a released file
    # reach the same place.
    contact: str = "joaogveloso.contact@gmail.com"
    warranty: str = (
        "Provided without warranties of any kind; see section 5 of the CC BY 4.0 licence."
    )
    honesty: str = (
        "Every colour in this file is MODELLED, not photographed. Reproducing these values "
        "as observations misrepresents them. The five solar-system planets are the exception "
        "and are derived from measured albedo spectra; each record's provenance field says "
        "which it is."
    )
    republished_note: str = (
        "This file has two rights layers. The derived_fields are ours and are CC BY 4.0. The "
        "republished_fields are upstream facts we pass through and cannot license to you; use "
        "them under their own source's terms, listed in sources."
    )
    # Kept as a plain string as well as in `acknowledgements`: it was already in the header of
    # released files, and a consumer reading rights.acknowledgement should not break because a
    # second acknowledgement turned up.
    acknowledgement: str = ARCHIVE_ACKNOWLEDGEMENT
    acknowledgements: tuple[tuple[str, str], ...] = ACKNOWLEDGEMENTS
    full_text: str = "https://github.com/jocarino/roman-telescope-data/blob/main/LICENSE-DATA"
    sources: tuple[Source, ...] = field(default_factory=lambda: SOURCES)
    # spectrum_source / instrument id -> the Source.name above that it owes.
    engine_credits: tuple[tuple[str, str], ...] = ENGINE_CREDITS
    instrument_credits: tuple[tuple[str, str], ...] = INSTRUMENT_CREDITS

    def as_dict(self) -> dict:
        return asdict(self)


RIGHTS = Rights()
