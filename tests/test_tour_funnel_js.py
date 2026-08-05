"""The guided-tour funnel, driven the way a visitor drives it.

`tour_started` → `tour_stop_viewed` → `tour_completed` only means anything if the counting is
right, and every way of getting it wrong is silent: a completion that fires on arrival makes
every shared `#stop-N` link look like a finished walk, a completion that fires twice puts the
completion count above the start count, and a stop event per keypress turns a held arrow key
into a fake progress curve. None of that shows up on the page, so it is pinned here.

tours.js is browser code with no module system, so the shim below plays the part of Alpine:
capture what `Alpine.data` registers, build the component, and re-run the `i` watcher whenever
`i` actually changes — which is all of Alpine's reactivity this component uses.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_TOURS_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "tours.js"

_SHIM = """
const spec = JSON.parse(require("fs").readFileSync(0, "utf8"));
const events = [];
let registered = null;

global.Alpine = { data: (name, fn) => { if (name === "tour") registered = fn; } };
global.window = {
  // The real exoTrack; call sites are guarded against it being absent, which the "silent"
  // spec below exercises.
  exoTrack: spec.tracking ? (name, props) => events.push({ name, props }) : undefined,
  TourStops: null,
};
global.location = { hash: spec.hash || "" };
global.history = { replaceState: () => {} };
global.document = { addEventListener: (evt, fn) => { if (evt === "alpine:init") fn(); } };

require(%s);

const watchers = [];
const c = registered({ n: spec.n, id: spec.id });
// Alpine's magics. $watch fires only on a real change, and $nextTick runs the callback later;
// running it inline is equivalent here because nothing in the callback reads the DOM.
c.$watch = (prop, fn) => watchers.push([prop, fn]);
c.$nextTick = (fn) => fn();
c.$el = { addEventListener: () => {} };
c.init();

// Every navigation the page offers routes through go(); the transport keys, the rail ticks,
// the arrow keys and the swipe handler are all thin wrappers over it.
for (const k of spec.moves) {
  const before = c.i;
  c.go(k);
  if (c.i !== before) watchers.forEach(([p, fn]) => p === "i" && fn());
}
console.log(JSON.stringify({ events, i: c.i }));
"""


def _run(**spec) -> dict:
    spec.setdefault("n", 5)
    spec.setdefault("id", "darkest-worlds")
    spec.setdefault("moves", [])
    spec.setdefault("tracking", True)
    out = subprocess.run(
        ["node", "-e", _SHIM % json.dumps(str(_TOURS_JS))],
        input=json.dumps(spec),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def _names(res: dict) -> list[str]:
    return [e["name"] for e in res["events"]]


def _of(res: dict, name: str) -> list[dict]:
    return [e["props"] for e in res["events"] if e["name"] == name]


pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def test_opening_a_tour_reports_which_tour_it_is() -> None:
    res = _run()
    assert _names(res) == ["tour_started", "tour_stop_viewed"]
    assert _of(res, "tour_started")[0] == {"tour_id": "darkest-worlds", "stops": 5, "entry_stop": 1}
    # Every event carries the tour, so the funnel is one query and not a join.
    assert all(e["props"]["tour_id"] == "darkest-worlds" for e in res["events"])


def test_walking_to_the_end_reports_each_stop_once_and_one_completion() -> None:
    res = _run(n=4, moves=[1, 2, 3])
    assert _names(res) == ["tour_started"] + ["tour_stop_viewed"] * 4 + ["tour_completed"]
    assert [p["stop"] for p in _of(res, "tour_stop_viewed")] == [1, 2, 3, 4]
    assert _of(res, "tour_completed")[0]["stops_seen"] == 4


def test_a_stop_seen_twice_is_reported_once() -> None:
    """Back and forth over the same stops is one visitor reading, not extra progress."""
    res = _run(n=4, moves=[1, 0, 1, 2, 1, 2])
    assert [p["stop"] for p in _of(res, "tour_stop_viewed")] == [1, 2, 3]


def test_skipping_to_the_last_tick_completes_but_says_how_little_was_seen() -> None:
    """The rail lets anyone jump straight to the end. That IS a completion — they reached it —
    but `stops_seen` keeps it distinguishable from a walk."""
    res = _run(n=8, moves=[7])
    assert _of(res, "tour_completed")[0]["stops_seen"] == 2


def test_starting_again_does_not_count_a_second_completion() -> None:
    """START AGAIN then walking back to the end is the same visit. A completion count above
    the start count reads as a bug in the numbers, not as an enthusiastic visitor."""
    res = _run(n=3, moves=[1, 2, 0, 1, 2])
    assert _names(res).count("tour_completed") == 1


def test_a_deep_link_to_the_last_stop_is_not_a_completion() -> None:
    """`#stop-N` links are shareable mid-tour, and the last stop is the one people share from.
    Arriving there is not walking there — completion needs a move."""
    res = _run(n=6, hash="#stop-6")
    assert "tour_completed" not in _names(res)
    assert _of(res, "tour_started")[0]["entry_stop"] == 6
    # And that visit never sees stop 1, so it must not read as dropping out of the opening.
    assert [p["stop"] for p in _of(res, "tour_stop_viewed")] == [6]
    # Stepping back and returning to the end is a real move, and does complete.
    assert "tour_completed" in _names(_run(n=6, hash="#stop-6", moves=[4, 5]))


def test_a_one_stop_tour_completes_on_arrival() -> None:
    """Nowhere to move to: arriving is the whole walk, and the alternative is a tour that can
    never be completed by anyone."""
    assert "tour_completed" in _names(_run(n=1))


def test_an_unkeyed_build_reports_nothing_and_still_walks() -> None:
    """No key, an ad blocker, or a local `exohub serve`: window.exoTrack is simply absent and
    every call site is a no-op. The tour must behave identically."""
    res = _run(n=4, moves=[1, 2, 3], tracking=False)
    assert res["events"] == []
    assert res["i"] == 3
