"""The solar system anchors: measured albedo spectra through the standard pipeline.

These tests are the project's public sanity check made executable — the pipeline must
reproduce the colours of planets we have photographs of. No network: the measured spectra
are committed under data/measured_albedo/.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.config import GRID_NM, ROMAN_CGI
from pipeline.emit.build import build_record
from pipeline.solar_system import solar_system_planets
from pipeline.spectrum.measured import karkoschka1998, payne2026_earth


@pytest.fixture(scope="module")
def records():
    return {
        pin.id: build_record(pin, [ROMAN_CGI], "2026-01-01T00:00:00+00:00")
        for pin in solar_system_planets()
    }


def test_all_five_anchors_present(records):
    assert set(records) == {"earth", "jupiter", "saturn", "uranus", "neptune"}


def test_measured_curves_are_sane_albedos():
    for planet in ("jupiter", "saturn", "uranus", "neptune"):
        a = karkoschka1998(planet).geometric_albedo(GRID_NM)
        assert a.shape == GRID_NM.shape
        assert np.all((a >= 0.0) & (a <= 1.0))
    e = payne2026_earth().geometric_albedo(GRID_NM)
    assert np.all((e >= 0.0) & (e <= 1.0))


def test_neptune_methane_bands_present():
    """The 619 nm CH4 band must survive interpolation — it is what makes Neptune blue-green."""
    nep = karkoschka1998("neptune")
    band = nep.geometric_albedo(np.array([619.0]))[0]
    continuum = nep.geometric_albedo(np.array([550.0]))[0]
    assert band < 0.6 * continuum


def test_provenance_and_sources(records):
    for rec in records.values():
        assert rec.provenance == "measured-albedo"
        assert rec.is_light_isolable
        assert rec.params.sources.equilibrium_temp_k == "measured"
        assert rec.params.sources.cloud_state == "measured"


def test_colours_match_known_planets(records):
    """The point of the anchors: physics must land near what the photos show."""
    def srgb(rec):
        return rec.true_colour.srgb

    # Jupiter and Saturn: warm cream — red >= green > blue.
    for pid in ("jupiter", "saturn"):
        r, g, b = srgb(records[pid])
        assert r >= g > b, f"{pid} should be warm: {r, g, b}"
    # Uranus and Neptune: methane worlds — blue/green above red.
    for pid in ("uranus", "neptune"):
        r, g, b = srgb(records[pid])
        assert b > r and g > r, f"{pid} should be blue-green: {r, g, b}"
    # Earth: the pale blue dot — blue highest, and pale (all channels high after
    # the luminance normalisation).
    r, g, b = srgb(records["earth"])
    assert b > r and b > g
    assert min(r, g, b) > 120


def test_saturn_warmer_than_jupiter(records):
    """Karkoschka's spectra have Saturn yellower than Jupiter; the colours must keep that."""
    jr, jg, jb = records["jupiter"].true_colour.srgb
    sr, sg, sb = records["saturn"].true_colour.srgb
    assert (sr - sb) > (jr - jb)


def test_sun_swap_is_identity_for_solar_planets(records):
    """Host star IS the Sun, so re-lighting by the Sun must change nothing — a built-in
    self-consistency check on the whole illuminant path."""
    for rec in records.values():
        assert rec.sun_swap.delta_e2000_vs_true < 0.05


def test_every_anchor_has_a_real_photo(records):
    for rec in records.values():
        assert rec.real_observations, f"{rec.id} must carry a real photograph"
        obs = rec.real_observations[0]
        assert "visible light" in obs.band
        assert obs.license.startswith("Public domain")


def test_roman_view_present(records):
    for rec in records.values():
        view = rec.instrument_views[0]
        assert view.instrument_id == "roman-cgi"
        assert len(view.band_samples.samples) == 4
        assert view.reconstruction_error.delta_e2000 >= 0.0
