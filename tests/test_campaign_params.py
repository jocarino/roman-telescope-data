"""Campaign tags (?utm_source=…) must survive long enough to be counted, then go away.

Attribution is the one number on this site that cannot be recomputed after the fact: a launch
post is posted once. The tags live only in the query string, and PostHog reads them off the URL
when it captures the pageview — which it does from a `setTimeout(…, 1)` inside its own loader,
NOT inside init(). So every load-time URL rewrite on the site is racing it:

  * the compare page rebuilds ?a=&b= from scratch once its fetch resolves;
  * /sky?planet=<id> drops the query when the arrived-at star is dismissed.

Both used to write `location.pathname` and delete the tags outright. These tests pin the two
halves of the fix: `keep` carries tags through a rewrite, `strip` removes them (and only them)
once the pageview is banked — plus the mechanism in analytics.js that waits for the event
rather than for init() to return, which is the part that looks redundant and isn't.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_STATIC = Path(__file__).resolve().parents[1] / "web" / "static"
_APP_JS = _STATIC / "app.js"

# app.js only touches the DOM from handlers, so a handful of stubs is enough to require() it
# outside a browser. `location`/`history` are read at call time, so each case can swap them.
_SHIM = """
global.window = {};
global.document = { addEventListener: () => {}, createElement: () => ({ getContext: () => null }) };
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
require(%s);

const cases = JSON.parse(require("fs").readFileSync(0, "utf8"));
const out = cases.map((c) => {
  let written = null;
  global.location = { pathname: c.pathname, search: c.search, hash: c.hash || "" };
  global.history = { replaceState: (_s, _t, url) => { written = url; } };
  global.window.history = global.history;
  const C = global.window.ExoCampaign;
  if (c.op === "only") return { url: C.only() };
  if (c.op === "keep") {
    const u = new URLSearchParams(c.preset || "");
    return { url: C.href(C.keep(u)) };
  }
  return { changed: C.strip(), url: written };
});
console.log(JSON.stringify(out));
"""

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _run(cases: list[dict]) -> list[dict]:
    out = subprocess.run(
        ["node", "-e", _SHIM % json.dumps(str(_APP_JS))],
        input=json.dumps(cases),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@needs_node
def test_a_rebuilt_query_carries_the_tags_through() -> None:
    """The compare page's rewrite: its own parameters, plus whatever tagged the visit."""
    (got,) = _run([{
        "op": "keep", "pathname": "/compare.html",
        "search": "?a=jupiter&b=hd-189733-b&utm_source=reddit&utm_campaign=launch",
        "preset": "a=jupiter&b=hd-189733-b",
    }])
    assert got["url"] == "?a=jupiter&b=hd-189733-b&utm_source=reddit&utm_campaign=launch"


@needs_node
def test_dropping_the_sky_deep_link_keeps_the_tag() -> None:
    """/sky?planet=<id> is the most-shared link on the site; ?planet= goes, the tag stays."""
    (got,) = _run([{
        "op": "only", "pathname": "/sky.html",
        "search": "?planet=hd-189733-b&utm_source=reddit&rdt_cid=t3_abc123",
    }])
    assert got["url"] == "?utm_source=reddit&rdt_cid=t3_abc123"


@needs_node
def test_an_untagged_visit_still_gets_a_clean_url() -> None:
    (got,) = _run([{"op": "only", "pathname": "/sky.html", "search": "?planet=earth"}])
    assert got["url"] == "/sky.html"


@needs_node
def test_keep_never_overwrites_the_callers_own_value() -> None:
    (got,) = _run([{
        "op": "keep", "pathname": "/compare.html",
        "search": "?utm_source=reddit", "preset": "utm_source=newsletter",
    }])
    assert got["url"] == "?utm_source=newsletter"


@needs_node
def test_strip_takes_the_tags_and_nothing_else() -> None:
    """Everything that isn't a tag is somebody's state — and the fragment is a scroll
    position, so dropping it would re-jump the page under the reader."""
    (got,) = _run([{
        "op": "strip", "pathname": "/compare.html",
        "search": "?a=jupiter&utm_source=reddit&utm_medium=social&gclid=xyz&b=earth",
        "hash": "#palette",
    }])
    assert got["changed"] is True
    assert got["url"] == "?a=jupiter&b=earth#palette"


@needs_node
def test_strip_of_a_tag_only_url_leaves_the_bare_path() -> None:
    (got,) = _run([{"op": "strip", "pathname": "/sky.html", "search": "?utm_source=hn"}])
    assert got["changed"] is True
    assert got["url"] == "/sky.html"


@needs_node
def test_strip_is_a_no_op_when_there_is_nothing_to_strip() -> None:
    """No replaceState at all: a pointless history entry rewrite on every untagged pageview
    would be churn on 100% of real traffic."""
    cases = [
        {"op": "strip", "pathname": "/sky.html", "search": "?planet=earth"},
        {"op": "strip", "pathname": "/", "search": ""},
        # Near-misses that are NOT campaign tags: no underscore, and a lookalike prefix.
        {"op": "strip", "pathname": "/", "search": "?utm=1&utmx=2&ref=friend"},
    ]
    for got in _run(cases):
        assert got["changed"] is False
        assert got["url"] is None


@needs_node
def test_the_click_ids_the_ad_networks_append_are_covered() -> None:
    ids = ["gclid", "fbclid", "msclkid", "ttclid", "twclid", "rdt_cid", "mc_cid", "igshid"]
    cases = [{"op": "strip", "pathname": "/", "search": f"?{k}=v"} for k in ids]
    for k, got in zip(ids, _run(cases), strict=True):
        assert got["changed"] is True, f"{k} is not treated as a campaign tag"


def test_every_url_rewrite_goes_through_the_helper() -> None:
    """The regression guard. The bug was not a wrong tag list — it was two rewrites that never
    thought about tags at all, so a future third would reintroduce it. Any replaceState that
    writes a path or query must route through ExoCampaign; hash-only ones (section tabs, tour
    stops) never touch the query and are exempt."""
    for js in sorted(_STATIC.glob("*.js")):
        for n, line in enumerate(js.read_text().splitlines(), 1):
            # The call, not the `history.replaceState` capability guards next to it.
            if not re.search(r"replaceState\s*\(", line) or line.lstrip().startswith("//"):
                continue
            ok = "ExoCampaign" in line or "this.href(" in line or re.search(r'"#', line)
            assert ok, f"{js.name}:{n} rewrites the URL without preserving campaign tags"


def test_analytics_waits_for_the_pageview_event() -> None:
    """PostHog captures the pageview a tick after init() returns, so stripping straight after
    init would delete the tag before it was ever read. The hook is what makes the order
    deterministic; without it this whole file is theatre."""
    js = (_STATIC / "analytics.js").read_text()
    assert 'ph.on("eventCaptured"' in js
    assert '"$pageview"' in js
    assert "capture_pageview: true" in js
