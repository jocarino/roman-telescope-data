"""/about and /press: the contact surface, and the page whose whole subject is accuracy.

The high-consequence failure these tests hold shut is the marketing review's headline one:
shipping a press page that gets Roman's own instrument wrong — a wrong band count or a
stale band centre would be reprinted, and caught by exactly the CGI people the project most
wants as allies. So the wording pins here are not style: the band figures on /press must be
the ones in pipeline.config, and the retired four-band configuration (660/835, "6%") must
never reappear in prose.

Second failure: an unreachable press page. The contact address is a build input
(CONTACT_EMAIL), so the templates are tested in both states — with an address, and falling
back to the issue tracker rather than rendering an empty slot.

Asset checks run against dist/ when present, like tests/test_footer.py: the flagship images
must exist at both sizes, carry the credit inside the file (PNG text + sRGB profile), and
travel as one press.zip.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from pipeline.config import ROMAN_CGI
from pipeline.rights import RIGHTS
from web.build import _env
from web.meta import Site, static_pages
from web.press import PressAsset

_ROOT = Path(__file__).resolve().parents[1]
_DIST = _ROOT / "dist"

_FAKE_ASSETS = [
    PressAsset(
        slug="colour-wall", title="The wall", width=3000, height=3100,
        caption="The computed colour of 5,768 known exoplanets. Not photographs.",
        alt="A dense grid of coloured squares.",
    )
]
_FAKE_STATS = {"family_shift_pct": 37, "n_measured": 5, "microlensing": 2}


def _press_html(site: Site | None = None) -> str:
    hub = {p.path: p for p in static_pages(5764)}
    return _env().get_template("press.html").render(
        meta=hub["/press"], site=site or Site(), build_id="test",
        assets=_FAKE_ASSETS, bands=ROMAN_CGI.bands, stats=_FAKE_STATS,
        n_planets=5768, known_total=6300, attribution=RIGHTS.attribution,
        snapshot="2026-08-06",
    )


def _about_html(site: Site | None = None) -> str:
    hub = {p.path: p for p in static_pages(5764)}
    return _env().get_template("about.html").render(
        meta=hub["/about"], site=site or Site(), build_id="test", n_planets=5768
    )


# ── the Roman figures cannot drift from pipeline.config ─────────────────────────────────


def test_press_band_figures_come_from_the_flight_configuration():
    html = _press_html()
    for band in ROMAN_CGI.bands:
        assert f"{band.center_nm:.0f}" in html, f"band {band.id} missing from /press"
    assert f"{len(ROMAN_CGI.bands)} visible bandpasses" in html


def test_press_never_resurrects_the_retired_band_set():
    """835 nm and the four-band framing traced to no primary source; they were our own
    errors. 660 may appear ONLY as the installed-but-unsupported note."""
    html = _press_html()
    assert "835" not in html
    assert "four band" not in html.lower()
    assert "four Roman" not in html
    if "660" in html:
        assert "not a supported observing mode" in html


def test_press_words_that_must_and_must_not_appear():
    """"Computed colour" is the phrase the project rests on; "disclaimer"/"caveat" file the
    honesty under legal boilerplate, and a "Media Centre" is what this page must not be."""
    html = _press_html().lower()
    assert "computed colour" in html
    assert "disclaimer" not in html
    assert "caveat" not in html
    assert "media centre" not in html and "media center" not in html


# ── contact: reachable in both build states ─────────────────────────────────────────────


@pytest.mark.parametrize("render", [_press_html, _about_html])
def test_contact_email_renders_when_the_build_carries_one(render):
    html = render(Site(contact_email="x@example.test"))
    assert 'href="mailto:x@example.test"' in html


@pytest.mark.parametrize("render", [_press_html, _about_html])
def test_contact_falls_back_to_the_issue_tracker_not_an_empty_slot(render):
    html = render(Site())
    assert "mailto:" not in html
    assert "/issues" in html


def test_footer_offers_about_and_the_email_when_set():
    base = (_ROOT / "web" / "templates" / "base.html").read_text()
    assert 'href="/about"' in base
    assert "site.contact_email" in base


def test_about_and_press_are_registered_pages():
    paths = {p.path for p in static_pages(10)}
    assert {"/about", "/press"} <= paths


# ── the assets themselves (dist-gated, like test_footer) ────────────────────────────────

pytestmark_dist = pytest.mark.skipif(
    not (_DIST / "press.html").exists(),
    reason="no dist/ built (run `uv run python -m web.build --out dist`)",
)


@pytestmark_dist
def test_built_pages_exist_and_carry_the_footer():
    for rel in ("about.html", "press.html"):
        html = (_DIST / rel).read_text()
        assert '<footer class="site-foot">' in html


@pytestmark_dist
def test_flagship_assets_exist_at_both_sizes_and_bundle():
    kit = _DIST / "press-kit"
    slugs = ("colour-wall", "roman-comparison", "band1-only")
    for slug in slugs:
        assert (kit / f"{slug}.png").exists()
        assert (kit / f"{slug}-1200.png").exists()
    with zipfile.ZipFile(kit / "press.zip") as z:
        names = set(z.namelist())
    assert "CREDITS.txt" in names
    for slug in slugs:
        assert {f"{slug}.png", f"{slug}-1200.png"} <= names


@pytestmark_dist
def test_credit_and_honesty_travel_inside_the_file():
    """The attribution and the sRGB profile ride in the PNG itself — they survive the image
    being pulled off the page, re-shared with no caption, or run through a CMS."""
    from PIL import Image

    for slug in ("colour-wall", "roman-comparison", "band1-only"):
        img = Image.open(_DIST / "press-kit" / f"{slug}.png")
        assert img.info.get("icc_profile"), f"{slug}: no embedded sRGB profile"
        assert img.text.get("Author") == RIGHTS.attribution, f"{slug}: credit missing"
        desc = img.text.get("Description", "")
        assert "photograph" in desc.lower(), f"{slug}: description does not state honesty"


@pytestmark_dist
def test_masters_are_print_sized():
    from PIL import Image

    for slug in ("colour-wall", "roman-comparison", "band1-only"):
        w, _ = Image.open(_DIST / "press-kit" / f"{slug}.png").size
        assert w >= 2900, f"{slug}: master is {w}px wide, below print size"

