"""What `tools/newswatch.py` must never get wrong.

Three of these are regression pins on mistakes the tool actually made while being built,
and they are the ones worth keeping:

  - the Roman band gate, because publishing "as Roman would see it" from a stale band model
    is the one unrecoverable error available to this project;
  - the catalogue join, because it silently reported catalogued planets as MISSING (records
    are keyed by the expanded display name `beta Pictoris b`, the alias table returns the
    Archive name `bet Pic b`) and nobody would double-check that line;
  - the alias guard, because the obvious first version ("a designation must contain a digit")
    discards every Greek-letter and variable-star planet: bet Pic b, AU Mic b, eps Eri b.

Everything here runs offline against tests/fixtures/feeds — no network, no planets.json.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pipeline.config import ROMAN_CGI
from tools import newswatch as nw

FIXTURES = Path("tests/fixtures/feeds")


# --- the gate on the most dangerous number the tool prints -----------------

def test_flight_bands_match_the_pipeline_config():
    """newswatch repeats the band ids to stay stdlib-only. This is the pin that makes that
    safe: correct pipeline/config.py and CI fails here rather than silently un-gating."""
    assert nw.FLIGHT_BANDS == tuple(b.id for b in ROMAN_CGI.bands)


def _record(band_ids):
    return {
        "instrument_views": [{
            "band_samples": {"samples": [{"band_id": b} for b in band_ids]},
        }]
    }


def test_roman_view_withheld_when_the_data_predates_the_band_correction():
    stale, why = nw.roman_is_stale(_record(["cgi-575", "cgi-660", "cgi-730", "cgi-835"]))
    assert stale
    assert "cgi-660" in why and "cgi-825" in why


def test_roman_view_allowed_on_flight_configuration():
    stale, why = nw.roman_is_stale(_record(list(nw.FLIGHT_BANDS)))
    assert not stale and why == ""


def test_a_record_with_no_roman_view_is_treated_as_stale():
    assert nw.roman_is_stale({"instrument_views": []})[0]


# --- normalisation: press spelling vs Archive spelling ---------------------

@pytest.mark.parametrize(
    ("press", "archive"),
    [
        ("TRAPPIST-1e", "TRAPPIST-1 e"),
        ("K2-18b", "K2-18 b"),
        ("HD189733b", "HD 189733 b"),
        ("HD 189733 b", "HD 189733 b"),
        ("Barnard's star", "Barnard s star"),
        ("PSR B1257+12 c", "PSR B1257+12 c"),
    ],
)
def test_press_and_archive_spellings_collapse_to_the_same_key(press, archive):
    assert nw.normalise(press) == nw.normalise(archive)


@pytest.mark.parametrize(
    ("archive_name", "press_form"),
    [
        ("51 Peg b", "51 Pegasi b"),
        ("bet Pic b", "beta Pictoris b"),
        ("ups And d", "upsilon Andromedae d"),
        ("eps Eri b", "epsilon Eridani b"),
        ("AU Mic b", "AU Microscopii b"),
        ("GJ 1214 b", "Gliese 1214 b"),
    ],
)
def test_expansion_covers_the_form_the_press_actually_prints(archive_name, press_form):
    """The Archive abbreviates; the press spells out. Expanding only long->short (the first
    thing you write) matches nothing, because the name we hold is already short."""
    assert nw.normalise(press_form) in nw._expand_word_forms(archive_name)


def test_greek_and_constellation_expansion_is_bidirectional():
    forms = nw._expand_word_forms("bet Pic b")
    assert nw.normalise("bet Pic b") in forms
    assert nw.normalise("beta Pic b") in forms
    assert nw.normalise("beta Pictoris b") in forms


# --- matching --------------------------------------------------------------

@pytest.fixture
def aliases():
    return {
        "planets": {
            nw.normalise("TRAPPIST-1 e"): "TRAPPIST-1 e",
            nw.normalise("TRAPPIST-1 f"): "TRAPPIST-1 f",
            nw.normalise("K2-18 b"): "K2-18 b",
            nw.normalise("bet Pic b"): "bet Pic b",
            nw.normalise("beta Pictoris b"): "bet Pic b",
            nw.normalise("TOI-700 d"): "TOI-700 d",
        },
        "hosts": {nw.normalise("TRAPPIST-1"): "TRAPPIST-1"},
    }


def test_longest_window_wins(aliases):
    """'TRAPPIST-1 e' must beat the host 'TRAPPIST-1' sitting inside it."""
    planets, hosts = nw.find_planets("Water vapour found on TRAPPIST-1 e", aliases)
    assert planets == ["TRAPPIST-1 e"] and hosts == []


def test_press_spelling_resolves_to_the_archive_name(aliases):
    planets, _ = nw.find_planets("New image of beta Pictoris b released", aliases)
    assert planets == ["bet Pic b"]


def test_bare_host_matches_as_a_host_not_a_planet(aliases):
    planets, hosts = nw.find_planets("The TRAPPIST-1 system at ten", aliases)
    assert planets == [] and hosts == ["TRAPPIST-1"]


def test_ordinary_prose_matches_nothing(aliases):
    planets, hosts = nw.find_planets(
        "Astronomers report the first detection of water in a protoplanetary disk", aliases)
    assert planets == [] and hosts == []


def test_min_alias_length_is_not_a_digit_requirement():
    """The guard that discards `bet Pic b` if you get it wrong. See the module docstring."""
    assert nw.MIN_ALIAS_LEN <= len(nw.normalise("FU Tau b"))
    assert not any(c.isdigit() for c in nw.normalise("bet Pic b"))


# --- the catalogue join ----------------------------------------------------

def _rec(pid, name, host, hex_="#8bd6f4"):
    return {
        "id": pid, "name": name, "host_star": {"name": host, "teff_k": 3457.0},
        "provenance": "model",
        "true_colour": {"hex": hex_, "palette": [], "confidence": "high",
                        "luminance_y": 0.1, "out_of_gamut": False},
        "params": {"radius_r_earth": 2.4, "mass_m_earth": 8.9,
                   "equilibrium_temp_k": 284.0, "sources": {}},
        "instrument_views": [{
            "band_samples": {"samples": [{"band_id": b} for b in nw.FLIGHT_BANDS],
                             "source": "simulated"},
            "colour": {"hex": "#e0ca8c"},
            "reconstruction_error": {"delta_e2000": 31.3},
        }],
        "system": {"member_count": 2},
        "meta": {"generated_at": "2026-08-06T00:00:00+00:00"},
    }


def _cat():
    return nw.Catalogue([
        _rec("bet-pic-b", "beta Pictoris b", "beta Pictoris"),
        _rec("k2-18-b", "K2-18 b", "K2-18"),
    ])


def test_archive_name_finds_the_record_stored_under_its_display_name():
    """Regression: `bet Pic b` was reported as NOT IN OUR CATALOGUE because the record is
    keyed `beta Pictoris b`. That is the tool's single most trusted line."""
    cat = _cat()
    assert "bet Pic b" in cat
    assert cat.get("bet Pic b")["id"] == "bet-pic-b"


def test_display_name_still_resolves():
    assert _cat().get("beta Pictoris b")["id"] == "bet-pic-b"


def test_a_genuinely_absent_planet_is_absent():
    assert "LHS 1140 b" not in _cat()


def test_host_lookup_uses_the_slug_too():
    assert _cat().by_host("bet Pic") is None          # not the stored host spelling
    assert _cat().by_host("beta Pictoris")["id"] == "bet-pic-b"


# --- filtering and ranking -------------------------------------------------

def _item(feed, title, uid, announce_type=None, summary=""):
    return nw.Item(feed=feed, uid=uid, title=title, link="x", summary=summary,
                   published=datetime.now(UTC), announce_type=announce_type)


PRESS = nw.Feed("nasa", "NASA", "u", "press")
ARXIV = nw.Feed("arxiv", "arXiv", "u", "preprint")


def _state():
    return {"seen": {}, "planet_last_surfaced": {}, "last_poll": None}


def test_arxiv_replacements_are_dropped(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    items = [_item(ARXIV, "A new look at K2-18 b", "u1", announce_type="replace")]
    kept, dropped = nw.rank(items, _cat(), _state(), now=datetime.now(UTC))
    assert kept == [] and dropped["replace"] == 1


def test_a_catalogue_paper_naming_many_planets_is_dropped(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    title = "Validation of TRAPPIST-1 e, TRAPPIST-1 f, K2-18 b, bet Pic b and TOI-700 d"
    kept, dropped = nw.rank([_item(ARXIV, title, "u2")], _cat(), _state(), now=datetime.now(UTC))
    assert kept == [] and dropped["too_many_planets"] == 1


def test_a_planet_surfaced_last_week_is_suppressed(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    now = datetime.now(UTC)
    state = _state()
    state["planet_last_surfaced"]["K2-18 b"] = (now - timedelta(days=7)).isoformat()
    kept, dropped = nw.rank([_item(PRESS, "K2-18 b in the news", "u3")], _cat(), state, now=now)
    assert kept == [] and dropped["suppressed"] == 1


def test_the_same_planet_is_surfaceable_again_after_the_window(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    now = datetime.now(UTC)
    state = _state()
    state["planet_last_surfaced"]["K2-18 b"] = (
        now - timedelta(days=nw.SUPPRESS_DAYS + 1)).isoformat()
    kept, _ = nw.rank([_item(PRESS, "K2-18 b in the news", "u4")], _cat(), state, now=now)
    assert len(kept) == 1


def test_press_outranks_a_preprint_about_the_same_planet(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    items = [_item(ARXIV, "Transit timing of K2-18 b", "u5"),
             _item(PRESS, "Signs of water on K2-18 b", "u6")]
    kept, _ = nw.rank(items, _cat(), _state(), now=datetime.now(UTC))
    assert kept[0].feed.kind == "press"


def test_a_three_week_old_press_release_is_not_a_newsjack(aliases, monkeypatch):
    """Found by running the real feeds: ESO's holds ten slow-moving items, so its 'newest'
    story about beta Pictoris d was three weeks old and still ranked top."""
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    now = datetime.now(UTC)
    old = _item(PRESS, "Faintest planet ever imaged: bet Pic b", "u9")
    old.published = now - timedelta(days=21)
    kept, dropped = nw.rank([old], _cat(), _state(), now=now)
    assert kept == [] and dropped["stale"] == 1


def test_an_undated_item_is_kept_not_silently_dropped(aliases, monkeypatch):
    """Every feed we poll dates its items, so an undated one is a parsing surprise. Dropping
    it would hide the bug; keeping it makes the bug visible in the output."""
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    undated = _item(PRESS, "Signs of water on K2-18 b", "u10")
    undated.published = None
    kept, _ = nw.rank([undated], _cat(), _state(), now=datetime.now(UTC))
    assert len(kept) == 1


def test_an_item_naming_no_planet_is_dropped(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    kept, dropped = nw.rank([_item(PRESS, "Rings in the sky: orbital data centres", "u7")],
                            _cat(), _state(), now=datetime.now(UTC))
    assert kept == [] and dropped["no_planet"] == 1


def test_a_planet_outside_the_catalogue_still_surfaces(aliases, monkeypatch):
    """The gap is the most valuable output here, so it must never be filtered away."""
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    kept, _ = nw.rank([_item(PRESS, "First image of TOI-700 d", "u8")],
                      _cat(), _state(), now=datetime.now(UTC))
    assert len(kept) == 1
    assert any("NOT in our catalogue" in r for r in kept[0].reasons)


# --- feed parsing, offline -------------------------------------------------

@pytest.mark.skipif(not FIXTURES.exists(), reason="run `newswatch feeds --save-fixture` first")
@pytest.mark.parametrize("feed", nw.FEEDS, ids=lambda f: f.id)
def test_every_saved_feed_parses_to_items_with_titles_and_links(feed):
    body = nw.fetch_feed(feed, fixture=FIXTURES)
    items = nw.parse_feed(feed, body)
    assert items, f"{feed.id} parsed to nothing"
    assert all(i.title for i in items)
    assert all(i.link for i in items)
    assert all(i.uid for i in items)


@pytest.mark.skipif(not FIXTURES.exists(), reason="run `newswatch feeds --save-fixture` first")
def test_arxiv_announce_type_is_read_from_the_arxiv_namespace():
    items = nw.parse_feed(nw.FEEDS[-1], nw.fetch_feed(nw.FEEDS[-1], fixture=FIXTURES))
    assert any(i.announce_type in {"new", "replace", "cross"} for i in items)


@pytest.mark.skipif(not FIXTURES.exists(), reason="run `newswatch feeds --save-fixture` first")
def test_no_feed_exceeds_the_per_feed_cap():
    for feed in nw.FEEDS:
        items = nw.parse_feed(feed, nw.fetch_feed(feed, fixture=FIXTURES))
        assert len(items) <= nw.MAX_ITEMS_PER_FEED


# --- the alert that reaches a phone ----------------------------------------

def _resolve(title, aliases, monkeypatch, cat=None):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    it = _item(PRESS, title, "a1")
    it.planets, it.hosts = nw.find_planets(title, aliases)
    return it, nw.resolve_target(it, cat or _cat())


def test_target_shows_the_display_name_not_the_archive_name(aliases, monkeypatch):
    """The alert is read by a human and links to the site, so it must say what the site says."""
    _, t = _resolve("New image of beta Pictoris b released", aliases, monkeypatch)
    assert t.kind == "planet"
    assert t.name == "beta Pictoris b"


def test_a_host_only_match_never_becomes_the_string_unknown(aliases, monkeypatch):
    """Regression: a story naming only a host fell through to 'unknown', which rendered a
    Bluesky search for 'unknown' and a fast-path command reading --planet "unknown"."""
    it, t = _resolve("The TRAPPIST-1 system at ten", aliases, monkeypatch)
    assert t.kind == "host" and t.name == "TRAPPIST-1"
    text = nw.alert_text(it, t, "https://example.test", now=datetime.now(UTC))
    assert "unknown" not in text
    assert "--planet" not in text        # never tell someone to build a planet we can't name


def test_a_missing_planet_alert_carries_a_runnable_fast_path(aliases, monkeypatch):
    it, t = _resolve("First image of TOI-700 d", aliases, monkeypatch)
    assert t.kind == "planet-missing"
    text = nw.alert_text(it, t, "https://example.test", now=datetime.now(UTC))
    assert 'build --planet "TOI-700 d"' in text
    assert "NOT IN OUR CATALOGUE" in text


def test_press_is_act_now_and_a_preprint_is_pre_build():
    """'Popping off' and 'about to' need opposite responses; alerting both the same way
    trains you to ignore both."""
    assert nw.tier_of(_item(PRESS, "t", "x")) == nw.TIER_ACT
    assert nw.tier_of(_item(ARXIV, "t", "x")) == nw.TIER_STOCK


def test_an_act_now_alert_pushes_the_reply_window_and_stock_does_not(aliases, monkeypatch):
    monkeypatch.setattr(nw, "_ALIASES", aliases)
    now = datetime.now(UTC)
    for feed, expect_window in ((PRESS, True), (ARXIV, False)):
        it = _item(feed, "Signs of water on K2-18 b", "x")
        it.planets, it.hosts = nw.find_planets(it.title, aliases)
        text = nw.alert_text(it, nw.resolve_target(it, _cat()), "https://example.test", now=now)
        assert ("~2 h" in text) is expect_window
        assert ("stock" in text) is not expect_window


def test_every_alert_fits_in_one_telegram_message(aliases, monkeypatch):
    """Telegram hard-caps at 4096 characters; the alert is a summary and must not be truncated
    into uselessness. The full briefing goes as an attachment instead."""
    now = datetime.now(UTC)
    long_title = "Astronomers report " + "a very long headline " * 20
    for feed in (PRESS, ARXIV):
        it, t = _resolve(f"{long_title} about K2-18 b", aliases, monkeypatch)
        it.feed = feed
        assert len(nw.alert_text(it, t, "https://example.test", now=now)) < nw.TELEGRAM_LIMIT


def test_alert_escapes_html_so_a_headline_cannot_break_the_message(aliases, monkeypatch):
    it, t = _resolve("K2-18 b <b>hype</b> & 'quotes'", aliases, monkeypatch)
    text = nw.alert_text(it, t, "https://example.test", now=datetime.now(UTC))
    assert "&lt;b&gt;hype&lt;/b&gt;" in text and "&amp;" in text


def test_a_stale_band_model_is_withheld_in_the_alert_too(aliases, monkeypatch):
    """The gate must hold on the phone as well as in the terminal — the alert is the surface
    someone actually posts from."""
    stale_rec = _rec("k2-18-b", "K2-18 b", "K2-18")
    stale_rec["instrument_views"][0]["band_samples"]["samples"] = [
        {"band_id": b} for b in ("cgi-575", "cgi-660", "cgi-730", "cgi-835")
    ]
    cat = nw.Catalogue([stale_rec])
    it, t = _resolve("Signs of water on K2-18 b", aliases, monkeypatch, cat=cat)
    text = nw.alert_text(it, t, "https://example.test", now=datetime.now(UTC))
    assert "withheld" in text
    assert "as Roman would see it" not in text


def test_telegram_is_absent_rather_than_silently_disabled(monkeypatch):
    """A notifier that quietly does nothing is worse than none — you would trust it."""
    monkeypatch.delenv("NEWSWATCH_TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("NEWSWATCH_TELEGRAM_CHAT_ID", raising=False)
    assert nw.Telegram.from_env() is None
    monkeypatch.setenv("NEWSWATCH_TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("NEWSWATCH_TELEGRAM_CHAT_ID", "c")
    assert nw.Telegram.from_env() == nw.Telegram("t", "c")


# --- colour naming (alt text depends on it being sane) ---------------------

@pytest.mark.parametrize(
    ("hex_str", "expected"),
    [("#ffffff", "very pale grey"), ("#000000", "near-black grey"),
     ("#1a3fd0", "blue"), ("#8bd6f4", "pale cyan-blue")],
)
def test_colour_names_are_the_words_a_blind_reader_gets(hex_str, expected):
    assert nw.colour_name(hex_str) == expected


# --- the scaffolds must stay scaffolds -------------------------------------

def test_copy_scaffolds_always_leave_the_physics_sentence_blank():
    """A ready-to-post caption is the thing 11-bluesky-mastodon.md says kills the account.
    If someone ever 'helpfully' fills this in, this test is what stops it shipping."""
    rec = {
        "id": "k2-18-b", "name": "K2-18 b", "provenance": "model",
        "true_colour": {"hex": "#8bd6f4", "palette": [], "confidence": "high",
                        "luminance_y": 0.1, "out_of_gamut": False},
    }
    out: list[str] = []
    nw.brief_copy(rec, out, "https://example.test")
    text = "\n".join(out)
    assert "⟨" in text and "⟩" in text
    assert "ONE sentence of physics" in text
    assert "utm_medium=newsjack" in text
