"""Curated real telescope images for the directly-imaged planets.

These are hand-maintained facts, not derivable from the Exoplanet Archive: which planets
have an actual processed direct-imaging photograph, where it came from, and how it must be
credited. Keyed by record id (see `pipeline.catalog._slug`). Only directly-imaged planets
appear here — microlensing planets never yield an image, and RV/transit planets have none
yet. The site's colour is always modelled; this is the genuine (always infrared, always
false-coloured) dot of light a telescope actually received.

Every entry is a real observation visually verified against its source, with an honest
credit + license. HR 8799 b/c/e share one JWST NIRCam system image (each note says which
labelled point source is that planet). Do not add an entry without a verified real image.
"""

from __future__ import annotations

from pipeline.models import RealObservation

# The JWST NIRCam coronagraph image of the HR 8799 system (planets b, c, d, e as points),
# released via ESA/Webb (weic2504a). Shared by all three HR 8799 records; each names its dot.
_HR8799 = dict(
    file="obs/{id}.jpg",  # filled per-planet below
    instrument="JWST NIRCam (coronagraph)",
    band="near-infrared (4.1/4.3/4.6 µm → false colour)",
    year=2024,
    credit="NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)",
    license="CC BY 4.0",
    source_url="https://esawebb.org/images/weic2504a/",
)

# id -> RealObservation. Verified public ESO / ESA-Webb / Subaru(NAOJ) direct images.
OBSERVATIONS: dict[str, RealObservation] = {
    "51-eri-b": RealObservation(
        file="obs/51-eri-b.jpg",
        instrument="JWST NIRCam (coronagraph)",
        band="near-infrared (4.1 µm, shown red → false colour)",
        year=2024,
        credit="NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)",
        license="CC BY 4.0",
        source_url="https://esawebb.org/images/weic2504b/",
        note="The planet is the fuzzy red point labelled “b”, just left of the masked star "
        "51 Eri. Infrared light, false-coloured — not a visible-light photo.",
    ),
    "hr-8799-b": RealObservation(
        **{**_HR8799, "file": "obs/hr-8799-b.jpg"},
        note="Planet “b” is the blue dot at far left — the outermost of HR 8799’s four planets "
        "(~68 AU). Star hidden by the coronagraph; infrared, false-coloured.",
    ),
    "hr-8799-c": RealObservation(
        **{**_HR8799, "file": "obs/hr-8799-c.jpg"},
        note="Planet “c” is the bluish-white dot at top (~38 AU). Star hidden by the "
        "coronagraph; infrared, false-coloured — not a visible-light photo.",
    ),
    "hr-8799-e": RealObservation(
        **{**_HR8799, "file": "obs/hr-8799-e.jpg"},
        note="Planet “e” is the orange dot nearest the masked star — the innermost of the four "
        "(~16 AU). Infrared, false-coloured — not a visible-light photo.",
    ),
    "bet-pic-b": RealObservation(
        file="obs/bet-pic-b.jpg",
        instrument="ESO VLT / SPHERE",
        band="near-infrared (false colour)",
        year=2018,
        credit="ESO / Lagrange / SPHERE consortium",
        license="CC BY 4.0",
        source_url="https://www.eso.org/public/images/potw1846a/",
        note="Twelve real SPHERE frames (2014–2018): in each, the star sits behind the black "
        "mask and Beta Pictoris b is the bright point orbiting it. Infrared, false-coloured.",
    ),
    "hd-95086-b": RealObservation(
        file="obs/hd-95086-b.jpg",
        instrument="ESO VLT / NACO",
        band="thermal infrared (L′, ~3.8 µm → false colour)",
        year=2013,
        credit="ESO / J. Rameau",
        license="CC BY 4.0",
        source_url="https://www.eso.org/public/images/eso1324a/",
        note="The planet is the faint blue point at lower-left; the star symbol inside the blue "
        "circle marks the subtracted stellar position. Thermal infrared, false-coloured.",
    ),
    "gj-504-b": RealObservation(
        file="obs/gj-504-b.jpg",
        instrument="Subaru Telescope / HiCIAO + AO188",
        band="near-infrared (J+H → false colour)",
        year=2013,
        credit="NAOJ (National Astronomical Observatory of Japan)",
        license="NAOJ terms — credit required",
        source_url="https://subarutelescope.org/en/gallery/pressrelease/galactic/2025/06/18/3566.html",
        note="The planet is the white point at upper-right; the star sits behind the black "
        "central mask amid blue/orange speckle noise. Near-infrared, false-coloured.",
    ),
}


def observation_for(planet_id: str) -> RealObservation | None:
    return OBSERVATIONS.get(planet_id)
