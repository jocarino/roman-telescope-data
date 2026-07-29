"""The real surface maps, and the means the renderer rescales them by.

`SurfaceMap.mean` is not decoration: the shader multiplies every texel by
(derived colour / mean), so if a map is ever regenerated — re-encoded, resized, recomposited
— without its mean being updated alongside, every one of those planets silently renders in
the wrong colour. Nothing else would catch it; the picture would just be subtly off. So the
means are checked against the shipped files here, with the same cos(latitude) weighting
tools/prep_textures.py uses.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from PIL import Image

from web.textures import SURFACE_MAPS, surface_map_for

_STATIC = Path(__file__).resolve().parents[1] / "web" / "static"

# The five planets we have flown past and mapped. Nothing else may have a map, or the site
# would be showing invented geography for a world nobody has ever resolved.
ANCHORS = {"earth", "jupiter", "saturn", "uranus", "neptune"}


def _cos_lat_mean(img: Image.Image) -> tuple[float, float, float]:
    """Mean sRGB of an equirectangular map, weighting rows by cos(latitude)."""
    px = img.convert("RGB").load()
    w, h = img.size
    tot = [0.0, 0.0, 0.0]
    wsum = 0.0
    for y in range(h):
        wt = math.cos((0.5 - (y + 0.5) / h) * math.pi)
        row = [0.0, 0.0, 0.0]
        for x in range(w):
            r, g, b = px[x, y]
            row[0] += r
            row[1] += g
            row[2] += b
        for i in range(3):
            tot[i] += (row[i] / w) * wt
        wsum += wt
    return tuple(t / wsum for t in tot)  # type: ignore[return-value]


def test_only_the_anchors_have_maps():
    assert set(SURFACE_MAPS) == ANCHORS
    assert surface_map_for("hr-8799-b") is None
    assert surface_map_for("nope") is None


@pytest.mark.parametrize("pid", sorted(ANCHORS))
def test_map_file_ships_and_is_equirectangular(pid):
    sm = SURFACE_MAPS[pid]
    path = _STATIC / sm.file
    assert path.exists(), f"{sm.file} is referenced but not shipped"
    with Image.open(path) as img:
        w, h = img.size
        # 2:1 is what wrapping a full 360x180 sphere requires; anything else skews the map.
        assert w == 2 * h, f"{sm.file} is {w}x{h}, not 2:1"
        # Power-of-two, or the renderer cannot mipmap it and the pixel styles alias to noise.
        assert w & (w - 1) == 0, f"{sm.file} width {w} is not a power of two"


@pytest.mark.parametrize("pid", sorted(ANCHORS))
def test_declared_mean_matches_the_shipped_file(pid):
    sm = SURFACE_MAPS[pid]
    with Image.open(_STATIC / sm.file) as img:
        actual = _cos_lat_mean(img)
    for i, (got, want) in enumerate(zip(actual, sm.mean, strict=True)):
        assert got == pytest.approx(want, abs=0.5), (
            f"{pid} channel {'RGB'[i]}: file averages {got:.2f} but web/textures.py says "
            f"{want:.2f}. Re-run tools/prep_textures.py and paste the printed means."
        )


@pytest.mark.parametrize("pid", sorted(ANCHORS))
def test_every_map_is_credited(pid):
    sm = SURFACE_MAPS[pid]
    assert sm.credit and sm.license and sm.source_url.startswith("https://")
    assert sm.body, "each map needs a plain-English description of what it actually is"


def test_saturn_is_the_only_ringed_anchor():
    ringed = {pid for pid, sm in SURFACE_MAPS.items() if sm.rings}
    assert ringed == {"saturn"}
    rings = SURFACE_MAPS["saturn"].rings
    assert rings is not None
    assert (_STATIC / rings.file).exists()
    # C ring inner edge to A ring outer edge, in Saturn radii, and the axial tilt.
    assert 1.0 < rings.inner < rings.outer < 3.0
    assert 0 < rings.tilt_deg < 90
