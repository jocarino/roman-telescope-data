"""Per-page share metadata: titles, descriptions, Open Graph, sitemap, robots.

The failure this guards against is silent and expensive: a page ships, unfurls as a bare URL
or a stale description, and nobody notices because nothing is broken on screen. So the checks
are about agreement (the <title> and og:title come from two different places and must match),
honesty (never imply a colour was photographed), and completeness (every planet page reachable
by a crawler, since the gallery grid is client-rendered and links to almost none of them).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import replace

import pytest

from pipeline.models import (
    ColourResultModel,
    Discovery,
    HostStar,
    PaletteStopModel,
    PlanetParams,
    PlanetRecord,
    RecordMeta,
)
from web.meta import (
    PageMeta,
    Site,
    planet_description,
    planet_meta,
    robots_txt,
    sitemap_xml,
    static_pages,
)

_SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _record(**over) -> PlanetRecord:
    base = dict(
        id="test-b",
        name="Test b",
        host_star=HostStar(name="Test", teff_k=5200.0, spectral_type="K0 V"),
        params=PlanetParams(
            equilibrium_temp_k=1200.0,
            radius_r_earth=12.0,
            mass_m_earth=300.0,
            semi_major_axis_au=0.03,
            distance_pc=20.0,
            assumed_cloud_state="cloud-free",
            assumed_metallicity=1.0,
            assumed_phase_angle_deg=20.0,
        ),
        discovery=Discovery(method="Transit", year=2010),
        is_light_isolable=True,
        provenance="model",
        true_colour=ColourResultModel(
            method="full-spectrum",
            hex="#3b5aa8",
            srgb=(59, 90, 168),
            xyz=(0.1, 0.1, 0.3),
            luminance_y=0.12,
            out_of_gamut=False,
            confidence="medium",
            palette=[PaletteStopModel(hex="#3b5aa8", role="mid")],
        ),
        meta=RecordMeta(generated_at="2026-01-01", pipeline_version="1", schema_version=5),
    )
    params_over = over.pop("params", None)
    rec = PlanetRecord(**{**base, **over})
    if params_over:
        rec = rec.model_copy(update={"params": rec.params.model_copy(update=params_over)})
    return rec


# ── descriptions ────────────────────────────────────────────────────────────────────────


def test_description_names_the_planet_type_and_star():
    d = planet_description(_record())
    assert d.startswith("Test b is a hot Jupiter orbiting Test,")
    assert "65 light-years away" in d  # 20 pc


def test_description_keeps_the_proper_nouns():
    """`TYPE_LABELS` values are title-cased and three of six contain a proper noun, so a
    naive .lower() gives 'a hot jupiter' / 'a super-earth'."""
    assert "hot Jupiter" in planet_description(_record())
    small = _record(params={"radius_r_earth": 2.0, "equilibrium_temp_k": 300.0})
    assert "super-Earth" in planet_description(small)


def test_description_never_claims_a_photograph():
    for rec in (_record(), _record(is_light_isolable=False)):
        d = planet_description(rec)
        assert "Modelled" in d
        # The only permitted use of the word is the denial.
        for match in re.finditer(r"photograph", d, re.I):
            assert "not photographed" in d[max(0, match.start() - 8) : match.end() + 4]


def test_microlensing_says_its_light_is_never_isolable():
    d = planet_description(_record(is_light_isolable=False, provenance="model-microlensing"))
    assert "microlensing" in d
    assert "model-only" in d
    assert "not photographed" not in d


def test_description_omits_distance_when_unknown():
    d = planet_description(_record(params={"distance_pc": None}))
    assert "light-year" not in d
    assert d.startswith("Test b is a hot Jupiter orbiting Test.")


def test_descriptions_fit_an_unfurl():
    """Slack/X truncate well before 300; anything longer is silently cut mid-sentence."""
    for rec in (_record(), _record(is_light_isolable=False)):
        assert len(planet_description(rec)) <= 300
    for page in static_pages(5764):
        assert len(page.description) <= 300


# ── absolute vs relative URLs ───────────────────────────────────────────────────────────


def test_absolute_urls_when_a_base_url_is_configured():
    site = Site(base_url="https://example.test")
    assert site.absolute("/og/x.png") == "https://example.test/og/x.png"


def test_paths_stay_relative_with_no_base_url():
    """Emitting tags against a guessed origin would be worse than relative ones: a wrong
    absolute og:image is a broken image everywhere, a relative one resolves for most clients."""
    assert Site().absolute("/og/x.png") == "/og/x.png"


# ── sitemap / robots ────────────────────────────────────────────────────────────────────


def _sitemap_locs(site: Site) -> list[str]:
    root = ET.fromstring(sitemap_xml(site))
    return [u.findtext(f"{_SM_NS}loc") for u in root.findall(f"{_SM_NS}url")]


def test_sitemap_is_wellformed_and_absolute():
    site = Site(base_url="https://example.test", pages=[planet_meta(_record())])
    locs = _sitemap_locs(site)
    assert locs == ["https://example.test/planet/test-b"]


def test_sitemap_lists_every_planet_page():
    recs = [_record(id=f"p-{i}", name=f"P {i}") for i in range(50)]
    site = Site(base_url="https://x.test", pages=[planet_meta(r) for r in recs])
    assert len(_sitemap_locs(site)) == 50


def test_sitemap_excludes_noindex_and_opted_out_pages():
    pages = [
        planet_meta(_record()),
        PageMeta(title="404", description="d", path="/404.html", noindex=True, in_sitemap=False),
        PageMeta(title="x", description="d", path="/hidden.html", in_sitemap=False),
    ]
    assert len(_sitemap_locs(Site(base_url="https://x.test", pages=pages))) == 1


def test_sitemap_escapes_urls():
    page = replace(planet_meta(_record()), path="/planet/a&b.html")
    xml = sitemap_xml(Site(base_url="https://x.test", pages=[page]))
    assert "a&amp;b" in xml
    ET.fromstring(xml)  # would raise on a raw &


def test_robots_points_at_the_sitemap_only_when_one_exists():
    assert "Sitemap:" in robots_txt(Site(base_url="https://x.test"))
    assert "Sitemap:" not in robots_txt(Site())
    assert robots_txt(Site()).startswith("User-agent: *\nAllow: /")


def test_robots_keeps_the_peek_fragments_out_of_the_index():
    """The ~5.8k hold-to-peek partials under /fragments/ have no <head> and so nowhere to put a
    noindex — robots.txt is the only thing keeping a near-duplicate of every planet page out of
    the index. Nothing on screen breaks if this line is dropped, so it needs an assertion."""
    for site in (Site(), Site(base_url="https://x.test")):
        assert "Disallow: /fragments/" in robots_txt(site)


# ── hub pages ───────────────────────────────────────────────────────────────────────────


def test_hub_pages_have_distinct_descriptions():
    descs = [p.description for p in static_pages(5764)]
    assert len(set(descs)) == len(descs)


def test_hub_paths_are_unique_so_the_build_can_key_on_them():
    paths = [p.path for p in static_pages(10)]
    assert len(set(paths)) == len(paths)


@pytest.mark.parametrize("path", ["/", "/how", "/compare", "/sky", "/tours"])
def test_build_can_look_up_every_hub_page_it_renders(path):
    assert path in {p.path for p in static_pages(10)}


def test_hub_paths_are_in_the_form_the_links_use():
    """One page, one URL. Every internal link is extensionless and slash-free (`/tours`, not
    `/tours/index.html` or `/tours/`), so the canonical these paths become has to match, or
    the page advertises a URL nothing on the site actually links to."""
    for page in static_pages(10):
        assert page.path.startswith("/"), page.path
        assert not page.path.endswith(".html"), page.path
        assert page.path == "/" or not page.path.endswith("/"), page.path
