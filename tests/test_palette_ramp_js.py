"""The browser derives the 5-stop ramp itself; it must agree with Python exactly.

The gallery index used to ship `palette` and `rpal` — ten hexes per planet — for something
that is a pure function of a base hex the index already carries. That was ~29% of the file,
so the ramp is now recomputed client-side by PlanetRender.ramp(). The same ramp is still
rendered server-side on planet and tour pages, so the two implementations sit side by side on
one screen and any drift would show as a seam.

These are the traps that actually bit, both worth keeping pinned:
  * Python's round() sends halves to even, JS's Math.round sends them up;
  * the lightness stops are COMPUTED (0.18 + (0.88-0.18)*i/4), and 0.88-0.18 is not exactly
    0.7, so writing the stops out as literals shifts a channel across a .5 boundary.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pipeline.palette.derive import derive_palette_from_hex

_RENDER_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "planet-render.js"

# planet-render.js reaches for a WebGL context at call time, not at load time, so a couple of
# stubs are enough to require() it outside a browser.
_SHIM = """
global.window = {};
global.document = { createElement: () => ({ getContext: () => null }) };
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
require(%s);
const hexes = JSON.parse(require("fs").readFileSync(0, "utf8"));
console.log(JSON.stringify(hexes.map((h) => global.window.PlanetRender.ramp(h))));
"""


def _js_ramps(hexes: list[str]) -> list[list[str]]:
    script = _SHIM % json.dumps(str(_RENDER_JS))
    out = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(hexes),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


# Neutrals, saturated primaries, near-black and near-white (the ends of the HLS round-trip),
# and the specific hexes whose tint-2 stop lands exactly on a rounding boundary.
_HEXES = [
    "#000000", "#ffffff", "#808080", "#7f7f7f",
    "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff", "#ff00ff",
    "#010203", "#fefdfc", "#c2c2ff", "#64b6ff", "#ddc8b5",
    "#e4c896", "#d3cda3", "#ffb9b7", "#fdbbb9", "#e5c891",
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_ramp_matches_python_exactly() -> None:
    want = [[s.hex for s in derive_palette_from_hex(h)] for h in _HEXES]
    assert _js_ramps(_HEXES) == want


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_ramp_matches_python_across_the_hex_cube() -> None:
    """A coarse sweep of the whole RGB cube, to catch boundary cases no fixture would name."""
    hexes = [
        f"#{r:02x}{g:02x}{b:02x}"
        for r in range(0, 256, 37)
        for g in range(0, 256, 41)
        for b in range(0, 256, 43)
    ]
    want = [[s.hex for s in derive_palette_from_hex(h)] for h in hexes]
    assert _js_ramps(hexes) == want


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_ramp_returns_five_stops_and_tolerates_junk() -> None:
    """A missing or malformed hex must not throw — a card still has to render."""
    for bad in ("", "#xyz", "not-a-colour"):
        assert len(_js_ramps([bad])[0]) == 5
