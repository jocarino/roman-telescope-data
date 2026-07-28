"""The "go outside and look at it" star chart: a whole-sky equatorial map as an inline SVG
(no chart library, same approach as web/svg.py).

The map is an equirectangular plot of the J2000 sky with right ascension increasing to
the LEFT (the astronomical chart convention — the sky as seen from inside the celestial
sphere), so the tick labels run 24h → 0h and make the flip explicit. Every faint dot is a
host star from this catalog; the target host is crosshaired in the accent colour with its
constellation named. Like the spectrum plot, two geometries are emitted: a wide desktop
face and a compact near-square face whose labels stay legible on a phone.

The chart splits in two. The ~5.8k dots are the same on every planet page — only the
crosshair moves — so they live in one shared file per geometry (`sky_field_svg`) that each
chart pulls in through <image>; the per-page part is just the frame, graticule and marker.
Inlined, those dots were 93% of a planet page and ~4.4 GB of a 4.5 GB dist. One consequence
is deliberate: a shared field is one file for every page, so it cannot leave a different
star out each time, and the target keeps its own dot underneath the crosshair.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.models import SkyPosition


@dataclass(frozen=True)
class _Geom:
    w: int
    h: int
    pad_l: int
    pad_r: int
    pad_t: int
    pad_b: int
    ra_label_hours: tuple[int, ...]  # which hour lines get a tick label
    extra_class: str = ""


_WIDE = _Geom(
    w=720, h=300, pad_l=44, pad_r=16, pad_t=14, pad_b=30, ra_label_hours=(0, 6, 12, 18, 24)
)
_COMPACT = _Geom(
    w=400,
    h=260,
    pad_l=40,
    pad_r=12,
    pad_t=12,
    pad_b=28,
    ra_label_hours=(0, 12, 24),
    extra_class=" compact",
)


def _x(g: _Geom, ra_deg: float) -> float:
    # RA increases leftward (chart convention): 0h at the right edge, 24h at the left.
    frac = 1.0 - (ra_deg % 360.0) / 360.0
    return g.pad_l + frac * (g.w - g.pad_l - g.pad_r)


def _y(g: _Geom, dec_deg: float) -> float:
    frac = (90.0 - dec_deg) / 180.0
    return g.pad_t + frac * (g.h - g.pad_t - g.pad_b)


# The dot colour is baked into the shared field file rather than read from style.css: an SVG
# pulled in through <image> is its own document and page CSS cannot reach inside it. Keep this
# in step with `.skychart .skydot` in web/static/style.css.
_DOT_FILL = "rgba(205,216,242,.34)"


def sky_field_svg(catalog_points: list[tuple[float, float]], compact: bool = False) -> str:
    """The catalogue starfield on its own, as a standalone SVG document.

    This is the same set of dots on every planet page — only the crosshair moves — so it is
    built once per geometry and referenced, instead of being inlined into all ~5.8k pages.
    Emitted as one <rect> per star, deliberately: the dots are 34% opaque, and where many
    overlap (the Kepler field above all) each one paints over the last and the pile-up reads
    as a bright clump. That brightness is the map saying "an enormous number of known planets
    are here", so it has to survive. Merging them into a single filled path would be a third
    of the bytes and would flatten exactly that signal.
    """
    g = _COMPACT if compact else _WIDE
    dots = "".join(
        f'<rect x="{_x(g, ra) - 1:.1f}" y="{_y(g, dec) - 1:.1f}" width="2" height="2"/>'
        for ra, dec in catalog_points
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {g.w} {g.h}" '
        f'width="{g.w}" height="{g.h}">'
        f"<style>rect{{fill:{_DOT_FILL}}}</style>{dots}</svg>"
    )


def sky_chart_svg(
    sky: SkyPosition,
    catalog_points: list[tuple[float, float]],
    compact: bool = False,
    field_url: str | None = None,
) -> str:
    g = _COMPACT if compact else _WIDE
    # Frame edges directly (never through _x, whose modulo folds 24h onto 0h).
    x0, x1 = float(g.pad_l), float(g.w - g.pad_r)
    y0, y1 = _y(g, 90.0), _y(g, -90.0)

    # Graticule: an hour line every 3h, a declination line every 30 degrees. The celestial
    # equator gets its own class so it reads slightly brighter than the rest of the grid.
    grid = ""
    for hr in range(0, 25, 3):
        xx = x0 + (1.0 - hr / 24.0) * (x1 - x0)
        grid += f'<line x1="{xx:.1f}" y1="{y0:.1f}" x2="{xx:.1f}" y2="{y1:.1f}" class="grid"/>'
        if hr in g.ra_label_hours:
            anchor = "start" if hr == 24 else ("end" if hr == 0 else "middle")
            grid += (
                f'<text x="{xx:.1f}" y="{g.h - 8:.0f}" class="tick" '
                f'text-anchor="{anchor}">{hr}h</text>'
            )
    for dec in (-60, -30, 0, 30, 60):
        yy = _y(g, dec)
        cls = "grid eq" if dec == 0 else "grid"
        grid += f'<line x1="{x0:.1f}" y1="{yy:.1f}" x2="{x1:.1f}" y2="{yy:.1f}" class="{cls}"/>'
        if dec in (-60, 0, 60):
            lbl = f"{dec:+d}°" if dec else "0°"
            grid += (
                f'<text x="{x0 - 5:.1f}" y="{yy + 3:.1f}" class="tick" '
                f'text-anchor="end">{lbl}</text>'
            )

    # Every host star in the catalog: faint 2x2 pixel dots (the retro starfield is the data
    # itself). With a field_url the dots come from the one shared file (see sky_field_svg) and
    # the target keeps its own dot, sitting under the crosshair — a shared field is one file
    # for every page and so cannot leave a different star out each time. At 2x2 under a 10x10
    # hollow marker it does not read as a data point, and the marker still says "you are here".
    # Without a field_url the dots are inlined and the target is skipped, as before.
    if field_url:
        dots = f'<image href="{field_url}" x="0" y="0" width="{g.w}" height="{g.h}"/>'
    else:
        dots = "".join(
            f'<rect x="{_x(g, ra) - 1:.1f}" y="{_y(g, dec) - 1:.1f}" '
            f'width="2" height="2" class="skydot"/>'
            for ra, dec in catalog_points
            if not (abs(ra - sky.ra_deg) < 1e-6 and abs(dec - sky.dec_deg) < 1e-6)
        )

    # Crosshair through the target host, with an open square marker (never a filled dot —
    # the star must stay visibly a MARKER, not a pretend photograph of anything).
    tx, ty = _x(g, sky.ra_deg), _y(g, sky.dec_deg)
    m = 5  # marker half-size
    label = sky.constellation.upper()
    # Flip the label to whichever side has room, and keep it off the chart edges.
    lx, anchor = (tx - 10, "end") if tx > (x0 + x1) / 2 else (tx + 10, "start")
    ly = max(ty - 8, g.pad_t + 12)
    marker = (
        f'<line x1="{tx:.1f}" y1="{y0:.1f}" x2="{tx:.1f}" y2="{y1:.1f}" class="xhair"/>'
        f'<line x1="{x0:.1f}" y1="{ty:.1f}" x2="{x1:.1f}" y2="{ty:.1f}" class="xhair"/>'
        f'<rect x="{tx - m:.1f}" y="{ty - m:.1f}" width="{2 * m}" height="{2 * m}" '
        f'class="skymark"/>'
        f'<text x="{lx:.1f}" y="{ly:.1f}" class="skylabel" text-anchor="{anchor}">{label}</text>'
    )

    # data-* attrs + the empty hzn group feed the client-side "your horizon" overlay
    # (app.js): it needs the plot rectangle and the target's coordinates to draw the
    # observer's horizon at the visitor's clock time. Layered after the dots so the
    # ground shading dims them, before the marker so the crosshair stays on top.
    return f"""<svg viewBox="0 0 {g.w} {g.h}" class="skychart{g.extra_class}" role="img"
  data-x0="{x0:.1f}" data-x1="{x1:.1f}" data-y0="{y0:.1f}" data-y1="{y1:.1f}"
  data-ra="{sky.ra_deg:.4f}" data-dec="{sky.dec_deg:.4f}"
  aria-label="Star chart: the host star's position in the sky, in {sky.constellation}">
  <rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" class="skyframe"/>
  {grid}
  {dots}
  <g class="hzn"></g>
  {marker}
</svg>"""
