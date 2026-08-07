"""The site wrapper: one footer, on every page, from base.html.

The failure this guards is the one the site actually had — pages that end in a dead stop. It
was never a bug in any single template; it was that nothing rendered site-wide chrome at all,
so each new page inherited the omission. Putting the footer in `base.html` fixes that
structurally (a page cannot opt out of its own base), and these tests hold that structure:
every built page carries it, its links point somewhere real, and the honesty line — the one
sentence that belongs on every page of this site — is in it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.rights import RIGHTS

_ROOT = Path(__file__).resolve().parents[1]
_DIST = _ROOT / "dist"
_TEMPLATES = _ROOT / "web" / "templates"

# Where the footer says you can go. Root-relative, extensionless, as the site serves them.
FOOTER_LINKS = ("/", "/how", "/credits", "/glossary", "/about")

pytestmark = pytest.mark.skipif(
    not (_DIST / "index.html").exists(),
    reason="no dist/ built (run `python -m web.build --out dist`)",
)


def _page(rel: str) -> str:
    return (_DIST / rel).read_text()


def test_the_footer_lives_in_the_base_template():
    """Not in a macro each page opts into: a page that forgets is exactly the old bug."""
    assert '<footer class="site-foot">' in (_TEMPLATES / "base.html").read_text()


@pytest.mark.parametrize(
    "rel",
    [
        "index.html",
        "how.html",
        "credits.html",
        "census.html",
        "glossary.html",
        "compare.html",
        "sky.html",
        "roman.html",
        "404.html",
        "tours/index.html",
    ],
)
def test_every_hub_page_carries_the_footer(rel):
    if not (_DIST / rel).exists():
        pytest.skip(f"{rel} not in this build")
    assert '<footer class="site-foot">' in _page(rel)


def test_planet_pages_carry_the_footer():
    """The pages people actually land on from a shared link, and the deepest cul-de-sac."""
    a_planet = next(iter((_DIST / "planet").glob("*.html")))
    html = a_planet.read_text()
    assert '<footer class="site-foot">' in html
    for href in FOOTER_LINKS:
        assert f'href="{href}"' in html


def test_the_footer_states_the_honesty_line():
    """Modelled, not photographed — on every page, whether or not anyone reads the rest."""
    html = _page("credits.html")
    foot = html[html.index('<footer class="site-foot">') :]
    assert "modelled" in foot.lower()
    assert "not photographed" in foot.lower()


def test_footer_destinations_exist_in_the_build():
    """A footer link to a 404 is worse than no footer."""
    for href in FOOTER_LINKS:
        rel = "index.html" if href == "/" else href.lstrip("/") + ".html"
        assert (_DIST / rel).exists(), f"footer links to {href}, which this build did not write"


def test_licence_and_repo_come_from_the_rights_block():
    """Typed into the template, these would be a second copy of a fact planets.json already
    carries — and the two would disagree the first time either moved."""
    foot = _page("credits.html")
    assert RIGHTS.derived_licence in foot
    assert RIGHTS.full_text.split("/blob/")[0] in foot


def test_the_footer_offers_a_way_to_reach_a_human():
    """A journalist on deadline could not contact the site's author at all, because no page
    carried an address. It is RIGHTS.contact — the same one stamped into released data
    files — and it must be visible text, not just a href, so it survives readers who
    never click."""
    html = _page("credits.html")
    foot = html[html.index('<footer class="site-foot">') :]
    assert f'href="mailto:{RIGHTS.contact}"' in foot
    assert f">{RIGHTS.contact}</a>" in foot
