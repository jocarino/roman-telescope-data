"""The sticky section tabs must never point at a section that is not on the page.

Three of the five sections are conditional — the sky chart needs a data release carrying sky
positions, "Seen in fiction" needs the planet to appear in the curated overlay, and the water
verdict needs the host star measured well enough to place a habitable zone. The tab bar
therefore repeats those conditions, and a repeated condition is a condition that can drift.

The failure is silent and only on some planets: a tab that scrolls nowhere, on the subset of
the catalog whose panel happens to be absent. So this checks the two directions against real
built pages rather than by reading the template.
"""

from __future__ import annotations

import json
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest

from web.build import build

PLANETS_JSON = Path("data/planets.json")

pytestmark = pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")

# Every section the bar knows about, in the order the bar must present them — which is the
# order they appear on the page. Only "sec-data" is unconditional.
SECTIONS = (
    "sec-sky",
    "sec-move",
    "sec-opinion",
    "sec-data",
    "sec-tour",
    "sec-fiction",
    "sec-water",
)


@lru_cache(maxsize=1)
def _pages() -> tuple[tuple[str, str], ...]:
    """Planet pages spanning the conditional cases: a solar-system anchor, planets that appear
    in fiction, a microlensing world, and a plain slice of the catalog."""
    out = Path(tempfile.mkdtemp(prefix="secnav-"))
    doc = json.loads(PLANETS_JSON.read_text())
    picks = {"earth", "jupiter", "hd-189733-b", "hd-80606-b"}
    wanted = [p for p in doc["planets"] if p["id"] in picks]
    wanted += [p for p in doc["planets"] if not p["is_light_isolable"]][:2]
    wanted += doc["planets"][:25]
    seen, planets = set(), []
    for p in wanted:
        if p["id"] not in seen:
            seen.add(p["id"])
            planets.append(p)
    doc["planets"] = planets
    src = out / "planets.json"
    src.write_text(json.dumps(doc))
    root = build(src, out / "dist", og_cards=False)
    return tuple(
        (p.name, p.read_text()) for p in sorted((root / "planet").glob("*.html"))
    )


def _tabs(html: str) -> list[str]:
    """Section ids the tab bar links to, in document order."""
    nav = re.search(r'<nav class="secnav".*?</nav>', html, re.S)
    return re.findall(r'data-sec="([^"]+)"', nav.group(0)) if nav else []


def _anchors(html: str) -> set[str]:
    """Section ids actually present on the page as jump targets."""
    return set(re.findall(r'id="(sec-[a-z]+)"', html))


def test_every_tab_points_at_a_section_that_exists():
    for name, html in _pages():
        present = _anchors(html)
        for sec in _tabs(html):
            assert sec in present, f"{name}: tab {sec} has no section to scroll to"


def test_every_section_on_the_page_has_a_tab():
    """The other direction: a section with no tab is unreachable from the bar."""
    for name, html in _pages():
        tabs = _tabs(html)
        if not tabs:
            continue  # the bar is absent entirely; covered below
        for sec in _anchors(html):
            assert sec in tabs, f"{name}: section {sec} is on the page but has no tab"


def test_every_panel_below_the_bar_is_reachable_from_it():
    """The check that catches what the two above cannot.

    They compare tabs against sections marked with a sec- id, so a panel that simply has no
    id at all satisfies both while being unreachable from the bar. That is not hypothetical:
    the bar shipped without "Planet data" or "Guided tour" exactly this way. Anything that
    renders as a panel below the bar is a destination, so it must carry an id.
    """
    for name, html in _pages():
        nav = re.search(r'<nav class="secnav".*?</nav>', html, re.S)
        if not nav:
            continue
        for cls, attrs in re.findall(r'<div class="panel ([a-z-]+)"([^>]*)>', html[nav.end():]):
            assert 'id="sec-' in attrs, f"{name}: panel .{cls} sits below the bar with no tab"


def test_tabs_keep_the_intended_order():
    for name, html in _pages():
        tabs = _tabs(html)
        assert tabs == [s for s in SECTIONS if s in tabs], f"{name}: tabs out of order"


def test_tabs_follow_the_sections_they_link_to():
    """The bar is a jump list, so it has to sit above its targets — otherwise its first tab
    scrolls backwards."""
    for name, html in _pages():
        tabs = _tabs(html)
        if not tabs:
            continue
        nav_at = html.index('<nav class="secnav"')
        for sec in tabs:
            assert nav_at < html.index(f'id="{sec}"'), f"{name}: bar sits below {sec}"


def test_no_bar_when_there_is_nothing_to_navigate():
    """One tab is not a navigation, it is a decoration that takes a sticky strip of every
    screen. Below two sections the bar must not render at all."""
    for name, html in _pages():
        tabs = _tabs(html)
        assert len(tabs) != 1, f"{name}: bar rendered with a single tab"


def test_at_least_one_page_actually_exercises_the_bar():
    """Guards the guards: if the fixture stopped producing pages with sections, every test
    above would pass vacuously."""
    assert any(len(_tabs(html)) > 1 for _, html in _pages())


def test_the_bar_is_plain_anchors_so_it_works_without_javascript():
    for name, html in _pages():
        nav = re.search(r'<nav class="secnav".*?</nav>', html, re.S)
        if not nav:
            continue
        for sec in _tabs(html):
            assert f'href="#{sec}"' in nav.group(0), f"{name}: {sec} tab is not a real anchor"
