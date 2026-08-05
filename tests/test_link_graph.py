"""The shape of the link graph a non-JS crawler actually sees.

tests/test_share_meta_build.py already asserts every planet id appears in *some* page's HTML.
That is the existence check, and it was enough to catch the orphan problem the colour hubs
fixed. It is not enough to keep the graph healthy, because it cannot tell:

  - a link from a page that is itself unreachable from / (an orphan pointing at an orphan),
  - a planet whose only inbound link is a line in a 1,830-anchor hub tail,
  - an internal link that points at a URL the build never wrote.

So this walks the built site breadth-first from /, following only static <a href>, using the
same crawler as `python3 tools/link_audit.py` — one implementation, so the number the tool
prints and the number CI enforces cannot drift apart.
"""

from __future__ import annotations

import json
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest

from tools.link_audit import audit, crawl
from web.build import build

PLANETS_JSON = Path("data/planets.json")
BASE = "https://example.test"

pytestmark = pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")

# /glossary is deliberately URL-only: the site owner asked for it out of the nav, and the
# jargon marks reveal their definition in place rather than linking out (see the note at the
# top of web/templates/glossary.html). It is the one page allowed to have no inbound link.
ORPHANS_BY_DESIGN = {"/glossary"}


@lru_cache(maxsize=1)
def _site() -> Path:
    """A slice big enough to have a real graph: several colour families with tails, a couple of
    multi-planet systems, and the solar-system anchors."""
    out = Path(tempfile.mkdtemp(prefix="linkgraph-"))
    doc = json.loads(PLANETS_JSON.read_text())
    picks = {"earth", "jupiter", "neptune", "hd-189733-b"}
    wanted = [p for p in doc["planets"] if p["id"] in picks]
    wanted += doc["planets"][:150]
    seen, planets = set(), []
    for p in wanted:
        if p["id"] not in seen:
            seen.add(p["id"])
            planets.append(p)
    # Whole systems or none: a record's sibling strip links to every planet of its host, and
    # half a system in the fixture would show up as broken links that the real build does not
    # have. (It would be a real defect if a *released* catalogue ever dropped one sibling and
    # kept another — which is exactly what test_no_internal_link... below would then catch.)
    by_id = {p["id"]: p for p in doc["planets"]}
    for p in list(planets):
        for sib in (p.get("system") or {}).get("siblings", []):
            if sib["id"] not in seen and sib["id"] in by_id:
                seen.add(sib["id"])
                planets.append(by_id[sib["id"]])
    doc["planets"] = planets
    src = out / "planets.json"
    src.write_text(json.dumps(doc))
    return build(src, out / "dist", base_url=BASE, og_cards=False)


@lru_cache(maxsize=1)
def _graph() -> dict:
    return crawl(_site())


def test_no_page_is_unreachable_from_the_front_page():
    """Reachability, not mere existence: a link on a page nothing links to is not a link."""
    result = audit(_site())
    orphans = set(result["all_pages"]["orphans"]) - ORPHANS_BY_DESIGN
    assert not orphans, f"unreachable by static links from /: {sorted(orphans)}"


def test_every_planet_page_is_within_three_clicks():
    """Depth is the crawl-budget question. Two is what the colour hubs buy (/ -> hub -> planet);
    three leaves room for a rail to be the shortest path without anything sinking deeper."""
    depth = _graph()["depth"]
    deep = {u: d for u, d in depth.items() if u.startswith("/planet/") and d > 3}
    assert not deep, f"planet pages more than 3 clicks deep: {sorted(deep.items())[:5]}"


def test_no_planet_depends_on_a_hub_tail_for_its_only_link():
    """The point of web/related.py. A planet linked only from its colour hub sits in a list of
    up to 1,830 anchors — not an orphan, but the next worst thing, and a dead end for a reader.
    Every planet must also be reachable from another planet page."""
    inbound = _graph()["inbound"]
    planets = [u for u in _graph()["depth"] if u.startswith("/planet/")]
    thin = [
        u
        for u in planets
        if not any(src.startswith("/planet/") for src in inbound.get(u, ()))
    ]
    assert not thin, f"{len(thin)} planets reachable only from index pages, e.g. {thin[:5]}"


def test_planet_pages_carry_several_inbound_links():
    stats = audit(_site())["planet_pages"]
    assert stats["inbound_min"] >= 2, f"a planet page has only {stats['inbound_min']} inbound link"
    assert stats["inbound_median"] >= 4, f"median inbound is {stats['inbound_median']}"


def test_no_internal_link_points_at_a_page_that_was_never_built():
    broken = _graph()["broken"]
    assert not broken, f"{len(broken)} dead internal links, e.g. {list(broken.items())[:3]}"
