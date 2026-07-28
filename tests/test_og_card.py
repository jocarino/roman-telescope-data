"""The Open Graph share card, and the thing that can quietly rot: its planet disc.

`web/og.py` renders the disc in numpy because the card is built server-side; the site renders
the same disc in GLSL. They are two implementations of one picture, and nothing on screen
shows them side by side — the card only ever appears in someone else's Slack — so drift here
is invisible until a share looks like a different planet from the page.

Two guards:
  * the constants of the shader's classic path are pinned against planet-render.js's actual
    source, so editing that path fails here until web/og.py is edited too;
  * an independently written scalar port of the same maths is checked against the vectorised
    one, which is what catches broadcast and axis-orientation bugs (a flipped y renders a
    plausible planet lit from the wrong side, and looks fine in isolation).
"""

from __future__ import annotations

import io
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from web import og
from web.og import CardSpec, card_png, render_card

_RENDER_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "planet-render.js"

_SPEC = CardSpec(
    name="HD 189733 b",
    palette=("#0d1a2b", "#1b3a63", "#3070b8", "#78b0e8", "#d6e8fb"),
    base_hex="#3b5aa8",
    subtitle="HD 189733 · K2 V",
    facts=("Hot Jupiter", "1,200 K equilibrium", "63 light-years away"),
    radius_r_earth=12.6,
    cloud_state="cloud-free",
    luminance_y=0.12,
    caption="MODELLED · NOT PHOTOGRAPHED",
)


# ── the card as an artefact ─────────────────────────────────────────────────────────────


def test_card_is_the_open_graph_slot():
    img = render_card(_SPEC)
    assert img.size == (1200, 630), "og:image:width/height in base.html hard-code this"


def test_card_png_decodes_and_stays_small():
    data = card_png(_SPEC)
    img = Image.open(io.BytesIO(data))
    assert img.format == "PNG"
    assert img.size == (1200, 630)
    # One card per planet at catalogue scale; 60 KB each would be a third of a gigabyte.
    assert len(data) < 60_000, f"{len(data)} bytes — quantisation regressed?"


def test_card_shows_the_planets_own_colour_not_only_the_ramp():
    """The base hex is the physics; no ramp stop is allowed to stand in for it."""
    px = np.asarray(render_card(_SPEC).convert("RGB")).reshape(-1, 3)
    want = np.array([int(_SPEC.base_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)])
    assert (px == want).all(axis=1).any()


def test_disc_is_drawn_and_is_not_black():
    img = render_card(_SPEC).convert("RGB")
    centre = img.getpixel((og._DISC_CX, og._DISC_CY))
    assert sum(centre) > 60, "the disc rendered black — palette or tone maths broke"
    # And the corner is still the page's background, i.e. the disc has not overrun the card.
    assert img.getpixel((1199, 629)) == og.BG


@pytest.mark.parametrize(
    "name", ["2MASS J21265040-8140293 b", "Jupiter", "OGLE-2018-BLG-0677L b"]
)
def test_long_names_shrink_rather_than_overflow(name):
    """Names run from 'Earth' to 22 characters of survey designation. The fitter steps the
    pixel font down through 8px multiples; if it ever fails, the name runs off the card."""
    img = np.asarray(render_card(CardSpec(**{**_SPEC.__dict__, "name": name})).convert("RGB"))
    # The rows the name occupies, and the last column inside the right margin. (Row 0-3 is
    # the full-width accent rule, which is meant to reach the edge.)
    band = img[96:200, og._COL_R : 1200].sum(axis=2)
    assert band.max() < 120, f"{name!r} overran the right margin"


# ── shader drift ────────────────────────────────────────────────────────────────────────

# Exact source lines of planet-render.js's classic path that web/og.py._disc() reimplements.
# If one of these stops matching, the two renderers have diverged: fix og.py, then update the
# expectation here. Whitespace-normalised so reflowing the JS is not a false alarm.
_PINNED = [
    'vec3 L = normalize(vec3(cos(light)*0.55, 0.28, 0.90));',
    'float nightF = 0.34;',
    'float limb = pow(z, 0.30);',
    'lit = smoothstep(-0.08, 0.42, dot(N, L));',
    'float shade = (nightF + (1.0-nightF)*lit) * limb;',
    'float band = 0.5 + 0.5*sin(lat*bandFreq + wphase + sin(lat*bandFreq*0.5)*0.6);',
    'band = mix(0.5, band, bandContrast);',
    'band += 0.12 * bandContrast * sin(lon*3.0 + lat*bandFreq*0.5);',
    'float rim = smoothstep(0.74,1.0,r2);',
    'float tone = shade * (0.60 + bandGain*band) * brightness + rim*haze*0.28;',
    'if(pixel==0){ col = mix(col, pal[4], rim*haze*0.4); }',
    # derive(): the attribute -> uniform mapping.
    'var bandFreq = cls === "gas" ? 15.0 : (cls === "ice" ? 7.0 : 2.5);',
    'var bandContrast = cls === "rocky" ? 0.25 : (cloudFree ? 0.25 : 0.8);',
    'var brightness = 0.72 + Math.min(lum, 1) * 0.55;',
    'var haze = Math.max(0, base[2] - Math.max(base[0], base[1])) * 2.2;',
    'var cls = r < 2 ? "rocky" : (r < 6 ? "ice" : "gas");',
    # The classic-mode band gain, passed as a uniform rather than written in the shader.
    'gl.uniform1f(U.bandGain, aug ? 0.66 : 0.44);',
]


@pytest.mark.parametrize("line", _PINNED, ids=lambda s: s[:38])
def test_shader_classic_path_still_matches_the_python_port(line):
    src = " ".join(_RENDER_JS.read_text().split())
    assert " ".join(line.split()) in src, (
        "planet-render.js changed a constant that web/og.py._disc() reimplements — "
        "update the port and this pin together"
    )


def test_derive_matches_the_js_cuts():
    """Spot-check the class cuts rather than trusting the pinned source alone."""
    rocky = og._derive(1.0, "cloudy", "#888888", 0.5)
    ice = og._derive(4.0, "cloudy", "#888888", 0.5)
    gas = og._derive(12.0, "cloudy", "#888888", 0.5)
    assert (rocky["bandFreq"], ice["bandFreq"], gas["bandFreq"]) == (2.5, 7.0, 15.0)
    assert rocky["bandContrast"] == 0.25 and gas["bandContrast"] == 0.8
    assert og._derive(12.0, "cloud-free", "#888888", 0.5)["bandContrast"] == 0.25
    # Blueness -> haze; a neutral grey has none.
    assert og._derive(12.0, "cloudy", "#888888", 0.5)["haze"] == 0.0
    assert og._derive(12.0, "cloudy", "#0000ff", 0.5)["haze"] == 1.0


# ── the vectorised port vs an independent scalar one ────────────────────────────────────


def _scalar_shader(spec: CardSpec, ux: float, uy: float) -> tuple[float, float, float]:
    """One pixel of the classic path, written straight from the GLSL, scalar and unvectorised.
    Deliberately does not share code with og._disc()."""
    d = og._derive(spec.radius_r_earth, spec.cloud_state, spec.base_hex, spec.luminance_y)
    pal = [og._hex_to_rgb01(h) for h in spec.palette]

    r2 = ux * ux + uy * uy
    z = math.sqrt(max(0.0, 1.0 - r2))
    lat = math.asin(max(-1.0, min(1.0, uy)))

    lx, ly, lz = math.cos(0.0) * 0.55, 0.28, 0.90
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    def smoothstep(e0, e1, x):
        t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
        return t * t * (3.0 - 2.0 * t)

    lit = smoothstep(-0.08, 0.42, ux * lx + uy * ly + z * lz)
    limb = z**0.30
    shade = (0.34 + 0.66 * lit) * limb

    bf, bc = d["bandFreq"], d["bandContrast"]
    band = 0.5 + 0.5 * math.sin(lat * bf + math.sin(lat * bf * 0.5) * 0.6)
    band = 0.5 + (band - 0.5) * bc
    lon = math.atan2(ux, z)
    band += 0.12 * bc * math.sin(lon * 3.0 + lat * bf * 0.5)

    rim = smoothstep(0.74, 1.0, r2)
    tone = shade * (0.60 + 0.44 * band) * d["brightness"] + rim * d["haze"] * 0.28

    t = max(0.0, min(1.0, tone)) * 4.0
    col = list(pal[0])
    for i in range(1, 5):
        w = max(0.0, min(1.0, t - (i - 1)))
        col = [c * (1 - w) + pal[i][k] * w for k, c in enumerate(col)]
    w = rim * d["haze"] * 0.4
    return tuple(c * (1 - w) + pal[4][k] * w for k, c in enumerate(col))


@pytest.mark.parametrize(
    "spec",
    [
        _SPEC,
        CardSpec(**{**_SPEC.__dict__, "radius_r_earth": 1.0, "cloud_state": "cloudy"}),
        CardSpec(**{**_SPEC.__dict__, "radius_r_earth": 4.0, "base_hex": "#c8b48a"}),
    ],
    ids=["gas-cloudfree", "rocky", "ice"],
)
@pytest.mark.parametrize("uv", [(0.0, 0.0), (0.3, 0.4), (-0.45, -0.2), (0.1, -0.6)])
def test_vectorised_disc_agrees_with_the_scalar_shader(spec, uv):
    """The disc renders 1:1, so every output pixel is the shader evaluated at that pixel's
    centre — no filtering to account for, and the comparison can be exact to a rounding step."""
    size = 400
    img = np.asarray(og._disc(spec, size).convert("RGB"), dtype=float)
    ux, uy = uv
    col = int((ux + 1.0) / 2.0 * size)
    row = int((1.0 - uy) / 2.0 * size)
    ref = np.array(
        _scalar_shader(
            spec,
            (col + 0.5) / size * 2.0 - 1.0,
            -((row + 0.5) / size * 2.0 - 1.0),
        )
    )
    assert np.allclose(img[row, col], ref * 255.0, atol=1.0), (
        f"disc pixel at uv={uv}: got {img[row, col]}, scalar shader says {ref * 255.0}"
    )


def test_disc_is_lit_from_the_shaders_direction_not_a_flipped_axis():
    """L = (0.55, 0.28, 0.90): up and to the right. A flipped axis is the easy bug here and
    it renders a perfectly plausible planet, so assert the lighting's asymmetry directly.

    Hemisphere means, not sample points: the belt term sin(lat*bandFreq + ...) is odd in
    latitude, so it cancels across symmetric halves and leaves the lighting gradient, whereas
    any single pair of points is dominated by whichever belt it happens to land on.
    """
    size = 300
    rgba = np.asarray(og._disc(_SPEC, size), dtype=float)
    lum = rgba[:, :, :3].sum(axis=2)
    lit_mask = rgba[:, :, 3] > 250  # interior only; the limb's partial alpha would skew means

    ax = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    uy = -ax[:, None] * np.ones((1, size))
    ux = ax[None, :] * np.ones((size, 1))

    def mean_where(cond):
        return lum[lit_mask & cond].mean()

    assert mean_where(uy > 0.25) > mean_where(uy < -0.25) + 5, "the light comes from above"
    assert mean_where(ux > 0.25) > mean_where(ux < -0.25) + 5, "and from the right"


def test_outside_the_limb_is_transparent():
    disc = og._disc(_SPEC, 200)
    alpha = np.asarray(disc)[:, :, 3]
    assert alpha[0, 0] == 0 and alpha[-1, -1] == 0
    assert alpha[100, 100] == 255


def test_limb_is_antialiased_not_a_hard_staircase():
    """The edge is the one place a 1:1 render needs help; coverage is computed analytically
    rather than by supersampling, so check it actually produces partial alpha."""
    alpha = np.asarray(og._disc(_SPEC, 200))[:, :, 3]
    partial = ((alpha > 0) & (alpha < 255)).sum()
    # Roughly one feathered pixel per unit of circumference: 2*pi*r with r = 100.
    assert 300 < partial < 1400, f"{partial} partially covered edge pixels"


def test_disc_fills_its_box_without_overrunning_it():
    alpha = np.asarray(og._disc(_SPEC, 200))[:, :, 3]
    assert alpha[100, 0] > 0 and alpha[100, -1] > 0, "the limb should touch the box edges"
    assert alpha[0, 0] == 0, "but the corners stay empty"
