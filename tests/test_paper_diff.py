"""The paper diff, where the safety property lives.

The design rule this file exists to enforce: **the model only quotes; Python decides.** Every
test here exercises the deciding half, because that is the half a wrong answer from would
matter — a bad quote is visible next to its source sentence, a bad verdict is not.

Nothing here calls the API. The extraction is stubbed; the arithmetic is real.
"""

from __future__ import annotations

import pytest

from tools import newswatch as nw
from tools.paper_diff import (
    TOLERANCE_FRACTION,
    TOLERANCE_KELVIN,
    Extraction,
    Quote,
    arxiv_id_from,
    compare,
    to_canonical,
)


def _ex(*quotes: Quote) -> Extraction:
    return Extraction(quotes=list(quotes), planet="Test b", note="")


def _q(quantity, value, unit, sentence="stated in the abstract"):
    return Quote(quantity=quantity, value=value, unit=unit, sentence=sentence)


# --- unit conversion: ours, never the model's ------------------------------

@pytest.mark.parametrize(
    ("quantity", "value", "unit", "expected"),
    [
        ("radius", 1.0, "R_Earth", 1.0),
        ("radius", 1.0, "R_Jup", 11.2089),
        # LaTeX, as abstracts actually print units. A normaliser that gives up here
        # silently disables the diff on most real papers.
        ("radius", 1.0, "$R_{\\rm Jup}$", 11.2089),
        ("radius", 1.0, "R_\\oplus", 1.0),
        ("radius", 1.0, "$R_\\oplus$", 1.0),
        ("radius", 2.0, " RJup ", 22.4178),
        ("mass", 1.0, "M_Jup", 317.828),
        ("mass", 1.0, "M_Earth", 1.0),
        ("mass", 1.0, "M_\\odot", 332946.0),
        ("mass", 1.0, "$M_{\\rm Earth}$", 1.0),
        ("equilibrium_temperature", 600.0, "K", 600.0),
        ("host_teff", 8039.0, "Kelvin", 8039.0),
    ],
)
def test_units_convert_to_our_scale(quantity, value, unit, expected):
    assert to_canonical(quantity, value, unit) == pytest.approx(expected, rel=1e-6)


def test_an_unrecognised_unit_returns_none_rather_than_passing_through():
    """The dangerous failure would be treating an unknown unit as if it were ours — that is a
    silent factor-of-11 error in the exact number the checklist protects."""
    assert to_canonical("radius", 1.0, "furlongs") is None
    assert to_canonical("mass", 1.0, "") is None


def test_an_unrecognised_unit_never_reports_superseded():
    [c] = compare({"radius": 2.0}, _ex(_q("radius", 1.0, "furlongs")))
    assert c.theirs is None
    assert c.superseded is False
    assert "compare by hand" in c.detail


# --- the tolerance decision ------------------------------------------------

def test_a_matching_radius_is_not_superseded():
    [c] = compare({"radius": 2.37}, _ex(_q("radius", 2.37, "R_Earth")))
    assert c.superseded is False


def test_a_radius_outside_ten_percent_is_superseded():
    [c] = compare({"radius": 2.37}, _ex(_q("radius", 3.10, "R_Earth")))
    assert c.superseded is True
    assert "%" in c.detail


def test_the_radius_tolerance_boundary_is_exclusive():
    """Exactly at tolerance is NOT superseded; a hair over is. Pinned because an off-by-one
    here silently changes what gets published."""
    theirs = 10.0
    at = theirs * (1 + TOLERANCE_FRACTION)
    over = theirs * (1 + TOLERANCE_FRACTION) + 0.01
    assert compare({"radius": at}, _ex(_q("radius", theirs, "R_Earth")))[0].superseded is False
    assert compare({"radius": over}, _ex(_q("radius", theirs, "R_Earth")))[0].superseded is True


def test_temperature_uses_an_absolute_tolerance_not_a_fraction():
    """100 K on a 600 K planet is 17% — a fractional rule would flag it. The checklist says
    absolute, and cool planets are exactly where the difference bites."""
    ok = compare({"equilibrium_temperature": 600.0},
                 _ex(_q("equilibrium_temperature", 690.0, "K")))[0]
    bad = compare({"equilibrium_temperature": 600.0},
                  _ex(_q("equilibrium_temperature", 750.0, "K")))[0]
    assert ok.superseded is False
    assert bad.superseded is True
    assert TOLERANCE_KELVIN == 100.0


def test_a_jupiter_radius_paper_against_an_earth_radius_catalogue_compares_correctly():
    """The end-to-end point of doing conversion ourselves: 1.26 R_Jup IS our 14.12 R⊕."""
    [c] = compare({"radius": 14.12}, _ex(_q("radius", 1.26, "R_Jup")))
    assert c.theirs == pytest.approx(14.12, rel=0.01)
    assert c.superseded is False


def test_a_missing_value_on_our_side_is_reported_not_guessed():
    [c] = compare({"radius": None}, _ex(_q("radius", 2.0, "R_Earth")))
    assert c.superseded is False
    assert "no value" in c.detail


# --- finding the paper -----------------------------------------------------

@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://arxiv.org/abs/2608.03094", "2608.03094"),
        ("http://arxiv.org/pdf/2504.12267", "2504.12267"),
        ("https://www.eso.org/public/news/eso2609/", None),  # would need a page fetch
        ("", None),
    ],
)
def test_arxiv_id_is_read_from_the_url_when_it_is_there(url, expected, monkeypatch):
    # Block the network so only the URL-parsing path is under test.
    monkeypatch.setattr("tools.paper_diff.urllib.request.urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("blocked")))
    assert arxiv_id_from(url) == expected


# --- the alert never lies about a diff it didn't do ------------------------

def test_no_diff_is_rendered_when_the_flag_is_off():
    assert nw.paper_diff_lines(object(), {}) == []


def test_a_broken_diff_degrades_to_a_note_and_never_blocks_the_alert(monkeypatch):
    """A story is breaking; a failed third-party call must not cost you the alert."""
    monkeypatch.setattr(nw, "DIFF_PAPER", True)
    import tools.paper_diff as pd
    monkeypatch.setattr(pd, "diff_paper",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    rec = {"params": {"radius_r_earth": 1.0}, "host_star": {"teff_k": 5000.0}}
    lines = nw.paper_diff_lines(nw.Item(feed=nw.FEEDS[0], uid="u", title="t", link="l",
                                        summary="", published=None), rec)
    assert any("by hand" in line for line in lines)


def test_a_diff_that_compared_nothing_says_so_and_never_implies_agreement(monkeypatch):
    """Two failures are possible here and only one of them used to be guarded.

    Claiming 'no differences found' when nothing was compared would be dangerous. But staying
    *silent* was also wrong: it made "ran and everything agreed" indistinguishable from "never
    ran", so the honest reaction to a briefing was "did it even do any checks?". State the
    reason; never imply a comparison that didn't happen.
    """
    monkeypatch.setattr(nw, "DIFF_PAPER", True)
    nw._DIFF_CACHE.clear()
    import tools.paper_diff as pd
    monkeypatch.setattr(pd, "diff_paper", lambda *a, **k: {
        "status": "no_numbers", "reason": "the abstract states none of the four parameters",
    })
    rec = {"params": {"radius_r_earth": 1.0}, "host_star": {"teff_k": 5000.0}}
    lines = nw.paper_diff_lines(nw.Item(feed=nw.FEEDS[0], uid="u", title="t", link="l",
                                        summary="", published=None), rec)
    text = "\n".join(lines)
    assert "none of the four parameters" in text
    assert "by hand" in text
    assert "agrees" not in text and "within tolerance" not in text


def test_the_verdict_block_distinguishes_not_run_from_compared(monkeypatch):
    """The three lines at the top are the answer to 'what am I supposed to look at'."""
    rec = {"params": {"radius_r_earth": 1.0, "mass_m_earth": 1.0,
                      "equilibrium_temp_k": 300.0}, "host_star": {"teff_k": 5000.0}}
    item = nw.Item(feed=nw.FEEDS[0], uid="v1", title="Water on K2-18 b", link="l",
                   summary="", published=None)

    monkeypatch.setattr(nw, "DIFF_PAPER", False)
    out: list[str] = []
    nw.verdict_block(out, rec, item)
    assert any("not run" in ln for ln in out)
    assert any("[YOU ]" in ln for ln in out)

    nw._DIFF_CACHE.clear()
    monkeypatch.setattr(nw, "DIFF_PAPER", True)
    import tools.paper_diff as pd
    monkeypatch.setattr(pd, "diff_paper", lambda *a, **k: {
        "status": "checked", "arxiv_id": "1", "backend": "cli",
        "comparisons": [pd.Comparison("radius", 1.0, 1.0, "R_Earth", "s", False, "Δ 0%")],
    })
    out = []
    nw.verdict_block(out, rec, item)
    assert any("[OK  ] 2." in ln and "radius" in ln for ln in out)
