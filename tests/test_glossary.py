"""The glossary is the single source of truth for jargon: data/glossary.json feeds both the
/glossary page and the site-wide hover tooltips. These tests keep the two ends honest —
templates can only mark a term the glossary actually defines, and the runtime payload every
page loads stays small.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from web.build import _glossary_runtime_js, _load_glossary

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATES = _ROOT / "web" / "templates"
_STATIC = _ROOT / "web" / "static"
# Three ways a term gets marked, all of which must name a real entry:
#   g('term-id') / g("term-id", 'label')  — the Jinja macro
#   data-term="term-id"                   — chips that keep their own styling (src/provenance)
#   glossHTML("term-id", "label")         — the JS equivalent, for copy built in app.js/census.js
_G_CALL = re.compile(r"\bg\(\s*['\"]([a-z0-9-]+)['\"]")
_DATA_TERM = re.compile(r'data-term="([a-z0-9-]+)"')
_JS_CALL = re.compile(r"(?:glossHTML|_gloss|\bg)\(\s*['\"]([a-z0-9-]+)['\"]")


def _doc() -> dict:
    return json.loads((_ROOT / "data" / "glossary.json").read_text())


def _term_ids() -> set[str]:
    return {t["id"] for t in _doc()["terms"]}


def test_entries_are_well_formed():
    doc = _doc()
    cats = {c["id"] for c in doc["categories"]}
    assert cats, "the glossary needs at least one category"
    seen: set[str] = set()
    for t in doc["terms"]:
        assert t["id"] not in seen, f"duplicate glossary id: {t['id']}"
        seen.add(t["id"])
        assert re.fullmatch(r"[a-z0-9-]+", t["id"]), f"id must be kebab-case: {t['id']}"
        assert t["category"] in cats, f"{t['id']}: unknown category {t['category']}"
        for field in ("term", "short", "long"):
            assert t.get(field, "").strip(), f"{t['id']}: missing {field}"
        # `short` is the hover tooltip: it has to fit in a small box without scrolling.
        assert len(t["short"]) <= 260, f"{t['id']}: short definition too long for a tooltip"
        # The long entry should actually add something, not repeat the tooltip.
        assert len(t["long"]) > len(t["short"]), f"{t['id']}: long definition adds nothing"


def test_see_also_targets_exist():
    ids = _term_ids()
    for t in _doc()["terms"]:
        for ref in t.get("seeAlso", []):
            assert ref in ids, f"{t['id']}: seeAlso points at unknown term {ref}"


@pytest.mark.parametrize("tpl", sorted(_TEMPLATES.rglob("*.html")))
def test_templates_only_mark_defined_terms(tpl: Path):
    """A mark with no glossary entry would render an affordance that explains nothing."""
    ids = _term_ids()
    text = tpl.read_text()
    for term in _G_CALL.findall(text):
        assert term in ids, f"{tpl.name}: g('{term}') has no entry in data/glossary.json"
    for term in _DATA_TERM.findall(text):
        assert term in ids, f'{tpl.name}: data-term="{term}" has no entry in data/glossary.json'


def test_chip_vocabularies_are_defined():
    """The chips (origin tags, provenance badges, discovery badges) build their data-term from
    Jinja lookup tables, so no regex over the templates can see the ids. Pin the vocabularies
    here instead: renaming a glossary entry without updating those maps would otherwise leave a
    chip that looks explainable and explains nothing."""
    ids = _term_ids()
    chip_terms = {
        # src_tag(): the per-value origin tags.
        "measured", "computed", "assumed",
        # provenance_badge(): how real this planet's colour is.
        "modelled", "simulated", "measured-spectrum",
        # DISC_TERMS: detection methods, on the title badge and the data card.
        "radial-velocity", "transit", "direct-imaging", "microlensing",
        "transit-timing-variations",
    }
    missing = sorted(t for t in chip_terms if t not in ids)
    assert not missing, f"chips reference undefined glossary terms: {missing}"


@pytest.mark.parametrize("js", sorted(_STATIC.glob("*.js")))
def test_js_only_marks_defined_terms(js: Path):
    """Copy built in JS (the compare table, the census tiles) marks terms the same way."""
    ids = _term_ids()
    for term in _JS_CALL.findall(js.read_text()):
        assert term in ids, f"{js.name}: glossHTML('{term}') has no entry in data/glossary.json"


def test_runtime_payload_is_small_and_complete():
    """Every page loads this file, so it carries the tooltip text only — never the long
    entries, which live on the glossary page."""
    doc = _load_glossary()
    js = _glossary_runtime_js(doc["terms"])
    assert js.startswith("window.GLOSSARY=")
    payload = json.loads(js[len("window.GLOSSARY=") :].rstrip(";\n"))
    assert set(payload) == {t["id"] for t in doc["terms"]}
    assert all(set(v) == {"t", "s"} for v in payload.values())
    assert len(js) < 40_000, "tooltip payload is getting heavy for a per-page asset"
