"""Build the spectrum plot as a self-contained inline SVG (no chart library, per the spec).

Shows the full-spectrum albedo A(lambda) and the four-band Roman reconstruction, and
hatches the region below the lowest Roman band centre — the blue half Roman is blind to and
can only guess. A spectral gradient bar under the x-axis grounds wavelength in colour.

Two geometries are emitted per planet: the wide desktop scope face, and a compact
near-square variant whose labels stay legible on a phone (a 720-wide SVG scaled to a
390px screen halves every font; the compact face renders at roughly 1:1 instead).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pipeline.config import GRID_END_NM, GRID_NM, GRID_START_NM


@dataclass(frozen=True)
class _Geom:
    w: int
    h: int
    pad_l: int
    pad_r: int
    pad_t: int
    pad_b: int
    vdiv: int          # vertical graticule divisions
    label_w: int       # "Roman is blind here" highlight box width
    extra_class: str = ""
    idsuf: str = ""    # def-id suffix so two variants on one page don't collide


_WIDE = _Geom(w=720, h=240, pad_l=44, pad_r=16, pad_t=16, pad_b=40, vdiv=8, label_w=132)
_COMPACT = _Geom(
    w=400, h=290, pad_l=40, pad_r=12, pad_t=20, pad_b=42, vdiv=4, label_w=138,
    extra_class=" compact", idsuf="-c",
)


def _wavelength_to_rgb(nm: float) -> tuple[int, int, int]:
    """Cheap approximate visible-spectrum colour for the axis gradient (display only)."""
    if nm < 380 or nm > 780:
        r = g = b = 0.0
    elif nm < 440:
        r, g, b = -(nm - 440) / (440 - 380), 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / (490 - 440), 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / (510 - 490)
    elif nm < 580:
        r, g, b = (nm - 510) / (580 - 510), 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, -(nm - 645) / (645 - 580), 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    # Intensity falloff at the ends.
    if nm > 700:
        f = 0.3 + 0.7 * (780 - nm) / (780 - 700)
    elif nm < 420:
        f = 0.3 + 0.7 * (nm - 380) / (420 - 380)
    else:
        f = 1.0
    return tuple(int(round(255 * (c * f) ** 0.8)) for c in (r, g, b))  # type: ignore[return-value]


def _x(g: _Geom, nm: float) -> float:
    frac = (nm - GRID_START_NM) / (GRID_END_NM - GRID_START_NM)
    return g.pad_l + frac * (g.w - g.pad_l - g.pad_r)


def _y(g: _Geom, val: float, vmax: float) -> float:
    frac = val / vmax if vmax > 0 else 0.0
    return g.h - g.pad_b - frac * (g.h - g.pad_t - g.pad_b)


def _stepped(g: _Geom, values: np.ndarray, vmax: float) -> str:
    """Step-chart points (horizontal then vertical) for a blocky, pixel-art line."""
    xs = [_x(g, nm) for nm in GRID_NM]
    ys = [_y(g, v, vmax) for v in values]
    pts = []
    for i in range(len(xs)):
        pts.append(f"{xs[i]:.1f},{ys[i]:.1f}")
        if i + 1 < len(xs):
            pts.append(f"{xs[i + 1]:.1f},{ys[i]:.1f}")
    return " ".join(pts)


def _render(
    g: _Geom, true_albedo: list[float], roman_recon: list[float], extrap_below_nm: float
) -> str:
    true_a = np.asarray(true_albedo, dtype=float)
    roman_a = np.asarray(roman_recon, dtype=float)
    vmax = max(float(true_a.max()), float(roman_a.max()), 0.05) * 1.1

    x0, x1 = _x(g, GRID_START_NM), _x(g, GRID_END_NM)
    y_axis = g.h - g.pad_b
    hatch_x1 = _x(g, extrap_below_nm)

    # Spectral gradient stops for the axis bar.
    stops = []
    for nm in range(int(GRID_START_NM), int(GRID_END_NM) + 1, 20):
        r, gg, b = _wavelength_to_rgb(nm)
        off = (nm - GRID_START_NM) / (GRID_END_NM - GRID_START_NM) * 100
        stops.append(f'<stop offset="{off:.0f}%" stop-color="rgb({r},{gg},{b})"/>')
    grad = "".join(stops)

    true_pts = _stepped(g, true_a, vmax)
    roman_pts = _stepped(g, roman_a, vmax)

    # Oscilloscope graticule: horizontal + vertical division lines.
    gridlines = ""
    for frac in (0.25, 0.5, 0.75, 1.0):
        yy = g.h - g.pad_b - frac * (g.h - g.pad_t - g.pad_b)
        gridlines += (
            f'<line x1="{x0:.0f}" y1="{yy:.1f}" x2="{x1:.0f}" y2="{yy:.1f}" class="grid"/>'
        )
        gridlines += (
            f'<text x="{x0 - 6:.0f}" y="{yy + 3:.1f}" class="ytick">{frac * vmax:.2f}</text>'
        )
    for i in range(1, g.vdiv):
        xx = x0 + i / g.vdiv * (x1 - x0)
        gridlines += (
            f'<line x1="{xx:.1f}" y1="{g.pad_t}" x2="{xx:.1f}" y2="{y_axis:.0f}" class="grid"/>'
        )

    half_lbl = g.label_w / 2
    return f"""<svg viewBox="0 0 {g.w} {g.h}" class="spectrum{g.extra_class}" role="img"
  aria-label="Albedo spectrum: full model vs Roman four-band reconstruction">
  <defs>
    <linearGradient id="specbar{g.idsuf}" x1="0" y1="0" x2="1" y2="0">{grad}</linearGradient>
    <pattern id="hatch{g.idsuf}" width="6" height="6" patternTransform="rotate(45)"
      patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="6" class="hatchline"/>
    </pattern>
  </defs>
  <rect x="{x0:.0f}" y="{g.pad_t}" width="{hatch_x1 - x0:.1f}" height="{y_axis - g.pad_t:.0f}"
    fill="url(#hatch{g.idsuf})" opacity="0.5"/>
  {gridlines}
  <polyline points="{true_pts}" class="line-true"/>
  <polyline points="{roman_pts}" class="line-roman"/>
  <!-- Drawn last so the label sits ON TOP of the gridlines and plot lines. -->
  <rect x="{(x0 + hatch_x1) / 2 - half_lbl:.0f}" y="{g.pad_t + 3:.0f}" width="{g.label_w}"
    height="15" rx="2" class="hatch-hl"/>
  <text x="{(x0 + hatch_x1) / 2:.0f}" y="{g.pad_t + 14:.0f}" class="hatchlabel"
    text-anchor="middle">Roman is blind here</text>
  <rect x="{x0:.0f}" y="{y_axis + 6:.0f}" width="{x1 - x0:.0f}" height="8"
    fill="url(#specbar{g.idsuf})" rx="2"/>
  <text x="{x0:.0f}" y="{g.h - 4:.0f}" class="xtick">380 nm</text>
  <text x="{x1:.0f}" y="{g.h - 4:.0f}" class="xtick" text-anchor="end">780 nm</text>
</svg>"""


def spectrum_svg(
    true_albedo: list[float],
    roman_recon: list[float],
    extrap_below_nm: float,
    compact: bool = False,
) -> str:
    geom = _COMPACT if compact else _WIDE
    return _render(geom, true_albedo, roman_recon, extrap_below_nm)
