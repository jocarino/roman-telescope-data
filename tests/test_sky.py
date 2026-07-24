"""Sky position: constellation determination (Roman 1987), formatting, and the record
back-compat guarantee (releases generated before the sky chart must still validate)."""

from __future__ import annotations

import pytest

from pipeline.models import PlanetRecord, SkyPosition
from pipeline.sky import (
    CONSTELLATION_NAMES,
    NAKED_EYE_LIMIT_VMAG,
    _boundaries,
    build_sky,
    constellation_abbr,
    format_dec,
    format_ra,
)

# J2000 positions of well-known stars whose constellation is unambiguous.
KNOWN_STARS = [
    ("Polaris", 37.954, 89.264, "UMi"),
    ("Sirius", 101.287, -16.716, "CMa"),
    ("Betelgeuse", 88.793, 7.407, "Ori"),
    ("51 Peg", 344.3665, 20.7689, "Peg"),
    ("Proxima Cen", 217.429, -62.679, "Cen"),
    ("HD 189733", 300.182, 22.711, "Vul"),
    ("TRAPPIST-1", 346.622, -5.041, "Aqr"),
    ("GJ 1214", 258.831, 4.964, "Oph"),
    ("WASP-12", 97.637, 29.672, "Aur"),
    ("Kepler-186", 298.68, 43.955, "Cyg"),
    ("ups And", 24.199, 41.405, "And"),
    ("bet Pic", 86.821, -51.066, "Pic"),
]


@pytest.mark.parametrize(("name", "ra", "dec", "want"), KNOWN_STARS)
def test_constellation_known_stars(name: str, ra: float, dec: float, want: str) -> None:
    assert constellation_abbr(ra, dec) == want, name


def test_boundary_table_complete() -> None:
    """357 strips (the full Roman 1987 table) naming exactly the 88 IAU constellations,
    every abbreviation resolvable to a full name."""
    rows = _boundaries()
    assert len(rows) == 357
    abbrs = {abbr for _, _, _, abbr in rows}
    assert len(abbrs) == 88
    assert abbrs == set(CONSTELLATION_NAMES)


def test_poles_and_wraparound() -> None:
    # The celestial poles sit in Ursa Minor / Octans; RA is irrelevant there.
    assert constellation_abbr(123.4, 90.0) == "UMi"
    assert constellation_abbr(321.0, -90.0) == "Oct"
    # RA 0/360 wraparound stays valid (0h crosses Pisces at the equator).
    assert constellation_abbr(0.0, 5.0) == constellation_abbr(360.0, 5.0)


def test_format_ra_dec() -> None:
    assert format_ra(344.3665) == "22h 57m"
    assert format_ra(0.0) == "0h 00m"
    assert format_ra(359.999) == "0h 00m"  # rounds up and wraps, never "24h 00m"
    assert format_dec(20.7689) == "+20° 46′"
    assert format_dec(-5.041) == "−5° 02′"
    assert format_dec(-89.9999) == "−90° 00′"  # rounds without producing 60′


def test_build_sky_naked_eye_threshold() -> None:
    bright = build_sky(344.3665, 20.7689, 5.46)  # 51 Peg
    assert bright.constellation == "Pegasus"
    assert bright.constellation_abbr == "Peg"
    assert bright.naked_eye is True

    at_limit = build_sky(344.3665, 20.7689, NAKED_EYE_LIMIT_VMAG)
    assert at_limit.naked_eye is True

    faint = build_sky(344.3665, 20.7689, 11.0)
    assert faint.naked_eye is False

    unmeasured = build_sky(344.3665, 20.7689, None)
    assert unmeasured.v_mag is None
    assert unmeasured.naked_eye is False


def test_record_back_compat_without_sky() -> None:
    """A record serialised before the sky field existed must still validate, with sky None."""
    rec = PlanetRecord.model_validate(
        {
            "id": "x-b",
            "name": "X b",
            "host_star": {"name": "X", "teff_k": 5000.0},
            "params": {
                "assumed_cloud_state": "cloudy",
                "assumed_phase_angle_deg": 20.0,
            },
            "discovery": {"method": "Transit"},
            "is_light_isolable": True,
            "provenance": "model",
            "meta": {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "pipeline_version": "0.1.0",
                "schema_version": 1,
            },
        }
    )
    assert rec.sky is None

    rec.sky = SkyPosition(ra_deg=1.0, dec_deg=2.0, constellation="Pisces", constellation_abbr="Psc")
    assert PlanetRecord.model_validate(rec.model_dump()).sky.constellation == "Pisces"
