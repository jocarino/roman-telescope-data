"""The analytics gate: a build only reports when it was given a key.

This is the one part of the site where a silent mistake costs data rather than pixels. Every
worktree serves its own dist/ on its own port, and the mobile harness reloads pages in a
390px iframe all day; if any of that shipped the tracking snippet it would land in the same
project as real visitors and there is no way to un-mix it afterwards. So the absence of the
snippet is asserted as hard as its presence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from web.build import build

PLANETS_JSON = Path("data/planets.json")
KEY = "phc_testtoken0000000000000000000000000000"

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
