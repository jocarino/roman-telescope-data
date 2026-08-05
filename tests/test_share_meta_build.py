"""What a built page actually says about itself.

tests/test_meta.py checks the metadata functions; this checks that the build wires them to
every page. The gap is real and silent: a template rendered without `meta=` still produces a
perfectly valid page, it just falls back to the shared site-wide description — which is
exactly the bug this work exists to fix, so it has to be caught here rather than by eye.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import pytest

from web.build import build

PLANETS_JSON = Path("data/planets.json")
BASE = "https://example.test"
_SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

pytestmark = pytest.mark.skipif(not PLANETS_JSON.exists(), reason="needs a fetched data release")


@lru_cache(maxsize=1)
def _site(tmp_root: str = "") -> Path:
    """Build a small real site once for the whole module. Cards are skipped: they are covered
    by tests/test_og_card.py and cost ~100 ms each."""
    import tempfile

    out = Path(tempfile.mkdtemp(prefix="sharemeta-"))
    doc = json.loads(PLANETS_JSON.read_text())
    # A spread that covers the interesting cases: solar-system anchors, a famous hot Jupiter,
    # and a microlensing planet (whose light is never isolable).
    wanted = [p for p in doc["planets"] if p["id"] in {"earth", "jupiter", "hd-189733-b"}]
    wanted += [p for p in doc["planets"] if not p["is_light_isolable"]][:2]
    # Enough planets that at least one colour family overflows web.hubs.FEATURED, so the
    # hub pages' "the other N" tail is actually exercised. At 15 every family fitted in
    # the featured cards and the crawlability test below passed without testing anything.
    wanted += doc["planets"][:90]
    seen, planets = set(), []
    for p in wanted:
        if p["id"] not in seen:
            seen.add(p["id"])
            planets.append(p)
    doc["planets"] = planets
    src = out / "planets.json"
    src.write_text(json.dumps(doc))
    return build(src, out / "dist", base_url=BASE, og_cards=False)


@lru_cache(maxsize=1)
def _pages() -> tuple[tuple[Path, str], ...]:
    root = _site()
    return tuple(
        (p, p.read_text()) for p in sorted(root.rglob("*.html")) if "fragments" not in p.parts
    )


def _tag(html: str, pattern: str) -> str | None:
    m = re.search(pattern, html)
    return m.group(1) if m else None


def _og(html: str, prop: str) -> str | None:
    return _tag(html, rf'<meta property="og:{prop}" content="([^"]*)">')


def _name_meta(html: str, name: str) -> str | None:
    return _tag(html, rf'<meta name="{name}" content="([^"]*)">')


def _served_url(rel_path: str) -> str:
    """The one URL a built artifact is meant to be reached by: extensionless, no trailing
    slash, `/` for the site root. `dist/census.html` is reachable as both `/census.html` and
    `/census`, and `dist/tours/index.html` as `/tours`, `/tours/` and `/tours/index.html` --
    which is precisely why the site has to pick one form and use it everywhere."""
    url = "/" + rel_path
    if url == "/index.html":
        return "/"
    if url.endswith("/index.html"):
        url = url[: -len("/index.html")]
    elif url.endswith(".html"):
        url = url[: -len(".html")]
    return url


# ── every page ──────────────────────────────────────────────────────────────────────────


def test_every_page_carries_share_tags():
    for path, html in _pages():
        assert _og(html, "title"), f"{path.name} has no og:title"
        assert _og(html, "image"), f"{path.name} has no og:image"
        assert _name_meta(html, "twitter:card") == "summary_large_image", path.name


def test_title_and_og_title_never_drift():
    """Both now come from the same PageMeta — base.html renders `meta.title` and no template
    overrides the block — so this can no longer drift by a typo. Kept as the guard that says
    so: re-adding a hand-typed `{% block title %}` that disagrees turns this red, and a second
    literal `<title>` in the head trips the count below (a browser would show the first, an
    unfurler often the last)."""
    for path, html in _pages():
        assert len(re.findall(r"<title[\s>]", html)) == 1, f"{path.name}: not exactly one <title>"
        title = _tag(html, r"<title>([^<]*)</title>")
        assert title == _og(html, "title"), f"{path.name}: <title> != og:title"


def test_every_page_has_a_canonical_and_absolute_og_urls():
    for path, html in _pages():
        canonical = _tag(html, r'<link rel="canonical" href="([^"]*)">')
        assert canonical and canonical.startswith(BASE), path.name
        assert _og(html, "url") == canonical, path.name
        assert _og(html, "image").startswith(f"{BASE}/og/"), path.name


def test_no_page_reuses_the_old_site_wide_description():
    """The bug being fixed: one description on all ~5.8k pages."""
    stale = "The colour scheme of every known exoplanet, derived from physics."
    descs = [_name_meta(html, "description") for _, html in _pages()]
    assert all(d and d != stale for d in descs)
    assert len(set(descs)) == len(descs), "two pages share a description"


# ── planet pages ────────────────────────────────────────────────────────────────────────


def _planet_pages():
    return [(p, h) for p, h in _pages() if p.parent.name == "planet"]


def test_planet_pages_point_at_their_own_card():
    for path, html in _planet_pages():
        assert _og(html, "image") == f"{BASE}/og/{path.stem}.png", path.name


def test_planet_descriptions_carry_the_planets_own_colour():
    for path, html in _planet_pages():
        desc = _name_meta(html, "description")
        assert re.search(r"#[0-9a-f]{6}", desc), f"{path.name}: {desc}"
        assert "Modelled reflected-light colour" in desc


def test_planet_image_alt_is_not_the_generic_fallback():
    for path, html in _planet_pages():
        alt = _og(html, "image:alt")
        assert alt and alt != "Exoplanet Palette", path.name


# ── crawlability ────────────────────────────────────────────────────────────────────────


def test_sitemap_lists_every_built_html_page():
    root = _site()
    locs = {
        u.findtext(f"{_SM_NS}loc")
        for u in ET.parse(root / "sitemap.xml").getroot().findall(f"{_SM_NS}url")
    }
    for path, html in _pages():
        if _name_meta(html, "robots") == "noindex, follow":
            continue
        rel = _served_url(path.relative_to(root).as_posix())
        # The build writes `census.html`; the site links to, and canonicalises, `/census`
        # (nginx `try_files $uri $uri.html` serves both). Extensionless is the one form every
        # internal link uses, so it is the canonical one -- `_served_url` maps the artifact to it.
        assert BASE + rel in locs, f"{rel} is built but absent from sitemap.xml"


def test_no_sitemap_url_carries_a_html_extension():
    """The canonical form is extensionless. A `.html` URL in the sitemap means some PageMeta
    drifted back to the artifact filename, which puts a duplicate of every page in the index."""
    root = _site()
    locs = {
        u.findtext(f"{_SM_NS}loc")
        for u in ET.parse(root / "sitemap.xml").getroot().findall(f"{_SM_NS}url")
    }
    offenders = sorted(u for u in locs if u.endswith(".html"))
    assert not offenders, f"sitemap carries non-canonical .html URLs: {offenders[:5]}"


# Internal hrefs that are not page navigations: real files served as themselves, so their
# extension is the URL and not a stray artifact name.
_ASSET_PREFIXES = ("/static/", "/og/", "/palettes/", "/fragments/", "/data/")
_ASSET_SUFFIXES = (".ase", ".png", ".svg", ".css", ".js", ".json", ".xml", ".txt", ".webmanifest")


def _internal_links(html: str) -> set[str]:
    """Root-relative hrefs, reduced to the path a crawler would fetch (query and fragment
    dropped). Skips assets, and skips Alpine's `:href` bindings, which are JS expressions."""
    links = set()
    for href in re.findall(r'(?<![:@\w])href="(/[^"]*)"', html):
        path = href.split("?")[0].split("#")[0]
        if not path or path.startswith(_ASSET_PREFIXES) or path.endswith(_ASSET_SUFFIXES):
            continue
        links.add(path)
    return links


def test_no_internal_link_carries_a_html_extension():
    """The other half of the sitemap's extensionless rule. A canonical says `/sky` while a link
    says `/sky.html`, and the site is telling a crawler two different URLs for one page: the
    link is what gets followed and counted, the canonical is what gets indexed. Both forms are
    served (nginx `try_files $uri $uri.html`), so nothing looks broken while it drifts."""
    offenders = {
        (path.name, link)
        for path, html in _pages()
        for link in _internal_links(html)
        if link.endswith(".html")
    }
    assert not offenders, f"internal links using the artifact filename: {sorted(offenders)[:5]}"


def test_every_internal_link_matches_the_canonical_of_the_page_it_reaches():
    """Stronger than the rule above, and the one that catches trailing slashes: follow every
    internal link to the file nginx would serve, and check that page's own canonical agrees
    that this is its URL. `/tours/` vs `/tours` fails here while both still serve fine."""
    root = _site()
    canonical_of = {
        _served_url(path.relative_to(root).as_posix()): _tag(
            html, r'<link rel="canonical" href="([^"]*)">'
        )
        for path, html in _pages()
    }
    mismatched = []
    for path, html in _pages():
        for link in _internal_links(html):
            # Targets outside this fixture's ~95-planet subset simply aren't built here (a
            # planet page links its siblings); their form is checked wherever they do exist.
            target = canonical_of.get(link.rstrip("/") or "/")
            if target and target != BASE + link:
                mismatched.append((path.name, link, target))
    assert not mismatched, f"link form disagrees with the target's canonical: {mismatched[:5]}"


def test_every_planet_page_is_reachable_by_a_static_link():
    """The one that matters: a planet page nothing links to is invisible to anything that does
    not execute JS and scroll. The gallery grid is built client-side and scroll-loaded, so for
    most of this site's life ~97% of planet pages existed only in sitemap.xml -- which is itself
    skipped when the build has no base URL. The colour hubs are what fix that, and this is the
    assertion that stops it silently regressing (truncate a hub's tail list and it goes red)."""
    root = _site()
    built = {p.stem for p in (root / "planet").glob("*.html")}
    linked = set()
    for path, html in _pages():
        if "fragments" in path.parts:
            continue
        linked |= set(re.findall(r'href="/planet/([a-z0-9-]+)"', html))
    orphans = sorted(built - linked)
    assert not orphans, f"{len(orphans)} planet pages have no static link in: {orphans[:5]}"


def test_every_colour_hub_is_itself_linked_from_the_gallery():
    """Hubs that nothing links to are orphans in turn, and take the catalogue down with them."""
    root = _site()
    hubs = {p.stem for p in (root / "colour").glob("*.html")}
    assert hubs, "no colour hubs were built"
    index = (root / "index.html").read_text()
    linked = set(re.findall(r'href="/colour/([a-z]+)"', index))
    assert hubs <= linked, f"hubs missing from the gallery: {sorted(hubs - linked)}"


def test_404_is_noindex_and_absent_from_the_sitemap():
    root = _site()
    html = (root / "404.html").read_text()
    assert _name_meta(html, "robots") == "noindex, follow"
    assert "404.html" not in (root / "sitemap.xml").read_text()


def test_descriptions_are_unique_across_the_whole_catalogue():
    """Not a style point: type + host + distance + colour family repeats across siblings (all
    seven TRAPPIST-1 planets collide), and duplicate meta descriptions at this scale are
    exactly what a search engine reads as a thin, templated site."""
    import collections

    from pipeline.models import PlanetsFile
    from web.meta import planet_description

    doc = PlanetsFile.model_validate_json(PLANETS_JSON.read_text())
    counts = collections.Counter(planet_description(r) for r in doc.planets)
    dupes = [d for d, n in counts.items() if n > 1]
    assert not dupes, f"{len(dupes)} duplicated descriptions, e.g. {dupes[:1]}"


def test_every_planet_description_fits_an_unfurl():
    from pipeline.models import PlanetsFile
    from web.meta import planet_description

    doc = PlanetsFile.model_validate_json(PLANETS_JSON.read_text())
    worst = max(doc.planets, key=lambda r: len(planet_description(r)))
    assert len(planet_description(worst)) <= 300, worst.name


def test_robots_txt_points_a_crawler_at_the_sitemap():
    robots = (_site() / "robots.txt").read_text()
    assert f"Sitemap: {BASE}/sitemap.xml" in robots
    assert "Allow: /" in robots


def test_the_built_peek_fragments_are_uncrawlable():
    """Two things have to hold together for the peek partials to stay out of the index, and
    neither is visible on screen: robots.txt disallows the directory, and no page links into it
    with an href (a Disallow'd URL that something links to can still be indexed URL-only). The
    hold-to-peek gesture fetches them from a `data-peek` attribute, which no crawler follows."""
    root = _site()
    assert (root / "fragments" / "peek").is_dir(), "no peek fragments were built"
    assert "Disallow: /fragments/" in (root / "robots.txt").read_text()
    linkers = [
        str(path.relative_to(root)) for path, html in _pages() if 'href="/fragments/' in html
    ]
    assert not linkers, f"pages link into /fragments/: {linkers[:5]}"


def test_no_sitemap_is_written_without_a_base_url(tmp_path):
    """A sitemap of relative paths is invalid; not publishing one is the honest failure."""
    doc = json.loads(PLANETS_JSON.read_text())
    doc["planets"] = doc["planets"][:3]
    src = tmp_path / "planets.json"
    src.write_text(json.dumps(doc))
    out = build(src, tmp_path / "dist", base_url="", og_cards=False)
    assert not (out / "sitemap.xml").exists()
    assert (out / "robots.txt").exists()
    html = (out / "index.html").read_text()
    assert _og(html, "image").startswith("/og/"), "should degrade to a root-relative path"
