"""The analytics gate: a build only reports when it was given a key.

This is the one part of the site where a silent mistake costs data rather than pixels. Every
worktree serves its own dist/ on its own port, and the mobile harness reloads pages in a
390px iframe all day; if any of that shipped the tracking snippet it would land in the same
project as real visitors and there is no way to un-mix it afterwards. So the absence of the
snippet is asserted as hard as its presence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from web.build import build

PLANETS_JSON = Path("data/planets.json")
KEY = "phc_testtoken0000000000000000000000000000"

_ROOT = Path(__file__).resolve().parents[1]
_STATIC = _ROOT / "web" / "static"

# Every way an event name reaches PostHog: `window.exoTrack("x", …)` at a call site, tours.js's
# `_track("x", …)` wrapper, and analytics.js's own internal `send("x", …)`. Deliberately NOT a
# bare `track(` — app.js has a component method of that name whose argument is a palette
# format ("css-vars", "hex"), not an event, and matching it would put junk in the vocabulary.
_EVENT_CALL = re.compile(r'(?<![A-Za-z0-9_$])(?:exoTrack|_track|send)\(\s*"([a-z][a-z0-9_]*)"')


def _emitted_events() -> set[str]:
    """Every event name the shipped front-end can actually send."""
    return {n for p in sorted(_STATIC.glob("*.js")) for n in _EVENT_CALL.findall(p.read_text())}

pytestmark = pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")


def _tiny(tmp_path: Path) -> Path:
    """A three-planet source file — this is about the <head>, not the catalogue."""
    doc = json.loads(PLANETS_JSON.read_text())
    doc["planets"] = doc["planets"][:3]
    src = tmp_path / "planets.json"
    src.write_text(json.dumps(doc))
    return src


def _pages(root: Path) -> list[tuple[Path, str]]:
    return [
        (p, p.read_text())
        for p in sorted(root.rglob("*.html"))
        if "fragments" not in p.parts
    ]


def test_no_key_means_no_analytics_anywhere(tmp_path):
    out = build(_tiny(tmp_path), tmp_path / "dist", og_cards=False)
    for path, html in _pages(out):
        low = html.lower()
        assert "posthog" not in low, f"{path.name} carries analytics in an unkeyed build"
        assert "analytics.js" not in low, path.name
        assert "exo_analytics" not in low, path.name


def test_key_wires_every_page(tmp_path):
    out = build(_tiny(tmp_path), tmp_path / "dist", og_cards=False, posthog_key=KEY)
    pages = _pages(out)
    assert pages
    for path, html in pages:
        assert KEY in html, f"{path.name} is missing the project token"
        assert "/static/analytics.js" in html, path.name
        assert "https://eu-assets.i.posthog.com/static/array.js" in html, path.name
        # Deferred, so nothing on the page ever waits on an analytics request.
        assert '<script src="/static/analytics.js' in html and "defer" in html, path.name


def test_hosts_are_overridable(tmp_path):
    out = build(
        _tiny(tmp_path),
        tmp_path / "dist",
        og_cards=False,
        posthog_key=KEY,
        posthog_api_host="https://ph.example.test/",
        posthog_assets_host="https://assets.example.test/",
    )
    html = (out / "index.html").read_text()
    # Trailing slashes are stripped, or the emitted URL would double up.
    assert "https://assets.example.test/static/array.js" in html
    assert '"https://ph.example.test"' in html
    assert "eu.i.posthog.com" not in html


def test_the_shipped_script_keeps_its_privacy_promises(tmp_path):
    """The README tells visitors there is no cookie and no banner, and the project settings
    are configured for cookieless ingestion. If someone flips one of these the claim silently
    becomes false, so pin all three."""
    out = build(_tiny(tmp_path), tmp_path / "dist", og_cards=False, posthog_key=KEY)
    js = (out / "static" / "analytics.js").read_text()
    assert 'cookieless_mode: "always"' in js
    assert "autocapture: false" in js
    assert "disable_session_recording: true" in js


# ── The vocabulary ──────────────────────────────────────────────────────────────
# The README calls the event list "fixed" and tells the next person that adding one is a
# guarded line at the call site plus a line in that list. Nothing enforced the second half, so
# an event could ship and be invisible to everyone reading the docs — which is how the site
# ended up with a tours page and a hold-to-peek gesture that reported nothing at all.


def test_every_event_is_in_the_readme_vocabulary():
    readme = (_ROOT / "README.md").read_text()
    missing = sorted(n for n in _emitted_events() if f"`{n}`" not in readme)
    assert not missing, (
        f"events emitted by web/static/*.js but absent from the README list: {missing}. "
        "Add them there, or the vocabulary stops being the documentation it claims to be."
    )


def test_the_untracked_gestures_report():
    """Guided tours and hold-to-peek were the two blind spots: a tour could be opened and
    nothing after it was visible, and a peek is a fetch of a static fragment — no navigation,
    no pageview, nothing. Both are the mobile-heavy end of the site, so their absence bent the
    numbers in exactly one direction."""
    wanted = {"tour_started", "tour_stop_viewed", "tour_completed", "peek_opened"}
    assert wanted <= _emitted_events()

    # Guarded like every other call site, so an unkeyed build and an ad-blocked page behave
    # identically to a reporting one.
    assert 'window.exoTrack && window.exoTrack("peek_opened"' in (_STATIC / "app.js").read_text()
    assert "if (!window.exoTrack) return;" in (_STATIC / "tours.js").read_text()


def test_tour_pages_name_the_tour_they_are(tmp_path):
    """Without the id in x-data every tour event reads `tour_id: ""` and the whole funnel
    collapses into one undifferentiated walk."""
    out = build(_tiny(tmp_path), tmp_path / "dist", og_cards=False, posthog_key=KEY)
    pages = [p for p in (out / "tours").glob("*.html") if p.name != "index.html"]
    assert pages, "no tour pages were built, so this test checked nothing"
    for p in pages:
        # The id is written through tojson|forceescape, because a raw double quote would end
        # the attribute. Which entity form the escaper picks is its business — the HTML parser
        # hands Alpine the decoded string either way — so compare after decoding.
        html = p.read_text().replace("&#34;", '"').replace("&quot;", '"')
        assert f'id: "{p.stem}"' in html, p.name
