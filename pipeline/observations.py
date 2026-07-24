"""Curated real images for planets we have actually photographed.

These are hand-maintained facts, not derivable from the Exoplanet Archive: which planets
have an actual processed photograph, where it came from, and how it must be credited.
Keyed by record id (see `pipeline.catalog._slug`). Two kinds of planet qualify:
directly-imaged exoplanets (infrared, false-coloured dots of light — the site's colour is
still modelled), and the solar system anchors (real visible-light spacecraft photographs,
the ground truth the measured-albedo swatch can be checked against). Microlensing planets
never yield an image, and RV/transit planets have none yet.

Each planet maps to a LIST of observations so a second instrument (e.g. Roman, post-launch)
is APPENDED beside the first, never substituted, and the page then offers a per-telescope
toggle. Every entry is a real observation visually verified against its source, with an
honest credit + license. HR 8799 b/c/e share one JWST NIRCam system image (each note says
which labelled point source is that planet). Do not add an entry without a verified image.
"""

from __future__ import annotations

from pipeline.models import RealObservation

# The JWST NIRCam coronagraph image of the HR 8799 system (planets b, c, d, e as points),
# released via ESA/Webb (weic2504a). Shared by all three HR 8799 records; each names its dot.
_HR8799 = dict(
    telescope="JWST",
    file="obs/{id}.jpg",  # filled per-planet below
    instrument="JWST NIRCam (coronagraph)",
    band="near-infrared (4.1/4.3/4.6 µm → false colour)",
    year=2024,
    credit="NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)",
    license="CC BY 4.0",
    source_url="https://esawebb.org/images/weic2504a/",
)

# id -> list[RealObservation]. Verified public ESO / ESA-Webb / Subaru(NAOJ) direct images.
OBSERVATIONS: dict[str, list[RealObservation]] = {
    "51-eri-b": [
        RealObservation(
            telescope="JWST",
            file="obs/51-eri-b.jpg",
            instrument="JWST NIRCam (coronagraph)",
            band="near-infrared (4.1 µm, shown red → false colour)",
            year=2024,
            credit="NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)",
            license="CC BY 4.0",
            source_url="https://esawebb.org/images/weic2504b/",
            note="The planet is the fuzzy red point labelled “b”, just left of the masked star "
            "51 Eri. Infrared light, false-coloured, not a visible-light photo.",
        ),
    ],
    "hr-8799-b": [
        RealObservation(
            **{**_HR8799, "file": "obs/hr-8799-b.jpg"},
            note="Planet “b” is the blue dot at far left, the outermost of HR 8799’s four "
            "planets (~68 AU). Star hidden by the coronagraph; infrared, false-coloured.",
        ),
    ],
    "hr-8799-c": [
        RealObservation(
            **{**_HR8799, "file": "obs/hr-8799-c.jpg"},
            note="Planet “c” is the bluish-white dot at top (~38 AU). Star hidden by the "
            "coronagraph; infrared, false-coloured, not a visible-light photo.",
        ),
    ],
    "hr-8799-e": [
        RealObservation(
            **{**_HR8799, "file": "obs/hr-8799-e.jpg"},
            note="Planet “e” is the orange dot nearest the masked star, the innermost of the "
            "four (~16 AU). Infrared, false-coloured, not a visible-light photo.",
        ),
    ],
    "bet-pic-b": [
        RealObservation(
            telescope="VLT",
            file="obs/bet-pic-b.jpg",
            instrument="ESO VLT / SPHERE",
            band="near-infrared (false colour)",
            year=2018,
            credit="ESO / Lagrange / SPHERE consortium",
            license="CC BY 4.0",
            source_url="https://www.eso.org/public/images/potw1846a/",
            note="Twelve real SPHERE frames (2014–2018): in each, the star sits behind the "
            "black mask and Beta Pictoris b is the bright point orbiting it. Infrared, "
            "false-coloured.",
        ),
    ],
    "hd-95086-b": [
        RealObservation(
            telescope="VLT",
            file="obs/hd-95086-b.jpg",
            instrument="ESO VLT / NACO",
            band="thermal infrared (L′, ~3.8 µm → false colour)",
            year=2013,
            credit="ESO / J. Rameau",
            license="CC BY 4.0",
            source_url="https://www.eso.org/public/images/eso1324a/",
            note="The planet is the faint blue point at lower-left; the star symbol inside the "
            "blue circle marks the subtracted stellar position. Thermal infrared, "
            "false-coloured.",
        ),
    ],
    "gj-504-b": [
        RealObservation(
            telescope="Subaru",
            file="obs/gj-504-b.jpg",
            instrument="Subaru Telescope / HiCIAO + AO188",
            band="near-infrared (J+H → false colour)",
            year=2013,
            credit="NAOJ (National Astronomical Observatory of Japan)",
            license="NAOJ terms, credit required",
            source_url="https://subarutelescope.org/en/gallery/pressrelease/galactic/2025/06/18/3566.html",
            note="The planet is the white point at upper-right; the star sits behind the black "
            "central mask amid blue/orange speckle noise. Near-infrared, false-coloured.",
        ),
    ],
    # ── Solar system anchors: real visible-light photographs, credit NASA (public domain).
    # Unlike the exoplanet entries above these are TRUE-COLOUR photos — the one place the
    # pipeline's swatch can be checked against what a camera actually saw.
    "jupiter": [
        RealObservation(
            telescope="Cassini",
            file="obs/jupiter.jpg",
            instrument="Cassini / Imaging Science Subsystem",
            band="visible light (true colour)",
            year=2000,
            credit="NASA/JPL/Space Science Institute",
            license="Public domain (NASA)",
            source_url="https://photojournal.jpl.nasa.gov/catalog/PIA04866",
            note="A real visible-light photograph — the most detailed global colour portrait "
            "of Jupiter ever made, from Cassini's December 2000 flyby. Compare it directly "
            "with the measured-spectrum swatch.",
        ),
    ],
    "saturn": [
        RealObservation(
            telescope="Cassini",
            file="obs/saturn.jpg",
            instrument="Cassini / Imaging Science Subsystem",
            band="visible light (natural colour)",
            year=2008,
            credit="NASA/JPL/Space Science Institute",
            license="Public domain (NASA)",
            source_url="https://photojournal.jpl.nasa.gov/catalog/PIA11141",
            note="A real visible-light photograph from Cassini in Saturn orbit (2008), "
            "natural colour. The spectrum behind our swatch is of the globe alone, at zero "
            "ring tilt — the rings in the photo are a bonus the disk-average never sees.",
        ),
    ],
    "uranus": [
        RealObservation(
            telescope="Voyager 2",
            file="obs/uranus.jpg",
            instrument="Voyager 2 / Imaging Science Subsystem",
            band="visible light (true colour)",
            year=1986,
            credit="NASA/JPL-Caltech",
            license="Public domain (NASA)",
            source_url="https://photojournal.jpl.nasa.gov/catalog/PIA18182",
            note="A real visible-light photograph — humanity's only close-up of Uranus "
            "(Voyager 2, January 1986). Its featureless pale cyan is genuinely what the "
            "planet looks like.",
        ),
    ],
    "neptune": [
        RealObservation(
            telescope="Voyager 2",
            file="obs/neptune.jpg",
            instrument="Voyager 2 / Imaging Science Subsystem",
            band="visible light (contrast-enhanced colour)",
            year=1989,
            credit="NASA/JPL",
            license="Public domain (NASA)",
            source_url="https://photojournal.jpl.nasa.gov/catalog/PIA01492",
            note="A real Voyager 2 photograph (August 1989) — but its famous deep blue was "
            "contrast-enhanced in processing. Modern reanalysis shows Neptune's true colour "
            "is the paler greenish-blue our measured spectrum reproduces.",
        ),
    ],
    "earth": [
        RealObservation(
            telescope="Apollo 17",
            file="obs/earth.jpg",
            instrument="Hasselblad 70 mm camera, en route to the Moon",
            band="visible light (true colour)",
            year=1972,
            credit="NASA / Apollo 17 crew",
            license="Public domain (NASA)",
            source_url="https://images.nasa.gov/details/as17-148-22727",
            note="The Blue Marble — a real photograph taken by the Apollo 17 crew on "
            "7 December 1972. The palest of pale blue dots, exactly the tint the measured "
            "spectrum yields.",
        ),
    ],
}


def observations_for(planet_id: str) -> list[RealObservation]:
    """All verified real images for a planet, in display order (empty if none)."""
    return OBSERVATIONS.get(planet_id, [])
