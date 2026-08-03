"""The spectrum polyline is simplified for size; it must still draw the identical shape."""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.config import GRID_NM
from web import svg as S


def _naive(g: S._Geom, values: np.ndarray, vmax: float) -> str:
    """The unsimplified step chart: a point per grid step, horizontal then vertical."""
    xs = [S._x(g, nm) for nm in GRID_NM]
    ys = [S._y(g, v, vmax) for v in values]
    pts = []
    for i in range(len(xs)):
        pts.append(f"{xs[i]:.1f},{ys[i]:.1f}")
        if i + 1 < len(xs):
            pts.append(f"{xs[i + 1]:.1f},{ys[i]:.1f}")
    return " ".join(pts)


def _covered(points: str) -> set[tuple[float, float]]:
    """Rasterise a polyline of axis-aligned segments at 0.05 units, as a set of points."""
    pts = [tuple(map(float, p.split(","))) for p in points.split()]
    cov: set[tuple[float, float]] = set()
    for (px0, py0), (px1, py1) in zip(pts, pts[1:], strict=False):
        if py0 == py1:
            lo, hi = sorted((px0, px1))
            n = int(round((hi - lo) / 0.05))
            cov.update((round(lo + k * 0.05, 2), round(py0, 2)) for k in range(n + 1))
        elif px0 == px1:
            lo, hi = sorted((py0, py1))
            n = int(round((hi - lo) / 0.05))
            cov.update((round(px0, 2), round(lo + k * 0.05, 2)) for k in range(n + 1))
        else:
            raise AssertionError(f"non-axis-aligned segment: {(px0, py0)} -> {(px1, py1)}")
    return cov


# A flat trace (the worst case for the old emitter, and what the band-limited Roman
# reconstruction looks like), a monotonic ramp, a sawtooth, and pure noise.
_N = len(GRID_NM)
_CASES = {
    "flat": np.full(_N, 0.42),
    "ramp": np.linspace(0.05, 0.9, _N),
    "steps": np.repeat([0.2, 0.6, 0.35, 0.8], _N // 4 + 1)[:_N],
    "sawtooth": np.abs(np.arange(_N) % 10 - 5) / 10.0,
    "noise": np.abs(np.sin(np.arange(_N) * 2.7)) * 0.8,
}


@pytest.mark.parametrize("name", sorted(_CASES))
@pytest.mark.parametrize("geom", [S._WIDE, S._COMPACT], ids=["wide", "compact"])
def test_simplified_polyline_draws_the_same_shape(name: str, geom: S._Geom) -> None:
    values = _CASES[name]
    vmax = max(float(values.max()), 0.05) * 1.1
    assert _covered(S._stepped(geom, values, vmax)) == _covered(_naive(geom, values, vmax))


@pytest.mark.parametrize("name", sorted(_CASES))
def test_no_repeated_points(name: str) -> None:
    values = _CASES[name]
    pts = S._stepped(S._WIDE, values, max(float(values.max()), 0.05) * 1.1).split()
    assert all(a != b for a, b in zip(pts, pts[1:], strict=False)), "duplicate point emitted"


def test_flat_trace_collapses_to_its_endpoints() -> None:
    """A constant albedo is one horizontal run, so it needs exactly two points."""
    values = _CASES["flat"]
    pts = S._stepped(S._WIDE, values, max(float(values.max()), 0.05) * 1.1).split()
    assert len(pts) == 2, pts


def test_simplification_actually_shrinks_a_realistic_trace() -> None:
    values = _CASES["steps"]
    vmax = max(float(values.max()), 0.05) * 1.1
    assert len(S._stepped(S._WIDE, values, vmax)) < len(_naive(S._WIDE, values, vmax)) / 2
