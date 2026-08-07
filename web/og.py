"""Build the Open Graph share card for a planet: a 1200x630 PNG, generated at site-build
time, one per planet.

The whole product is an image, so a shared link that unfurls as a grey rectangle throws the
product away at the moment it travels furthest. This module draws the same thing the page
draws -- the lit disc, the five-stop ramp, the base hex -- so the unfurl in Slack or iMessage
IS the planet, not a logo.

The disc is a numpy port of the classic (non-phase, non-pixel) path of the WebGL shader in
`web/static/planet-render.js`. It is deliberately a port and not an approximation: the share
card and the page have to show the same world. If that shader's classic path changes, change
`_disc()` with it -- tests/test_og_card.py pins the shader constants so the two cannot drift
silently.

Honesty rules carry over from the site: the card says MODELLED, never photographed, and a
microlensing planet -- whose light no telescope will ever isolate -- says so on the card.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONTS = Path(__file__).parent / "assets" / "fonts"

# Card geometry. 1200x630 is the Open Graph 1.91:1 slot every unfurler crops to.
W, H = 1200, 630

# Site colour tokens, lifted from web/static/style.css :root so the card reads as the site.
BG = (0, 0, 0)
FG = (232, 236, 244)  # --fg
FG_DIM = (151, 161, 180)  # --fg-dim
FG_FAINT = (107, 116, 136)  # --fg-faint
ACCENT = (35, 196, 232)  # --accent (Tron, the default theme)
GRID = (18, 24, 32)  # graticule, a touch above pure black
SHADOW = (26, 31, 40)  # hard offset shadow behind the swatches (retro styling)

# Disc placement: left third, vertically centred, with room for the caption beneath.
_DISC_CX, _DISC_CY, _DISC_R = 296, 300, 196
# Right-hand text column.
_COL_X = 570
_COL_R = W - 60


@lru_cache(maxsize=16)
def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    name = "Silkscreen-Bold.ttf" if bold else "Silkscreen-Regular.ttf"
    return ImageFont.truetype(str(_FONTS / name), size)


def _hex_to_rgb01(hexcode: str) -> tuple[float, float, float]:
    h = hexcode.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _hex_to_rgb(hexcode: str) -> tuple[int, int, int]:
    h = hexcode.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


@dataclass(frozen=True)
class CardSpec:
    """Everything the card draws. Assembled by the caller from a PlanetRecord so this module
    stays free of the data schema (and trivially testable)."""

    name: str
    palette: tuple[str, ...]  # the 5-stop ramp, shade-2 -> tint-2
    base_hex: str  # the planet's own colour, NOT a ramp stop
    subtitle: str  # host star line
    facts: tuple[str, ...]  # short right-column stat lines
    radius_r_earth: float | None
    cloud_state: str
    luminance_y: float
    caption: str  # the honesty line under the disc


# ── the disc ────────────────────────────────────────────────────────────────────────────
# A straight port of planet-render.js's classic path: style "smooth" (pixel=0), fidelity
# "classic" (turb=0, warmCool=0, bandGain=0.44), phase < 0 (the fixed soft day/night term).

_BAND_GAIN = 0.44
_NIGHT_F = 0.34
_LIGHT = 0.0  # the `light` uniform; 0 is the site's default key direction


def _derive(radius_r_earth: float | None, cloud_state: str, base_hex: str,
            luminance_y: float) -> dict[str, float]:
    """Port of `derive()` in planet-render.js. Same cuts, same constants."""
    r = radius_r_earth if radius_r_earth else 8.0
    cls = "rocky" if r < 2 else ("ice" if r < 6 else "gas")
    cloud = (cloud_state or "").lower()
    cloud_free = "cloud-free" in cloud or "free" in cloud
    band_freq = 15.0 if cls == "gas" else (7.0 if cls == "ice" else 2.5)
    band_contrast = 0.25 if cls == "rocky" else (0.25 if cloud_free else 0.8)
    brightness = 0.72 + min(luminance_y, 1.0) * 0.55
    br, bg, bb = _hex_to_rgb01(base_hex)
    haze = min(max(0.0, bb - max(br, bg)) * 2.2, 1.0)  # blueness -> haze
    return {
        "bandFreq": band_freq,
        "bandContrast": band_contrast,
        "brightness": brightness,
        "haze": haze,
    }


# Ramp resolution. The shader evaluates ramp() per pixel; here it is a 1-D lookup, because
# `tone` is scalar per pixel and the ramp is a pure function of it. Evaluating it as four
# full-frame mixes over three channels was the single most expensive thing in the card. At
# 2048 steps the worst-case quantisation error is well under 1/255 of a channel, i.e. the
# lookup and the per-pixel evaluation round to the same 8-bit colour.
_RAMP_STEPS = 2048


def _ramp_lut(pal: np.ndarray) -> np.ndarray:
    """The shader's `ramp()` evaluated once across [0, 1] -> (_RAMP_STEPS, 3) float32."""
    tt = np.linspace(0.0, 1.0, _RAMP_STEPS, dtype=np.float32) * 4.0
    col = np.repeat(pal[0][None, :], _RAMP_STEPS, axis=0)
    for i in range(1, 5):
        w = np.clip(tt - (i - 1), 0.0, 1.0)[:, None]
        col = col * (1.0 - w) + pal[i] * w
    return col


def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ── the pixel-art disc ──────────────────────────────────────────────────────────────────
# A port of the shader's OTHER path: style "retro" (pixel=1, classic fidelity, phase < 0).
# The look is made by the resolution, not despite it: the shader renders the globe at 80 px
# and lets CSS upscale with image-rendering:pixelated, so the port renders the same 80 px
# grid and upscales with NEAREST. Constants follow planet-render.js exactly: 5 posterization
# levels, dither amplitude 0.9/levels, outline ring darkening the rim to 0.35 (keepLit is 0
# whenever there is no phase control, so the classic outline is always fully present).

_PIXEL_RES = 80
_PIXEL_LEVELS = 5.0

# The shader's 4x4 Bayer matrix, row-major, as gl_FragCoord indexes it.
_BAYER4 = (
    np.array(
        [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32
    )
    / 16.0
    - 0.5
)


def disc_pixel(spec: CardSpec, size: int, rot: float = 0.0) -> Image.Image:
    """The retro pixel-art globe at `size` px (rendered at 80 px, upscaled NEAREST).

    `size` is snapped down to a whole multiple of the 80 px grid so every fat pixel is the
    same number of device pixels wide — a fractional upscale is exactly the jank the site's
    own renderer works to avoid.
    """
    d = _derive(spec.radius_r_earth, spec.cloud_state, spec.base_hex, spec.luminance_y)
    pal = np.array([_hex_to_rgb01(h) for h in spec.palette], dtype=np.float32)

    n = _PIXEL_RES
    ax = ((np.arange(n, dtype=np.float32) + 0.5) / n * 2.0 - 1.0).astype(np.float32)
    ux = ax[None, :]
    uy = -ax[:, None]
    r2 = ux * ux + uy * uy
    inside = r2 <= 1.0
    z = np.sqrt(np.clip(1.0 - r2, 0.0, None))

    lvec = np.array([math.cos(_LIGHT) * 0.55, 0.28, 0.90], dtype=np.float32)
    lvec = lvec / np.linalg.norm(lvec)
    ndotl = ux * lvec[0] + uy * lvec[1] + z * lvec[2]
    lit = _smoothstep(-0.08, 0.42, ndotl)
    limb = np.power(np.clip(z, 0.0, None), 0.30)
    shade = (_NIGHT_F + (1.0 - _NIGHT_F) * lit) * limb

    bf, bc = d["bandFreq"], d["bandContrast"]
    lat = np.arcsin(np.clip(uy, -1.0, 1.0))
    band = 0.5 + 0.5 * np.sin(lat * bf + np.sin(lat * bf * 0.5) * 0.6)
    band = 0.5 + (band - 0.5) * bc
    lon = np.arctan2(np.broadcast_to(ux, r2.shape), z) + rot
    band = band + 0.12 * bc * np.sin(lon * 3.0 + lat * bf * 0.5)

    rim = _smoothstep(0.74, 1.0, r2)
    tone = shade * (0.60 + _BAND_GAIN * band) * d["brightness"] + rim * d["haze"] * 0.28

    # Pixel path: dither THEN posterize — flat colour bands with dithered pixel-art edges.
    # gl_FragCoord.y counts from the bottom of the buffer; our rows count from the top.
    cols_idx = np.arange(n) % 4
    rows_idx = (n - 1 - np.arange(n)) % 4
    bayer = _BAYER4[rows_idx[:, None], cols_idx[None, :]]
    dither = 0.9 / _PIXEL_LEVELS
    tone = np.clip(tone, 0.0, 1.0) + bayer * dither
    tone = np.floor(tone * _PIXEL_LEVELS + 0.5) / _PIXEL_LEVELS

    idx = (np.clip(tone, 0.0, 1.0) * (_RAMP_STEPS - 1) + 0.5).astype(np.int32)
    col = _ramp_lut(pal)[idx]
    # Retro outline ring (keepLit = 0 with no phase control -> constant 0.35 factor).
    col = np.where((r2 > 0.90)[..., None], col * 0.35, col)

    rgb = np.clip(col * 255.0 + 0.5, 0, 255).astype(np.uint8)
    alpha = np.where(inside, 255, 0).astype(np.uint8)  # hard edge: pixel art has no AA
    img = Image.fromarray(np.dstack([rgb, alpha]), mode="RGBA")
    k = max(1, size // n)
    return img.resize((n * k, n * k), Image.NEAREST)


def _disc(spec: CardSpec, size: int, rot: float = 0.0) -> Image.Image:
    """Render the lit sphere to an RGBA image of `size` px, transparent outside the limb."""
    d = _derive(spec.radius_r_earth, spec.cloud_state, spec.base_hex, spec.luminance_y)
    pal = np.array([_hex_to_rgb01(h) for h in spec.palette], dtype=np.float32)

    n = size
    # Pixel centres across [-1, 1]; +y is up, matching the shader's clip-space uv. float32
    # throughout: the output is 8-bit, and this halves the memory traffic, which is where
    # the time in this function actually goes.
    ax = ((np.arange(n, dtype=np.float32) + 0.5) / n * 2.0 - 1.0).astype(np.float32)
    ux = ax[None, :]  # (1, n)
    uy = -ax[:, None]  # (n, 1)
    r2 = ux * ux + uy * uy
    z = np.sqrt(np.clip(1.0 - r2, 0.0, None))

    lvec = np.array([math.cos(_LIGHT) * 0.55, 0.28, 0.90], dtype=np.float32)
    lvec = lvec / np.linalg.norm(lvec)
    ndotl = ux * lvec[0] + uy * lvec[1] + z * lvec[2]
    lit = _smoothstep(-0.08, 0.42, ndotl)
    limb = np.power(np.clip(z, 0.0, None), 0.30)
    shade = (_NIGHT_F + (1.0 - _NIGHT_F) * lit) * limb

    # Latitude, and the belt term that depends on nothing else, are functions of the ROW
    # alone: kept as (n, 1) columns and broadcast, rather than evaluated per pixel. arcsin
    # and one of the three sines over ~600k pixels was most of this function's runtime.
    bf, bc = d["bandFreq"], d["bandContrast"]
    lat = np.arcsin(np.clip(uy, -1.0, 1.0))
    band = 0.5 + 0.5 * np.sin(lat * bf + np.sin(lat * bf * 0.5) * 0.6)
    band = 0.5 + (band - 0.5) * bc  # mix(0.5, band, bandContrast)
    lon = np.arctan2(np.broadcast_to(ux, r2.shape), z) + rot
    band = band + 0.12 * bc * np.sin(lon * 3.0 + lat * bf * 0.5)

    rim = _smoothstep(0.74, 1.0, r2)
    tone = shade * (0.60 + _BAND_GAIN * band) * d["brightness"] + rim * d["haze"] * 0.28
    idx = (np.clip(tone, 0.0, 1.0) * (_RAMP_STEPS - 1) + 0.5).astype(np.int32)
    col = _ramp_lut(pal)[idx]
    # Smooth-only haze tint toward the lightest stop.
    w = (rim * d["haze"] * 0.4)[..., None]
    col = col * (1.0 - w) + pal[4] * w

    rgb = np.clip(col * 255.0 + 0.5, 0, 255).astype(np.uint8)
    # Analytic edge coverage rather than supersampling. Everything inside the limb is a smooth
    # gradient that a 1:1 sample renders exactly; only the circular edge needs antialiasing,
    # and its coverage has a closed form. Rendering 2x and downsampling instead cost 4x the
    # pixels for a picture that differs by a mean of 0.3/255 (see tests/test_og_card.py) —
    # five minutes of a deploy at catalogue scale.
    coverage = np.clip((1.0 - np.sqrt(r2)) * (n / 2.0) + 0.5, 0.0, 1.0)
    alpha = np.clip(coverage * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), mode="RGBA")


# ── text helpers ────────────────────────────────────────────────────────────────────────


def _text_w(draw: ImageDraw.ImageDraw, s: str, font: ImageFont.FreeTypeFont) -> int:
    return int(draw.textbbox((0, 0), s, font=font)[2])


def _fit_font(draw: ImageDraw.ImageDraw, s: str, max_w: int, sizes: tuple[int, ...],
              bold: bool = True) -> ImageFont.FreeTypeFont:
    """Largest size from `sizes` (descending) whose rendering fits `max_w`.

    Silkscreen is an 8px-grid pixel face, so the candidate sizes are multiples of 8: any other
    size lands glyph stems between device pixels and the name renders furry.
    """
    for size in sizes:
        if _text_w(draw, s, _font(bold, size)) <= max_w:
            return _font(bold, size)
    return _font(bold, sizes[-1])


def _ellipsize(draw: ImageDraw.ImageDraw, s: str, font: ImageFont.FreeTypeFont,
               max_w: int) -> str:
    if _text_w(draw, s, font) <= max_w:
        return s
    while s and _text_w(draw, s + "…", font) > max_w:
        s = s[:-1]
    return s + "…"


# ── the card ────────────────────────────────────────────────────────────────────────────


def render_card(spec: CardSpec) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Oscilloscope graticule, faint, on the same 60px division everywhere.
    for x in range(0, W + 1, 60):
        draw.line([(x, 0), (x, H)], fill=GRID)
    for y in range(0, H + 1, 60):
        draw.line([(0, y), (W, y)], fill=GRID)

    # Accent rule along the top edge — the site's signature hairline.
    draw.rectangle([0, 0, W, 3], fill=ACCENT)

    disc = _disc(spec, _DISC_R * 2)
    img.paste(disc, (_DISC_CX - _DISC_R, _DISC_CY - _DISC_R), disc)

    # Honesty caption under the disc. Never "photo", always "modelled".
    cap_font = _font(False, 16)
    cap = _ellipsize(draw, spec.caption, cap_font, _DISC_R * 2 + 40)
    draw.text((_DISC_CX - _text_w(draw, cap, cap_font) // 2, _DISC_CY + _DISC_R + 34), cap,
              font=cap_font, fill=FG_FAINT)

    # ── right column ──
    y = 96
    kicker = _font(False, 16)
    draw.text((_COL_X, y), "EXOPLANET PALETTE", font=kicker, fill=ACCENT)
    y += 40

    name_font = _fit_font(draw, spec.name, _COL_R - _COL_X, (64, 56, 48, 40, 32, 24))
    name = _ellipsize(draw, spec.name, name_font, _COL_R - _COL_X)
    draw.text((_COL_X, y), name, font=name_font, fill=FG)
    y += name_font.size + 26

    sub_font = _font(False, 16)
    draw.text((_COL_X, y), _ellipsize(draw, spec.subtitle, sub_font, _COL_R - _COL_X),
              font=sub_font, fill=FG_DIM)
    y += 46

    for fact in spec.facts[:3]:
        draw.text((_COL_X, y), _ellipsize(draw, fact, sub_font, _COL_R - _COL_X),
                  font=sub_font, fill=FG_FAINT)
        y += 26

    # ── the ramp: five squares with the retro hard offset shadow ──
    sw, gap, off = 96, 14, 6
    ramp_y = H - 176
    for i, hexcode in enumerate(spec.palette[:5]):
        x = _COL_X + i * (sw + gap)
        draw.rectangle([x + off, ramp_y + off, x + off + sw, ramp_y + off + sw], fill=SHADOW)
        draw.rectangle([x, ramp_y, x + sw, ramp_y + sw], fill=_hex_to_rgb(hexcode))

    # The base swatch's own hex, called out separately — no ramp stop claims to be the
    # planet's colour, so the card doesn't let one imply it either.
    hex_font = _font(True, 24)
    hy = ramp_y + sw + 34
    chip = 22
    draw.rectangle([_COL_X, hy + 2, _COL_X + chip, hy + 2 + chip], fill=_hex_to_rgb(spec.base_hex))
    draw.text((_COL_X + chip + 14, hy), spec.base_hex.upper(), font=hex_font, fill=FG)
    return img


def card_png(spec: CardSpec, colours: int = 128) -> bytes:
    """PNG bytes for the card, palette-quantised.

    One card per planet at ~6k planets, so size matters: full-colour these are ~250 KB each
    (1.4 GB of dist). The card is flat art over a black field, so an adaptive 128-colour
    palette is visually indistinguishable and about 8x smaller. Crawlers fetch these one at
    a time and never on a page load, so decode cost is irrelevant.
    """
    img = render_card(spec).quantize(
        colors=colours, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
