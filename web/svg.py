"""Build the spectrum plot as a self-contained inline SVG (no chart library, per the spec).

Shows the full-spectrum albedo A(lambda) and the four-band Roman reconstruction, and
hatches the region below the lowest Roman band centre — the blue half Roman is blind to and
can only guess. A spectral gradient bar under the x-axis grounds wavelength in colour.
"""

from __future__ import annotations

import numpy as np

from pipeline.config import GRID_END_NM, GRID_NM, GRID_START_NM

_W, _H = 720, 240
_PAD_L, _PAD_R, _PAD_T, _PAD_B = 44, 16, 16, 40


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


def _x(nm: float) -> float:
    frac = (nm - GRID_START_NM) / (GRID_END_NM - GRID_START_NM)
    return _PAD_L + frac * (_W - _PAD_L - _PAD_R)


def _y(val: float, vmax: float) -> float:
    frac = val / vmax if vmax > 0 else 0.0
    return _H - _PAD_B - frac * (_H - _PAD_T - _PAD_B)


def _polyline(values: np.ndarray, vmax: float) -> str:
    pts = " ".join(f"{_x(nm):.1f},{_y(v, vmax):.1f}" for nm, v in zip(GRID_NM, values, strict=True))
    return pts


def spectrum_svg(true_albedo: list[float], roman_recon: list[float], extrap_below_nm: float) -> str:
    true_a = np.asarray(true_albedo, dtype=float)
    roman_a = np.asarray(roman_recon, dtype=float)
    vmax = max(float(true_a.max()), float(roman_a.max()), 0.05) * 1.1

    x0, x1 = _x(GRID_START_NM), _x(GRID_END_NM)
    y_axis = _H - _PAD_B
    hatch_x1 = _x(extrap_below_nm)

    # Spectral gradient stops for the axis bar.
    stops = []
    for nm in range(int(GRID_START_NM), int(GRID_END_NM) + 1, 20):
        r, g, b = _wavelength_to_rgb(nm)
        off = (nm - GRID_START_NM) / (GRID_END_NM - GRID_START_NM) * 100
        stops.append(f'<stop offset="{off:.0f}%" stop-color="rgb({r},{g},{b})"/>')
    grad = "".join(stops)

    true_pts = _polyline(true_a, vmax)
    roman_pts = _polyline(roman_a, vmax)

    # y gridlines
    gridlines = ""
    for frac in (0.25, 0.5, 0.75, 1.0):
        yy = _H - _PAD_B - frac * (_H - _PAD_T - _PAD_B)
        gridlines += (
            f'<line x1="{x0:.0f}" y1="{yy:.1f}" x2="{x1:.0f}" y2="{yy:.1f}" class="grid"/>'
        )
        gridlines += (
            f'<text x="{x0 - 6:.0f}" y="{yy + 3:.1f}" class="ytick">{frac * vmax:.2f}</text>'
        )

    return f"""<svg viewBox="0 0 {_W} {_H}" class="spectrum" role="img"
  aria-label="Albedo spectrum: full model vs Roman four-band reconstruction">
  <defs>
    <linearGradient id="specbar" x1="0" y1="0" x2="1" y2="0">{grad}</linearGradient>
    <pattern id="hatch" width="6" height="6" patternTransform="rotate(45)"
      patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="6" class="hatchline"/>
    </pattern>
  </defs>
  <rect x="{x0:.0f}" y="{_PAD_T}" width="{hatch_x1 - x0:.1f}" height="{y_axis - _PAD_T:.0f}"
    fill="url(#hatch)" opacity="0.5"/>
  <text x="{(x0 + hatch_x1) / 2:.0f}" y="{_PAD_T + 14:.0f}" class="hatchlabel"
    text-anchor="middle">Roman is blind here</text>
  {gridlines}
  <polyline points="{true_pts}" class="line-true"/>
  <polyline points="{roman_pts}" class="line-roman"/>
  <rect x="{x0:.0f}" y="{y_axis + 6:.0f}" width="{x1 - x0:.0f}" height="8" fill="url(#specbar)"
    rx="2"/>
  <text x="{x0:.0f}" y="{_H - 4:.0f}" class="xtick">380 nm</text>
  <text x="{x1:.0f}" y="{_H - 4:.0f}" class="xtick" text-anchor="end">780 nm</text>
</svg>"""
