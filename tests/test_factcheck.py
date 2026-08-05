"""The prose checker, pinned against the errors this project actually published.

Each test below is one of the mistakes from the P3 list in the private fix list — a sentence we
wrote, believed, and had to correct. They are the regression suite: if the checker stops
catching one of these, the class of error is live again.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import factcheck  # noqa: E402


def _record(name: str, hex_colour: str, srgb: list[int], provenance: str = "model") -> dict:
    return {"id": name.lower().replace(" ", "-"), "name": name, "provenance": provenance,
            "host_star": {"name": name.rsplit(" ", 1)[0]},
            "true_colour": {"hex": hex_colour, "srgb": srgb}}


@pytest.fixture
def catalogue(tmp_path: Path) -> factcheck.Catalogue:
    """A miniature dataset with the objects the P3 errors were about."""
    payload = {"planets": [
        # The real shipped colour: a vivid blue, not the near-black the draft claimed.
        _record("TrES-2 b", "#2fa1ff", [47, 161, 255]),
        _record("WASP-12 b", "#3b3b44", [59, 59, 68]),
        _record("47 Ursae Majoris b", "#d7cab5", [215, 202, 181], "simulated-cgi"),
        _record("upsilon Andromedae d", "#d7cab5", [215, 202, 181], "simulated-cgi"),
        _record("GJ 1214 b", "#8fb8c8", [143, 184, 200]),
        _record("Neptune", "#abd2e1", [171, 210, 225], "measured-albedo"),
        _record("Jupiter", "#d7cab5", [215, 202, 181], "measured-albedo"),
    ]}
    path = tmp_path / "planets.json"
    path.write_text(json.dumps(payload))
    return factcheck.load_catalogue(path)


def _run(text: str, catalogue: factcheck.Catalogue, tmp_path: Path,
         repo: Path | None = None) -> list[factcheck.Finding]:
    doc = tmp_path / "draft.md"
    doc.write_text(text)
    return factcheck.check_file(doc, catalogue, repo or factcheck.REPO_ROOT, {}, {})


def _checks(findings: list[factcheck.Finding]) -> set[str]:
    return {f.check for f in findings}


# --- the six errors ---------------------------------------------------------------------

def test_colour_claim_contradicting_the_shipped_swatch(catalogue, tmp_path):
    """"TrES-2 b renders near-black" — it renders #2fa1ff, because every swatch is normalised."""
    findings = _run("TrES-2 b renders near-black on the site.", catalogue, tmp_path)
    colour = [f for f in findings if f.check == "colour-claim"]
    assert len(colour) == 1
    assert "#2fa1ff" in colour[0].message
    assert colour[0].severity == "error"


def test_colour_claim_that_agrees_is_silent(catalogue, tmp_path):
    findings = _run("TrES-2 b comes out a startling blue.", catalogue, tmp_path)
    assert "colour-claim" not in _checks(findings)


def test_colour_word_must_be_near_the_planet_it_describes(catalogue, tmp_path):
    """A hook bank naming four planets and mentioning molten iron is not four colour claims."""
    line = ("Hook bank: TrES-2 b — the darkest world known; WASP-12 b — being eaten alive by "
            "its star, stretched into an egg, glowing red-hot on the day side.")
    findings = _run(line, catalogue, tmp_path)
    assert "colour-claim" not in _checks(findings)


def test_colour_of_the_page_is_not_the_colour_of_the_planet(catalogue, tmp_path):
    findings = _run("A rendered disc of TrES-2 b on a near-black background.",
                    catalogue, tmp_path)
    assert "colour-claim" not in _checks(findings)


def test_a_hedged_colour_is_not_a_claim(catalogue, tmp_path):
    """"everyone wants it to be blue, and we don't know" is the honest sentence, not the error."""
    findings = _run("TrES-2 b is the one everyone wants to be green; we don't know its "
                    "atmosphere.", catalogue, tmp_path)
    assert "colour-claim" not in _checks(findings)


def test_object_not_in_the_catalogue(catalogue, tmp_path):
    """"HIP 71618 B" was listed as a Roman target; it is a brown dwarf, and not in our data."""
    findings = _run("Roman will look at HIP 71618 B first.", catalogue, tmp_path)
    names = [f for f in findings if f.check == "object-name"]
    assert len(names) == 1
    assert names[0].severity == "error"
    assert "not in the catalogue" in names[0].message


def test_archive_abbreviation_is_a_warning_not_an_error(catalogue, tmp_path):
    """"47 UMa b" is real, but the site labels it "47 Ursae Majoris b" — a reader's search fails."""
    findings = _run("Take 47 UMa b as the worked example.", catalogue, tmp_path)
    names = [f for f in findings if f.check == "object-name"]
    assert len(names) == 1
    assert names[0].severity == "warn"
    assert "47 Ursae Majoris b" in names[0].message


def test_common_alias_is_resolved_to_the_site_label(catalogue, tmp_path):
    findings = _run("The press always writes Gliese 1214 b.", catalogue, tmp_path)
    names = [f for f in findings if f.check == "object-name"]
    assert len(names) == 1
    assert "GJ 1214 b" in names[0].message


def test_spacing_variants_are_the_same_object(catalogue, tmp_path):
    """`WASP-12b`, `WASP 12 b` and `wasp-12b` must not be reported as three unknown objects."""
    findings = _run("WASP-12b and WASP 12 b and wasp-12b.", catalogue, tmp_path)
    assert "object-name" not in _checks(findings)


def test_stale_code_reference(catalogue, tmp_path):
    """A draft cited `pipeline/cie.py`; the module has always lived at `pipeline/colour/cie.py`."""
    findings = _run("The conversion is in `pipeline/cie.py`.", catalogue, tmp_path)
    refs = [f for f in findings if f.check == "code-ref"]
    assert len(refs) == 1
    assert refs[0].severity == "error"


def test_stale_reference_suggests_where_the_file_went(catalogue, tmp_path):
    doc = tmp_path / "draft.md"
    doc.write_text("The conversion is in `pipeline/cie.py`.")
    elsewhere = factcheck.index_basenames([factcheck.REPO_ROOT])
    findings = factcheck.check_file(doc, catalogue, factcheck.REPO_ROOT, {}, elsewhere)
    assert "pipeline/colour/cie.py" in findings[0].message


def test_an_output_path_is_not_a_stale_reference(catalogue, tmp_path):
    """`--emit-manifest data/manifest.json` names a file the command creates."""
    findings = _run("uv run python -m pipeline drift --emit-manifest data/manifest.json",
                    catalogue, tmp_path)
    assert "code-ref" not in _checks(findings)


def test_live_code_reference_passes(catalogue, tmp_path):
    findings = _run("The anchors are ordered in `pipeline/curate.py`.", catalogue, tmp_path)
    assert "code-ref" not in _checks(findings)


def test_symbol_must_exist(catalogue, tmp_path):
    """Checked against a fake source tree, so this file's own examples cannot satisfy it."""
    repo = tmp_path / "repo"
    (repo / "pipeline").mkdir(parents=True)
    (repo / "pipeline" / "catalog.py").write_text('_CGI_TARGETS = {"47 UMa b"}\n')
    real = _run("Exemplars come from `_CGI_TARGETS`.", catalogue, tmp_path, repo=repo)
    assert "code-ref" not in _checks(real)
    invented = _run("Exemplars come from `_ROMAN_EXEMPLAR_SET`.", catalogue, tmp_path, repo=repo)
    assert "code-ref" in _checks(invented)


def test_survey_acronyms_are_not_treated_as_symbols(catalogue, tmp_path):
    """`KELT`, `OGLE` and `LICENSE` in backticks are not claims about our source tree."""
    findings = _run("Names from `KELT`, `OGLE`, `MASCARA`, plus a `LICENSE` file.",
                    catalogue, tmp_path)
    assert "code-ref" not in _checks(findings)


def test_unsourced_measurement_is_listed(catalogue, tmp_path):
    """The WASP-12b class: an upper limit written up as a measurement, with nothing to check."""
    findings = _run("WASP-12 b has a geometric albedo of 0.064.", catalogue, tmp_path)
    assert "sourcing" in _checks(findings)


def test_sourced_or_hedged_measurement_is_silent(catalogue, tmp_path):
    cited = _run("Bell et al. (2017) put the geometric albedo of 0.064 as an upper limit.",
                 catalogue, tmp_path)
    assert "sourcing" not in _checks(cited)
    limited = _run("The geometric albedo of 0.064 is an upper limit.", catalogue, tmp_path)
    assert "sourcing" not in _checks(limited)


def test_defining_a_term_is_not_a_measurement_claim(catalogue, tmp_path):
    findings = _run("**Geometric albedo** is the fraction of light a world reflects. See item 14.",
                    catalogue, tmp_path)
    assert "sourcing" not in _checks(findings)


# --- counts -----------------------------------------------------------------------------

def test_precise_count_about_our_data_is_an_error(catalogue, tmp_path):
    catalogue.counts["planets"] = 5764
    findings = _run("The dataset holds 5,764 planets today.", catalogue, tmp_path)
    assert "count" not in _checks(findings)
    wrong = _run("The dataset holds 5,773 planets today.", catalogue, tmp_path)
    counts = [f for f in wrong if f.check == "count"]
    assert counts and counts[0].severity == "error"


def test_honest_rounding_passes(catalogue, tmp_path):
    """"about 5,700 worlds" is rounding, not error — the checker must not punish plain English."""
    catalogue.counts["planets"] = 5764
    findings = _run("The dataset holds about 5,700 worlds.", catalogue, tmp_path)
    assert "count" not in _checks(findings)


def test_someone_elses_total_is_not_our_count(catalogue, tmp_path):
    findings = _run("`pscomppars` holds 6,324 planets today.", catalogue, tmp_path)
    assert "count" not in _checks(findings)


def test_a_shortfall_is_not_a_count(catalogue, tmp_path):
    findings = _run("The catalogue is ~560 planets behind.", catalogue, tmp_path)
    assert "count" not in _checks(findings)


# --- mechanics --------------------------------------------------------------------------

def test_ignore_marker_silences_one_line(catalogue, tmp_path):
    text = "Alias handling: `HD 95128 b` = `47 UMa b`. <!-- factcheck: ignore -->"
    assert _run(text, catalogue, tmp_path) == []


def test_a_marker_quoted_in_backticks_does_not_take_effect(catalogue, tmp_path):
    """Documenting the off marker in the README silently switched the whole README off."""
    text = ("Suppress a file with `<!-- factcheck: off -->`.\n"
            "The conversion is in `pipeline/cie.py`.")
    assert _checks(_run(text, catalogue, tmp_path)) == {"code-ref"}


def test_off_marker_silences_a_file(catalogue, tmp_path):
    text = "<!-- factcheck: off -->\nTrES-2 b renders near-black in `pipeline/nope.py`."
    assert _run(text, catalogue, tmp_path) == []


def test_prose_checks_skip_fenced_blocks_but_paths_do_not(catalogue, tmp_path):
    text = "```\nTrES-2 b renders near-black\npython3 pipeline/nope.py\n```"
    findings = _run(text, catalogue, tmp_path)
    assert _checks(findings) == {"code-ref"}


def test_missing_dataset_stands_the_catalogue_checks_down(tmp_path):
    empty = factcheck.load_catalogue(tmp_path / "absent.json")
    assert not empty.loaded
    findings = _run("HIP 71618 B renders near-black.", empty, tmp_path)
    assert not [f for f in findings if f.check in {"object-name", "colour-claim", "count"}]


def test_counts_come_from_the_data(catalogue):
    assert catalogue.counts["planets"] == 7
    assert catalogue.counts["anchors"] == 2
    assert catalogue.counts["cgi_targets"] == 2


def test_exit_status_is_one_when_an_error_survives(catalogue, tmp_path, capsys):
    doc = tmp_path / "draft.md"
    doc.write_text("The conversion is in `pipeline/cie.py`.")
    code = factcheck.main([str(doc), "--data", "/nonexistent.json"])
    capsys.readouterr()
    assert code == 1
