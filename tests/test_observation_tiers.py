"""The gallery's "How real" axis, and the Roman shortlist that used to be tangled up in it.

These two answer different questions and the site conflated them for a while: Roman's target
list rode inside a filter labelled "modelled vs measured colour", which implied that being
observable by Roman said something about how a colour was derived. It says nothing of the
kind. The tests below hold the two apart and pin the honesty wording that depends on it.
"""

from functools import lru_cache
from pathlib import Path

from pipeline.models import PlanetsFile
from web.build import _index_entry, _load_roman_ids, _observation_tier

PLANETS_JSON = Path("data/planets.json")


@lru_cache(maxsize=1)
def _records() -> tuple:
    return tuple(PlanetsFile.model_validate_json(PLANETS_JSON.read_text()).planets)


def test_every_planet_lands_in_exactly_one_tier() -> None:
    """The tiers partition the catalogue: no planet is untiered, none is double-counted."""
    tiers = {"colour", "photo", "imaged", "unseen", "lost"}
    seen = [_observation_tier(r) for r in _records()]
    assert set(seen) <= tiers
    assert len(seen) == len(_records())


def test_measured_spectrum_outranks_a_photograph() -> None:
    """The five anchors have BOTH a measured spectrum and a real photo, so order matters.

    They must land in "colour", not "photo": the whole point of those five is that the swatch
    itself is measured, which is a stronger claim than "someone has a picture of it".
    """
    by_id = {r.id: r for r in _records()}
    for pid in ("earth", "jupiter", "saturn", "uranus", "neptune"):
        rec = by_id[pid]
        assert rec.real_observations, f"{pid} lost its photograph"
        assert _observation_tier(rec) == "colour"


def test_photographed_planets_are_the_ones_with_a_real_image() -> None:
    """"Photographed" means an image is on file — not merely that imaging found the planet."""
    photo = {r.id for r in _records() if _observation_tier(r) == "photo"}
    assert photo == {r.id for r in _records()
                     if r.real_observations and r.provenance != "measured-albedo"}
    # ...and it is a strict subset of the direct-imaging discoveries, which is why "imaged"
    # (found by imaging, no picture here) has to exist as a separate tier rather than collapse.
    imaged_any = {r.id for r in _records() if r.discovery.method == "Imaging"}
    assert photo < imaged_any


def test_microlensing_is_its_own_tier_not_a_missing_photo() -> None:
    """A microlensing planet is not "not yet seen" — it can never be seen again, by anyone."""
    lost = [r for r in _records() if _observation_tier(r) == "lost"]
    assert lost, "expected at least one never-observable-again planet"
    assert all(not r.is_light_isolable for r in lost)


def test_the_common_tier_is_not_written_into_the_index() -> None:
    """"Never seen" is ~98% of the catalogue and is stored by being absent (like `fic`).

    If this ever starts being written out, the index grows by tens of KB for a field whose
    value the browser can infer — and `results()` must keep reading a missing `obs` as unseen.
    """
    for rec in _records()[:200]:
        entry = _index_entry(rec)
        assert (_observation_tier(rec) == "unseen") == ("obs" not in entry)


def test_roman_shortlist_reaches_the_gallery_whole() -> None:
    """Every target on the board's shortlist that exists in the catalogue gets the flag.

    The regression this guards: the shortlist was duplicated as a four-name literal in the
    pipeline, so only three of the twenty-odd targets were ever marked, and the gallery and
    the /roman board quietly disagreed about who was on Roman's list.
    """
    roman_ids = _load_roman_ids()
    assert len(roman_ids) > 10, "shortlist looks truncated"
    joined = {r.id for r in _records() if r.id in roman_ids}
    flagged = {r.id for r in _records() if _index_entry(r, None, None, roman_ids).get("rt")}
    assert flagged == joined
    assert len(flagged) > 3


def test_being_a_roman_target_is_not_an_observation_tier() -> None:
    """Roman targets are modelled like everything else — the shortlist must not promote them.

    This is the conflation the split exists to prevent: no target may land in a tier that
    claims someone has caught its light, purely by virtue of being on the list.
    """
    roman_ids = _load_roman_ids()
    for rec in _records():
        if rec.id in roman_ids and rec.provenance != "measured-cgi":
            assert _observation_tier(rec) in {"unseen", "imaged"}
