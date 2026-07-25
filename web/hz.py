"""The habitable-zone strip: this planet's orbit against its star's liquid-water zone,
as a self-contained inline SVG (no chart library, same approach as web/svg.py, web/sky.py).

One axis: distance from the host star, logarithmic because a single system spans orbits
from 0.01 AU to 100 AU while the zone itself is a narrow band. The star sits at the left,
the zone is drawn as two nested bands (optimistic outside, conservative inside) and the
planet is an open square marker — never a filled dot, for the same reason as the sky
chart: it must read as a MARKER, not as a pretend photograph.

Two geometries, as everywhere else: a wide desktop face and a compact face for phones.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pipeline.models import Habitability, PlanetRecord

# Ticks we are willing to label, in AU. Only those inside the drawn range appear.
_TICKS = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)


@dataclass(frozen=True)
class _Geom:
    w: int
    h: int
    pad_l: int
    pad_r: int
    axis_y: int  # the baseline the bands and markers sit on
    band_h: int
    extra_class: str = ""


_WIDE = _Geom(w=720, h=132, pad_l=54, pad_r=22, axis_y=74, band_h=34)
_COMPACT = _Geom(w=400, h=140, pad_l=44, pad_r=16, axis_y=82, band_h=32, extra_class=" compact")


def _fmt_au(au: float) -> str:
    """Distances span four decades, so pick the precision from the magnitude. Trailing zeros
    are stripped so a row of ticks reads 0.01 / 0.1 / 1 rather than 0.010 / 0.10 / 1.00."""
    if au >= 10:
        return f"{au:.0f}"
    if au >= 1:
        return f"{au:.2f}".rstrip("0").rstrip(".")
    if au >= 0.1:
        return f"{au:.2f}".rstrip("0").rstrip(".")
    return f"{au:.3f}".rstrip("0").rstrip(".")


def hz_strip_svg(rec: PlanetRecord, compact: bool = False) -> str | None:
    """The strip for one planet, or None if its zone was not computable."""
    hab: Habitability | None = rec.habitability
    a = rec.params.semi_major_axis_au
    if hab is None or a is None or a <= 0:
        return None
    if hab.optimistic_inner_au is None or hab.optimistic_outer_au is None:
        return None
    if hab.inner_au is None or hab.outer_au is None:
        return None

    g = _COMPACT if compact else _WIDE
    x0, x1 = float(g.pad_l), float(g.w - g.pad_r)

    # Log range: always show the whole zone plus the planet, with a margin either side so
    # neither the marker nor the outer band edge ever touches the frame.
    lo = min(a, hab.optimistic_inner_au) / 2.2
    hi = max(a, hab.optimistic_outer_au) * 2.2
    llo, lhi = math.log10(lo), math.log10(hi)

    def px(au: float) -> float:
        frac = (math.log10(au) - llo) / (lhi - llo)
        return x0 + min(max(frac, 0.0), 1.0) * (x1 - x0)

    top = g.axis_y - g.band_h / 2
    opt_x0, opt_x1 = px(hab.optimistic_inner_au), px(hab.optimistic_outer_au)
    con_x0, con_x1 = px(hab.inner_au), px(hab.outer_au)

    bands = (
        f'<rect x="{opt_x0:.1f}" y="{top:.1f}" width="{max(opt_x1 - opt_x0, 1):.1f}" '
        f'height="{g.band_h}" class="hz-band opt"/>'
        f'<rect x="{con_x0:.1f}" y="{top:.1f}" width="{max(con_x1 - con_x0, 1):.1f}" '
        f'height="{g.band_h}" class="hz-band cons"/>'
    )

    # Axis + decade ticks. The axis is the orbit line: distance from the star, left to right.
    axis = f'<line x1="{x0:.1f}" y1="{g.axis_y}" x2="{x1:.1f}" y2="{g.axis_y}" class="hz-axis"/>'
    ticks = ""
    for t in _TICKS:
        if not (lo <= t <= hi):
            continue
        xx = px(t)
        # The star marker owns the left end of the axis and carries its own label on the
        # same baseline; a decade tick landing under it would print the two on top of
        # each other, so the star wins and the tick is dropped.
        if xx - x0 < 34:
            continue
        ticks += (
            f'<line x1="{xx:.1f}" y1="{g.axis_y - 4}" x2="{xx:.1f}" y2="{g.axis_y + 4}" '
            f'class="hz-tick"/>'
            f'<text x="{xx:.1f}" y="{g.h - 6}" class="tick" text-anchor="middle">'
            f"{_fmt_au(t)}</text>"
        )

    # The star: an open marker hard against the left edge, labelled with its name.
    star = (
        f'<line x1="{x0:.1f}" y1="{g.axis_y - 9}" x2="{x0:.1f}" y2="{g.axis_y + 9}" '
        f'class="hz-star"/>'
        f'<line x1="{x0 - 9:.1f}" y1="{g.axis_y}" x2="{x0 + 9:.1f}" y2="{g.axis_y}" '
        f'class="hz-star"/>'
        f'<text x="{x0:.1f}" y="{g.h - 6}" class="tick" text-anchor="middle">star</text>'
    )

    # The planet marker: open square + a label that flips to whichever side has room.
    mx = px(a)
    m = 6
    flip = mx > (x0 + x1) / 2
    lx, anchor = (mx - m - 5, "end") if flip else (mx + m + 5, "start")
    marker = (
        f'<line x1="{mx:.1f}" y1="{top - 12:.1f}" x2="{mx:.1f}" y2="{g.axis_y + 12:.1f}" '
        f'class="hz-orbit"/>'
        f'<rect x="{mx - m:.1f}" y="{g.axis_y - m}" width="{2 * m}" height="{2 * m}" '
        f'class="hz-mark"/>'
        f'<text x="{lx:.1f}" y="{top - 4:.1f}" class="hz-label" text-anchor="{anchor}">'
        f"{_fmt_au(a)} AU</text>"
    )

    # Zone-edge callouts under the band: the conservative edges, which are the ones a reader
    # is most likely to want to compare against the planet's own distance.
    # A narrow band would print the two numbers on top of each other, so once they get close
    # they turn outward and hang off their own edge instead of centring on it.
    edge_y = top + g.band_h + 13
    tight = (con_x1 - con_x0) < 62
    lx0, la = (con_x0 - 3, "end") if tight else (con_x0, "middle")
    lx1, ra = (con_x1 + 3, "start") if tight else (con_x1, "middle")
    edges = (
        f'<text x="{lx0:.1f}" y="{edge_y:.1f}" class="hz-edge" '
        f'text-anchor="{la}">{_fmt_au(hab.inner_au)}</text>'
        f'<text x="{lx1:.1f}" y="{edge_y:.1f}" class="hz-edge" '
        f'text-anchor="{ra}">{_fmt_au(hab.outer_au)}</text>'
    )

    zone_word = {
        "conservative": "inside the habitable zone",
        "optimistic": "at the optimistic edge of the habitable zone",
        "too-hot": "closer to its star than the habitable zone",
        "too-cold": "further from its star than the habitable zone",
    }.get(hab.zone, "at an uncomputable distance")
    alt = (
        f"Orbit diagram: {rec.name} orbits at {_fmt_au(a)} AU, {zone_word}, which for this "
        f"star runs {_fmt_au(hab.inner_au)} to {_fmt_au(hab.outer_au)} AU."
    )

    return f"""<svg viewBox="0 0 {g.w} {g.h}" class="hzstrip{g.extra_class}" role="img"
  aria-label="{alt}">
  {bands}
  {axis}
  {ticks}
  {edges}
  {star}
  {marker}
</svg>"""
