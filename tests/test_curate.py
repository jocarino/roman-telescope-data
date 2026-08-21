"""The gallery's default order: a hue-diverse deal, with the solar-system anchors dealt in
after it has run for a couple of rounds.

This is the front door of the site, so the properties worth pinning are the ones a visitor
actually experiences: the opening cards are exoplanets rather than the solar system, the opening
screens hold every colour the catalogue has rather than a run of one, and nothing is lost or
duplicated on the way. The exact positions further down are an implementation detail and
deliberately not asserted.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.colour.family import colour_family
from pipeline.curate import curated_order, curated_ranks
from tests.test_tours import make_record

# sRGB triples that land in distinct colour families (see pipeline/colour/family.py).
_SRGB = {
    "azure": (60, 165, 255),
    "orange": (224, 138, 60),
    "gold": (217, 200, 74),
    "teal": (47, 184, 184),
    "white": (240, 241, 244),
}
# Roughly the XYZ of each of the above, so the chroma term is not fed nonsense.
_XYZ = {
    "azure": (0.30, 0.32, 0.95),
    "orange": (0.40, 0.32, 0.09),
    "gold": (0.50, 0.55, 0.15),
    "teal": (0.28, 0.38, 0.48),
    "white": (0.85, 0.90, 0.98),
}


def planet(pid: str, family: str, *, lum: float = 0.4, dist_pc: float = 200.0):
    rec = make_record(pid, lum=lum, dist_pc=dist_pc, xyz=_XYZ[family])
    rec.true_colour.srgb = list(_SRGB[family])
    return rec


def anchor(pid: str, sma: float, family: str = "white"):
    rec = planet(pid, family)
    rec.provenance = "measured-albedo"
    rec.params.semi_major_axis_au = sma
    return rec


def families(records) -> list[str]:
    return [colour_family(tuple(r.true_colour.srgb)) for r in records]


def test_the_gallery_does_not_open_on_the_solar_system():
    """The site is about exoplanets. Whatever else the deal does, the cards a visitor meets
    first are not the five worlds they could have looked up in an atlas."""
    recs = [planet(f"model-{i}", "azure") for i in range(40)]
    recs += [planet(f"gold-{i}", "gold") for i in range(40)]
    recs += [anchor("neptune", 30.1), anchor("earth", 1.0), anchor("jupiter", 5.2)]
    opening = [r.id for r in curated_order(recs)[:12]]
    assert not ({"earth", "jupiter", "neptune"} & set(opening)), opening


def test_the_anchors_are_dealt_as_one_block_outward_from_the_sun():
    """They still arrive together and still read outward from the Sun — the run is what lets
    the calibration story be told about them as a group rather than one stray card."""
    recs = [planet(f"model-{i}", "azure") for i in range(40)]
    recs += [planet(f"gold-{i}", "gold") for i in range(40)]
    recs += [anchor("neptune", 30.1), anchor("earth", 1.0), anchor("jupiter", 5.2)]
    ids = [r.id for r in curated_order(recs)]
    at = [ids.index(x) for x in ("earth", "jupiter", "neptune")]
    assert at == sorted(at), at                      # outward from the Sun
    assert at[-1] - at[0] == 2, at                   # contiguous
    assert at[0] > 3, at                             # and not at the front


def test_anchors_without_an_orbit_sort_last_and_stay_deterministic():
    recs = [planet(f"model-{i}", "azure") for i in range(40)]
    no_orbit = anchor("mystery", 1.0)
    no_orbit.params.semi_major_axis_au = None
    recs += [no_orbit, anchor("earth", 1.0)]
    ids = [r.id for r in curated_order(recs)]
    assert ids.index("earth") + 1 == ids.index("mystery")


def test_the_opening_screens_hold_every_colour_not_the_biggest_one():
    """The bug this order exists to fix: alphabetically, the first 30 cards were 18 planets of
    one family and 5 of another. A round-robin deal cannot do that."""
    recs = [planet(f"white-{i}", "white") for i in range(40)]
    recs += [planet(f"azure-{i}", "azure") for i in range(40)]
    recs += [planet("gold-1", "gold"), planet("teal-1", "teal")]
    first = families(curated_order(recs)[:8])
    assert set(first) == {"white", "azure", "gold", "teal"}
    # A rare family is not merely present, it is on the first screen: one gold planet in 82 is
    # unfindable by scrolling, and it is exactly the kind of planet worth showing.
    assert "gold" in families(curated_order(recs)[:4])


def test_every_planet_is_dealt_exactly_once():
    recs = [planet(f"a-{i}", "azure") for i in range(5)]
    recs += [planet(f"w-{i}", "white") for i in range(9)]
    recs += [anchor("earth", 1.0)]
    order = curated_order(recs)
    assert [r.id for r in order] != [r.id for r in recs]  # it really did reorder
    assert sorted(r.id for r in order) == sorted(r.id for r in recs)
    assert sorted(curated_ranks(recs).values()) == list(range(len(recs)))


def test_the_order_does_not_depend_on_the_order_the_catalogue_arrived_in():
    """Two builds of the same data must deal the same cards — otherwise every data release
    reshuffles the front page for no reason anyone could explain."""
    recs = [planet(f"a-{i}", "azure", lum=0.3 + i * 0.01) for i in range(6)]
    recs += [planet(f"w-{i}", "white", lum=0.5) for i in range(6)]
    forward = [r.id for r in curated_order(recs)]
    assert [r.id for r in curated_order(list(reversed(recs)))] == forward


def test_a_family_leads_with_its_vivid_member_not_its_washed_out_one():
    """Chroma is what makes a card say what its colour family IS; a near-grey member of the
    family reads as one more beige swatch."""
    vivid = planet("vivid", "azure")
    vivid.true_colour.xyz = [0.25, 0.25, 1.10]  # far from the white point: high Lab C*
    washed = planet("washed", "azure")
    washed.true_colour.xyz = [0.50, 0.53, 0.60]  # nearly neutral
    assert [r.id for r in curated_order([washed, vivid])] == ["vivid", "washed"]


def test_a_family_does_not_deal_three_visual_twins_in_a_row():
    """The failure that made the first version look stuck: TRAPPIST-1 h, g and f are the same
    colour to the eye, and ranking by "best" alone dealt them as consecutive cards."""
    twins = []
    for i in range(3):
        t = planet(f"twin-{i}", "azure")
        t.true_colour.xyz = [0.25, 0.25, 1.10 + i * 0.0001]  # identical to the eye
        twins.append(t)
    odd = planet("odd-one", "azure")
    odd.true_colour.xyz = [0.34, 0.30, 0.62]  # same family, visibly different shade
    order = [r.id for r in curated_order([*twins, odd])]
    assert order[1] == "odd-one", order


def test_boost_reorders_within_a_family_but_never_jumps_one():
    """A planet the site tells stories about leads its own colour, but cannot displace the
    round-robin — the deal is what keeps the front page diverse."""
    plain = planet("plain", "azure")
    plain.true_colour.xyz = [0.25, 0.25, 1.10]  # the vivid one on chroma alone
    storied = planet("storied", "azure")
    storied.true_colour.xyz = [0.34, 0.30, 0.62]  # a little duller, but on a tour
    white = planet("a-white", "white")
    assert [r.id for r in curated_order([plain, storied, white])][0] == "plain"
    boosted = curated_order([plain, storied, white], boost={"storied"})
    assert [r.id for r in boosted][0] == "storied"
    # ...and the white planet is still dealt second, boost or no boost: one card per family.
    assert boosted[1].id == "a-white"


# ── the client's half of the deal ──────────────────────────────────────────────────────────
# The order is computed here and shipped as one integer per planet, but WHICH sort the gallery
# opens in lives in app.js — in three places that have to agree (the component's own property,
# the defaults table the "clear all filters" button and the persistence layer read, and the
# template's "a filter is set" dot). They silently disagreed once already: the property still
# said "name" while the defaults table said "curated", which loads the site in the old order
# with the "start here" strip hidden, because a sort that isn't the default reads as a filter.

_APP_JS = Path(__file__).resolve().parents[1] / "web" / "static" / "app.js"
_GALLERY_HTML = Path(__file__).resolve().parents[1] / "web" / "templates" / "gallery.html"


def test_the_gallery_opens_in_the_curated_order():
    found = set(re.findall(r'\bsort: "([a-z]+)"', _APP_JS.read_text()))
    # The share-link layer maps each knob to its URL parameter name (`sort: "sort"`); that is
    # a key, not a default, so it is not one of the places that has to agree.
    found.discard("sort")
    assert found == {"curated"}, f"app.js disagrees with itself about the default sort: {found}"
    assert "sort !== 'curated'" in _GALLERY_HTML.read_text()


def test_curated_is_offered_first_in_the_sort_menu():
    """The menu is rendered straight from sortLabels, so its key order is its display order."""
    labels = re.search(r"sortLabels: \{(.*?)\},", _APP_JS.read_text(), re.S).group(1)
    assert re.findall(r"(\w+):", labels)[0] == "curated"
