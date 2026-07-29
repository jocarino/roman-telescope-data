"""Real surface maps for the five solar-system anchors.

The anchors are the one place on this site where ground truth exists: we have flown past
these planets and mapped them. Everywhere else the render's light-and-dark pattern is
schematic — bands drawn by a shader because nobody knows what the clouds of an exoplanet
actually look like. Here we can do better, so we do: the globe samples a real
equirectangular map and Jupiter gets its Great Red Spot, Earth its continents, Saturn its
rings, and Uranus the featureless haze Voyager 2 actually found.

What this does NOT change is the colour. Every map is rescaled per channel so its own
cos(latitude)-weighted mean equals that planet's physics-derived hex, i.e. the shader
multiplies each texel by (derived colour / `mean`). The morphology becomes real; the
colour claim stays exactly what it was — computed from a spectrum, not sampled from a
photograph. `mean` is measured on the shipped file, in the same sRGB-encoded space the
shader works in; regenerate both with `python3 tools/prep_textures.py`.

Curated, not derived — like `pipeline.observations`, this is hand-verified fact (which map,
from whom, under what licence) and lives outside the data release: it is applied at
site-build time, so a new map needs no `planets.json` re-release.
"""

from __future__ import annotations

from dataclasses import dataclass

# Solar System Scope's planetary map set: NASA imagery redrawn into clean, seam-free
# equirectangular maps, published for reuse under CC BY 4.0. Used for the four giants.
_SSS_CREDIT = "Solar System Scope (maps from NASA elevation and imagery data)"
_SSS_LICENSE = "CC BY 4.0"
_SSS_SOURCE = "https://www.solarsystemscope.com/textures/"


@dataclass(frozen=True)
class Rings:
    """A ring system, drawn as a tilted annulus around the globe.

    `inner`/`outer` are in planet radii and `tilt_deg` is how far the ring plane is opened
    towards the viewer. The strip is a 1-pixel-tall radial slice — colour and opacity from
    the innermost radius to the outermost — so the Cassini Division is a real gap in the
    data rather than something the shader draws.
    """

    file: str
    inner: float
    outer: float
    tilt_deg: float

    @property
    def frame_aspect(self) -> float:
        """How wide the render frame has to be, relative to its height.

        Must stay identical to `ringAspect()` in web/static/planet-render.js — the template
        uses it for the canvas's intrinsic size so a ringed hero lays out at the right shape
        on first paint, before any JavaScript has run. Get it wrong and the page loads with a
        square canvas and visibly snaps. The eighth-snapping is what keeps both render
        resolutions (80 and 480 px tall) a whole number of pixels wide, which the pixel styles
        need for their integer CSS upscale.
        """
        return round(((self.outer * 1.03) / 1.10) * 8) / 8


@dataclass(frozen=True)
class SurfaceMap:
    """One planet's real map: the file, the mean to normalise it by, and its provenance."""

    file: str
    mean: tuple[float, float, float]  # cos(lat)-weighted mean of `file`, sRGB 0-255
    body: str  # what the map actually is, in plain English
    credit: str
    license: str
    source_url: str
    rings: Rings | None = None


# Saturn's rings span the C ring's inner edge (74,658 km) to the A ring's outer edge
# (136,775 km); over an equatorial radius of 60,268 km that is 1.24 to 2.27 planet radii.
# 26.7° is Saturn's axial tilt — the widest the rings ever open to an observer.
_SATURN_RINGS = Rings(file="tex/saturn-ring.png", inner=1.24, outer=2.27, tilt_deg=26.7)

# Record id -> its map. Only the five anchors have one; every other planet keeps the
# schematic render, because for every other planet a map would be invention.
SURFACE_MAPS: dict[str, SurfaceMap] = {
    "earth": SurfaceMap(
        file="tex/earth.jpg",
        mean=(93.97, 100.64, 111.82),
        body="Blue Marble Next Generation — a composite of MODIS satellite imagery (land, "
        "ocean floor and ice, December 2004) under NASA's Blue Marble cloud layer",
        credit="NASA Earth Observatory (Reto Stöckli, Robert Simmon)",
        license="Public domain",
        source_url="https://visibleearth.nasa.gov/images/73909/december-blue-marble-next-generation",
    ),
    "jupiter": SurfaceMap(
        file="tex/jupiter.jpg",
        mean=(177.09, 167.47, 155.04),
        body="a global cloud-top map: the belts and zones, and the Great Red Spot south of "
        "the equator",
        credit=_SSS_CREDIT,
        license=_SSS_LICENSE,
        source_url=_SSS_SOURCE,
    ),
    "saturn": SurfaceMap(
        file="tex/saturn.jpg",
        mean=(221.56, 202.15, 166.35),
        body="a global cloud-top map — far fainter banding than Jupiter's, because a deep "
        "ammonia haze sits over it — plus the ring system",
        credit=_SSS_CREDIT,
        license=_SSS_LICENSE,
        source_url=_SSS_SOURCE,
        rings=_SATURN_RINGS,
    ),
    "uranus": SurfaceMap(
        file="tex/uranus.jpg",
        mean=(157.23, 205.23, 212.22),
        body="a global map that is almost perfectly blank — Voyager 2 found essentially no "
        "visible-light features at all",
        credit=_SSS_CREDIT,
        license=_SSS_LICENSE,
        source_url=_SSS_SOURCE,
    ),
    "neptune": SurfaceMap(
        file="tex/neptune.jpg",
        mean=(56.68, 90.03, 180.37),
        body="a global cloud-top map with the Great Dark Spot Voyager 2 photographed in 1989",
        credit=_SSS_CREDIT,
        license=_SSS_LICENSE,
        source_url=_SSS_SOURCE,
    ),
}


def surface_map_for(record_id: str) -> SurfaceMap | None:
    """This planet's real map, or None (which is every planet but the five anchors)."""
    return SURFACE_MAPS.get(record_id)
