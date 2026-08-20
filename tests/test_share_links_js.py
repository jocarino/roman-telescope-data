"""A copied link must reproduce the view: the gallery's filters and the planet page's scope.

"Look at this" only works if the URL carries what was on screen. Both pages keep their
non-default state in the query string (ExoShare.sync) and copy the same URL made absolute
(ExoShare.url). These tests pin the round trip — what is written is what is read back — and
the two rules that keep it honest: defaults are omitted (the plain URL stays plain), and a
setting the target planet cannot show (no Sun-swap, no map) is ignored rather than half-applied.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_APP_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "app.js"

# app.js registers its components on alpine:init; the shim captures that listener and fires it
# against a stub Alpine, then drives the `detail` / `gallery` factories directly.
_SHIM = """
const listeners = {};
global.window = {};
global.document = {
  addEventListener: (n, f) => { listeners[n] = f; },
  createElement: () => ({ getContext: () => null }),
  querySelector: () => null, readyState: "complete",
  referrer: "",
};
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
// Node ships a read-only `navigator` of its own; define over it.
Object.defineProperty(globalThis, "navigator", { configurable: true,
  value: { clipboard: { writeText: (t) => { global.copied = t; } } } });
const comps = {};
global.Alpine = { data: (n, f) => { comps[n] = f; } };
require(%s);
listeners["alpine:init"]();

const cases = JSON.parse(require("fs").readFileSync(0, "utf8"));
const out = cases.map((c) => {
  let written = null;
  global.copied = null;
  global.location = { origin: "https://x.test", pathname: c.pathname,
    search: c.search || "", hash: "" };
  global.history = { replaceState: (_s, _t, url) => { written = url; } };
  global.window.history = global.history;
  const store = Object.assign({}, c.storage || {});
  global.localStorage = { getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = v; }, removeItem: (k) => { delete store[k]; } };
  if (c.page === "detail") {
    const d = comps.detail(c.init || {});
    d.$refs = {};
    d.init();
    if (c.apply) { Object.assign(d, c.apply); d._syncUrl(); }
    d.copyLink();
    return { params: d.shareParams().toString(), written, copied: global.copied,
      state: { view: d.view, illum: d.illum, fidelity: d.fidelity, heroStyle: d.heroStyle,
        heroSource: d.heroSource, phaseIdx: d.phaseIdx, phasePlay: d.phasePlay,
        obsIdx: d.obsIdx } };
  }
  const g = comps.gallery({});
  const any = g._applyShareParams(new URLSearchParams(c.search || ""));
  if (c.apply) Object.assign(g, c.apply);
  g._syncUrl();
  g.copyLink();
  const state = {};
  g._filterKeys.forEach((k) => { state[k] = g[k]; });
  return { any, params: g.shareParams().toString(), written, copied: global.copied, state };
});
console.log(JSON.stringify(out));
"""

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

_PHASES = [{"d": d, "h": "#336699", "l": 0.3} for d in range(0, 181, 10)]
_DETAIL = {
    "fullHex": "#336699", "romanHex": "#446688", "fullLum": 0.3, "romanLum": 0.3,
    "fullPalette": ["#111111"], "romanPalette": ["#222222"],
    "phases": _PHASES, "map": None, "obs": [],
}


def _run(cases: list[dict]) -> list[dict]:
    out = subprocess.run(
        ["node", "-e", _SHIM % json.dumps(str(_APP_JS))],
        input=json.dumps(cases), capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def _detail(**kw) -> dict:
    c = {"page": "detail", "pathname": "/planet/x/", "init": dict(_DETAIL)}
    c.update(kw)
    return c


# ---- planet page ---------------------------------------------------------------------------

def test_a_fresh_planet_page_shares_its_plain_url():
    (r,) = _run([_detail()])
    assert r["params"] == ""
    assert r["copied"] == "https://x.test/planet/x/"
    assert r["written"] is None  # nothing to write: the URL already equals the view


def test_every_knob_is_written_and_read_back():
    init = dict(_DETAIL, hasSun=True, sunHex="#abcdef", sunLum=0.3, sunPalette=["#333333"],
                obs=[{"telescope": "VLT"}, {"telescope": "JWST"}])
    (w,) = _run([_detail(init=init, apply={
        "view": "full", "illum": "sun", "fidelity": "stylised", "heroStyle": "smooth",
        "heroSource": "telescope", "obsIdx": 1, "phaseIdx": 9, "phasePlay": False,
    })])
    assert w["params"] == ("light=sun&style=stylised&shape=sphere&source=telescope"
                           "&telescope=JWST&phase=90")
    (r,) = _run([_detail(init=init, search="?" + w["params"])])
    assert r["state"] == {
        "view": "full", "illum": "sun", "fidelity": "stylised", "heroStyle": "smooth",
        "heroSource": "telescope", "phaseIdx": 9, "phasePlay": False, "obsIdx": 1,
    }
    assert r["copied"] == "https://x.test/planet/x/?" + w["params"]


def test_a_linked_scope_beats_the_remembered_one():
    stored = {"scopeView": "full", "planetStyle": "smooth", "renderFidelity": "stylised"}
    (r,) = _run([_detail(search="?view=roman&shape=pixel", storage=stored)])
    assert r["state"]["view"] == "roman"
    assert r["state"]["heroStyle"] == "retro"
    assert r["state"]["fidelity"] == "stylised"  # a knob the link did not name keeps its value
    assert r["params"] == "view=roman&style=stylised"


def test_settings_this_planet_cannot_show_are_ignored():
    (r,) = _run([_detail(search="?light=sun&source=map&telescope=JWST&phase=40")])
    assert r["state"]["illum"] == "native"    # no Sun-swap data
    assert r["state"]["heroSource"] == "model"  # no real map
    assert r["state"]["phaseIdx"] == 4 and r["state"]["phasePlay"] is False
    assert r["params"] == "phase=40"


def test_a_playing_phase_cycle_writes_no_phase():
    (r,) = _run([_detail(apply={"phasePlay": True, "phaseIdx": 7})])
    assert "phase" not in r["params"]


def test_phase_snaps_to_the_nearest_lit_stop():
    a, b = _run([_detail(search="?phase=94"), _detail(search="?phase=999")])
    assert a["state"]["phaseIdx"] == 9
    assert b["state"]["phaseIdx"] == len(_PHASES) - 2  # never the unlit 180° stop


def test_address_bar_follows_the_knobs_and_keeps_campaign_tags():
    (r,) = _run([_detail(search="?utm_source=launch", apply={"view": "roman"})])
    assert r["written"] == "?view=roman&utm_source=launch"  # the tag survives the rewrite
    assert r["copied"] == "https://x.test/planet/x/?view=roman"  # the shared link drops the tag


# ---- gallery -------------------------------------------------------------------------------

def test_gallery_filters_round_trip_through_the_url():
    (w,) = _run([{"page": "gallery", "pathname": "/", "apply": {
        "q": "kepler", "obs": "photo", "ptype": "hot-jupiter", "distBand": "near",
        "hz": "water", "fic": True, "sort": "lum", "nearId": "hd-189733-b", "view": "roman",
    }}])
    params = w["params"]
    assert params == ("q=kepler&obs=photo&type=hot-jupiter&dist=near&hz=water&fiction=1"
                      "&sort=lum&near=hd-189733-b&view=roman")
    assert w["copied"] == "https://x.test/?" + params
    (r,) = _run([{"page": "gallery", "pathname": "/", "search": "?" + params}])
    assert r["any"] is True
    assert r["state"] == {
        "q": "kepler", "obs": "photo", "roman": "all", "ptype": "hot-jupiter", "disc": "all",
        "distBand": "near", "hz": "water", "family": None, "fic": True, "sort": "lum",
        "nearId": "hd-189733-b",
    }


def test_the_old_deep_links_still_work_and_junk_is_dropped():
    (r,) = _run([{"page": "gallery", "pathname": "/",
                  "search": "?fiction=1&type=not-a-type&sort=nope"}])
    assert r["any"] is True
    assert r["state"]["fic"] is True
    assert r["state"]["ptype"] == "all" and r["state"]["sort"] == "curated"
    assert r["params"] == "fiction=1"


def test_a_bare_front_door_names_no_filter():
    (r,) = _run([{"page": "gallery", "pathname": "/", "search": "?utm_source=x"}])
    assert r["any"] is False
    assert r["params"] == ""
    assert r["written"] is None
