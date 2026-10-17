"""The owner's own visits are marked, remembered, and kept out of the numbers.

Cookieless analytics cannot tell the person who built the site from anyone else: there is
no cookie, no login, and the distinct id is a server-side hash that rotates daily. PostHog's
documented answer is a secret URL switch, so `?internal` marks the browser. Three things
have to hold for that to be worth anything: the mark survives to the next page without the
switch (or it would have to be typed on every visit), it is dropped from the address bar so a
copied link doesn't carry it, and it rides on the events as a property the project filter can
see — before the pageview, which PostHog captures a tick after `loaded`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_STATIC = Path(__file__).resolve().parents[1] / "web" / "static"
_ANALYTICS_JS = _STATIC / "analytics.js"

# analytics.js reads the URL, localStorage and window.posthog at load and touches the DOM only
# from handlers, so a handful of stubs is enough to require() it outside a browser. The PostHog
# stub records what init() was given, invokes `loaded` the way the library does, and records
# every register() call. Each case starts from a chosen localStorage so the second visit — the
# one with no switch in the URL — can be tested on its own.
_SHIM = """
const cases = JSON.parse(require("fs").readFileSync(0, "utf8"));
const out = cases.map((c) => {
  const store = Object.assign({}, c.storage || {});
  global.localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
  };
  let written = null, toast = null, registered = null;
  global.location = { pathname: c.pathname || "/", search: c.search || "", hash: c.hash || "" };
  global.history = { replaceState: (_s, _t, url) => { written = url; } };
  global.document = { addEventListener: () => {}, title: "" };
  global.window = {
    history: global.history,
    exoToast: (m) => { toast = m; },
    ExoCampaign: {
      href: (p) => {
        const q = p.toString();
        return (q ? "?" + q : location.pathname) + location.hash;
      },
    },
    EXO_ANALYTICS: { key: "phc_test", api_host: "https://x" },
    posthog: {
      init: (_k, cfg) => { if (cfg.loaded) cfg.loaded(global.window.posthog); },
      register: (p) => { registered = p; },
      on: () => () => {},
      capture: () => {},
    },
  };
  delete require.cache[require.resolve(%s)];
  require(%s);
  return { store, written, toast, registered, tracks: typeof global.window.exoTrack };
});
console.log(JSON.stringify(out));
"""

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _run(cases: list[dict]) -> list[dict]:
    js = json.dumps(str(_ANALYTICS_JS))
    out = subprocess.run(
        ["node", "-e", _SHIM % (js, js)],
        input=json.dumps(cases),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@needs_node
def test_the_switch_marks_this_browser_and_leaves_the_url() -> None:
    (got,) = _run([{"pathname": "/planet/hd-189733-b", "search": "?internal"}])
    assert got["store"] == {"exoInternal": "1"}
    assert got["registered"] == {"$internal_or_test_user": True}
    assert got["written"] == "/planet/hd-189733-b", "the switch must not stay in a copyable URL"
    assert "internal" in got["toast"], "the owner needs to see that it took"
    assert got["tracks"] == "function", "marking must not switch tracking off — it labels it"


@needs_node
def test_the_mark_is_remembered_without_the_switch() -> None:
    """The whole point: PostHog's own recipe needs `?internal` on every visit because it has
    nowhere to remember. This browser does."""
    (got,) = _run([{"pathname": "/", "storage": {"exoInternal": "1"}}])
    assert got["registered"] == {"$internal_or_test_user": True}
    assert got["written"] is None, "nothing to strip, so no URL rewrite"
    assert got["toast"] is None, "no nagging on every page"


@needs_node
def test_an_ordinary_visitor_is_untouched() -> None:
    (got,) = _run([{"pathname": "/", "search": "?utm_source=reddit"}])
    assert got["registered"] is None
    assert got["store"] == {}
    assert got["written"] is None, "campaign tags are stripped AFTER the pageview, not here"


@needs_node
def test_off_forgets_and_keeps_the_other_parameters() -> None:
    (got,) = _run([{
        "pathname": "/",
        "search": "?utm_source=reddit&internal=off",
        "hash": "#roman",
        "storage": {"exoInternal": "1"},
    }])
    assert got["store"] == {}
    assert got["registered"] is None
    assert got["written"] == "?utm_source=reddit#roman", "only ?internal goes; tags and hash stay"
    assert "removed" in got["toast"]


def test_the_mark_is_an_event_property_set_before_the_pageview() -> None:
    """Pinned as text because it is the part a well-meaning edit would 'simplify' away: the
    property goes on via register() inside `loaded`, not via setInternalOrTestUser(), which
    would create a person profile the install promises never to make — and one the daily salt
    discards anyway."""
    js = _ANALYTICS_JS.read_text()
    assert "setInternalOrTestUser" not in js.replace("`setInternalOrTestUser()`", "")
    assert "loaded: function (p)" in js
    assert "p.register({ $internal_or_test_user: true })" in js
