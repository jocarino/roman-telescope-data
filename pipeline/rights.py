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
    ),
    Source(
        name="colour-science",
        role="CIE 1931 colour-matching functions and the XYZ->sRGB transform",
        url="https://www.colour-science.org",
        licence="BSD-3-Clause (imported, not redistributed)",
        citation="doi:10.5281/zenodo.17837391",
    ),
    Source(
        name="VizieR / CDS, Strasbourg",
        role="star catalogue behind the sky charts",
        url="https://vizier.cds.unistra.fr",
        licence="acknowledgement requested",
        citation="doi:10.26093/cds/vizier; 2000, A&AS 143, 23",
        note="The original catalogue authors and publication references must be cited "
        "explicitly alongside VizieR itself.",
    ),
)


@dataclass(frozen=True)
class Rights:
    """The rights block stamped into the file header."""

    derived_licence: str = CC_BY_4
    derived_fields: tuple[str, ...] = DERIVED_FIELDS
    republished_fields: tuple[str, ...] = REPUBLISHED_FIELDS
    attribution: str = "Exoplanet Palette (jocarino), CC BY 4.0"
    holder: str = "Copyright (c) 2026 jocarino"
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
    acknowledgement: str = ARCHIVE_ACKNOWLEDGEMENT
    full_text: str = "https://github.com/jocarino/roman-telescope-data/blob/main/LICENSE-DATA"
    sources: tuple[Source, ...] = field(default_factory=lambda: SOURCES)

    def as_dict(self) -> dict:
        return asdict(self)


RIGHTS = Rights()
