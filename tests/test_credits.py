"""The credits page has one job: nothing this site runs on goes uncredited.

That only holds if the page is generated from the same structures the pipeline actually uses
— `pipeline.rights` (which is also stamped into `planets.json`), `web.textures` and
`pipeline.observations` — rather than being a hand-maintained list that quietly falls behind.
These tests are what makes "add a source and it appears" a guarantee instead of a habit: add
one without a plain-English line, or drop one from the page, and this fails.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

import pytest

from pipeline.config import INSTRUMENTS, ROMAN_CGI
from pipeline.observations import OBSERVATIONS
from pipeline.rights import (
    ACKNOWLEDGEMENTS,
    ARCHIVE_ACKNOWLEDGEMENT,
    CARRIED_ASSETS,
    ENGINE_CREDITS,
    INSTRUMENT_CREDITS,
    SOURCES,
)
from web.build import _env
from web.credits import PLAIN, credits_context, image_credits, science_sources
from web.meta import Site, static_pages
from web.textures import SURFACE_MAPS


def _html() -> str:
    hub = {p.path: p for p in static_pages(5764)}
    return _env().get_template("credits.html").render(
        meta=hub["/credits"], site=Site(), build_id="test", **credits_context()
    )


def _on_page(text: str, html: str) -> bool:
    """Citations and credits are full of ampersands (`A&AS`, `Marley & Fortney`), which reach
    the page escaped — so compare against what Jinja actually wrote."""
    return escape(text, quote=False) in html


# ── the page cannot fall behind the pipeline ────────────────────────────────────────────


@pytest.mark.parametrize("src", SOURCES + CARRIED_ASSETS, ids=lambda s: s.name)
def test_every_source_has_a_plain_english_line(src):
    """A citation alone credits the source but tells a newcomer nothing. Both, or neither."""
    assert src.name in PLAIN, f"{src.name}: add a plain-English line to web.credits.PLAIN"
    assert len(PLAIN[src.name]) > 60, f"{src.name}: the plain line says nothing useful"


def test_plain_has_no_entries_for_sources_that_no_longer_exist():
    known = {s.name for s in SOURCES + CARRIED_ASSETS}
    assert set(PLAIN) <= known, f"stale PLAIN entries: {set(PLAIN) - known}"


@pytest.mark.parametrize("src", SOURCES + CARRIED_ASSETS, ids=lambda s: s.name)
def test_every_source_is_named_on_the_page(src):
    html = _html()
    assert _on_page(src.name, html)
    assert _on_page(src.licence, html), f"{src.name}: licence/terms missing from the page"
    if src.citation:
        assert _on_page(src.citation, html), f"{src.name}: citation missing from the page"


def test_dois_become_links():
    """The citations carry `doi:10.x/y`; a reader should be able to click through."""
    entries = {e.name: e for e in science_sources()}
    payne = entries["Payne et al. (2026)"]
    assert payne.doi == "10.3847/PSJ/ae2feb"
    assert f"https://doi.org/{payne.doi}" in _html()
    # An entry whose citation has no DOI must not fabricate one.
    assert all(e.doi == "" or e.doi.startswith("10.") for e in entries.values())


# ── the parts that are conditions of use, not courtesies ────────────────────────────────


def test_licences_stored_as_urls_are_printed_by_name():
    """`pipeline.rights` records CC BY as its URL — right for a machine-readable header, and
    unreadable as a chip. The reader gets the name; the URL becomes the link."""
    payne = next(e for e in science_sources() if e.name == "Payne et al. (2026)")
    assert payne.licence == "CC BY 4.0"
    assert payne.licence_url.startswith("https://creativecommons.org/licenses/by/4.0")
    # Every licence reaching a chip is a name, never a URL — the URL is the href.
    assert all(not e.licence.startswith("http") for e in science_sources())
    assert f'href="{payne.licence_url}" target="_blank" rel="noopener">CC BY 4.0</a>' in _html()


def test_every_required_acknowledgement_is_verbatim():
    """The Archive and CDS both ask for exact wording; paraphrasing fails the condition it is
    under. Iterating the tuple means a third one added later is checked automatically."""
    html = _html()
    assert ARCHIVE_ACKNOWLEDGEMENT in html
    for who, text in ACKNOWLEDGEMENTS:
        assert _on_page(text, html), f"{who}: acknowledgement missing or paraphrased"


# ── no engine and no instrument can ship uncredited ─────────────────────────────────────


def _pipeline_engine_ids() -> set[str]:
    """Every value the pipeline can write into `params.spectrum_source`, read out of the code
    that writes it rather than from a list someone has to remember to update."""
    root = Path(__file__).resolve().parents[1] / "pipeline"
    ids = {"parametric"}  # router.py's fallback, written as a literal there
    for path in root.rglob("*.py"):
        text = path.read_text()
        ids |= set(re.findall(r'spectrum_source\s*=\s*"([a-z0-9]+)"', text))
        ids |= set(re.findall(r'\bsource\s*=\s*"([a-z0-9]+)"', text))
        # router.py picks engines by label: ("cahoy", make_cahoy)
        ids |= set(re.findall(r'\(\s*"([a-z0-9]+)"\s*,\s*make_', text))
    # `source` on a BandSampleSet is "simulated"/"measured" — a state, not an engine.
    return ids - {"simulated", "measured"}


def test_every_spectrum_engine_names_a_credited_source():
    """The guard the whole page exists for: add an engine, and it must bring a credit with it."""
    credited = dict(ENGINE_CREDITS)
    known = {s.name for s in SOURCES}
    for engine in _pipeline_engine_ids():
        assert engine in credited, (
            f"spectrum_source '{engine}' has no entry in rights.ENGINE_CREDITS — "
            "an engine cannot ship uncredited"
        )
        assert credited[engine] in known, f"{engine}: credits an unknown source"
    for engine, name in credited.items():
        assert engine in _pipeline_engine_ids(), f"stale ENGINE_CREDITS entry: {engine}"
        assert _on_page(name, _html()), f"{engine}: its source is not on the credits page"


def test_every_instrument_names_a_credited_bandpass_source():
    """Adding HWO later is appending an Instrument — it must append a citation too."""
    credited = dict(INSTRUMENT_CREDITS)
    known = {s.name for s in SOURCES}
    assert set(credited) == set(INSTRUMENTS), "instrument credits and the registry disagree"
    for inst_id, name in credited.items():
        assert name in known, f"{inst_id}: credits an unknown source"


def test_the_bandpass_entry_states_its_width_convention():
    """A bandpass number without its convention is not a citation — nominal design widths and
    as-built FWHMs differ, and a reader checking our Roman colours needs to know which."""
    primer = next(e for e in science_sources() if e.name.startswith("Roman Coronagraph"))
    assert "top-hat" in primer.note
    assert "nominal" in primer.note
    for band in ROMAN_CGI.bands:
        assert f"{band.center_nm:.0f} nm" in primer.note, f"{band.id} not named in the note"


def test_the_page_states_both_rights_layers():
    """Claiming the whole dataset would assert rights over upstream facts we do not hold."""
    html = _html()
    assert "creativecommons.org/licenses/by/4.0/" in html
    for field in ("true_colour", "spectrum", "palette"):
        assert f"<code>{field}</code>" in html
    for field in ("params", "host_star", "discovery"):
        assert f"<code>{field}</code>" in html


def test_it_says_the_colours_are_modelled():
    """The one claim this site must never soften, on the page most likely to be quoted."""
    assert "MODELLED" in _html().upper()


# ── imagery ─────────────────────────────────────────────────────────────────────────────


def test_every_image_credit_appears():
    html = _html()
    for sm in SURFACE_MAPS.values():
        assert _on_page(sm.credit, html), f"uncredited surface map: {sm.credit}"
        assert sm.source_url in html, f"no way back to the original: {sm.credit}"
    for obs in OBSERVATIONS.values():
        for o in obs:
            assert _on_page(o.credit, html), f"uncredited telescope image: {o.credit}"
            assert o.source_url in html, f"no way back to the original: {o.credit}"


def test_image_credits_are_grouped_not_repeated():
    """One rightsholder, one row — the JWST team credit covers several separate releases."""
    credits = image_credits()
    assert credits, "no image credits collected at all"
    keys = [(c.credit, c.licence, c.kind) for c in credits]
    assert len(set(keys)) == len(keys)
    jwst = next(c for c in credits if c.credit.startswith("NASA, ESA, CSA"))
    assert len(jwst.uses) > 1, "the shared JWST credit should collapse into one row"


def test_image_credits_use_real_planet_names_when_the_build_supplies_them():
    """De-slugging cannot recover `bet-pic-b` -> `beta Pic b`, so the build passes names in."""
    named = image_credits({"bet-pic-b": "beta Pic b"})
    assert any("beta Pic b" in c.used_for for c in named)


# ── reachability ────────────────────────────────────────────────────────────────────────


def test_the_page_is_in_the_sitemap_set():
    page = next(p for p in static_pages(10) if p.path == "/credits")
    assert page.in_sitemap and not page.noindex


def test_the_site_links_to_it():
    """A credits page nobody can reach is the same as no credits page."""
    templates = Path(__file__).resolve().parents[1] / "web" / "templates"
    linked = [t.name for t in templates.glob("*.html") if 'href="/credits"' in t.read_text()]
    assert "gallery.html" in linked, "the front page must link the credits"
    assert len(linked) >= 3, f"only {linked} link to /credits"
