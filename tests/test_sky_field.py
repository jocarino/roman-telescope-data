"""The starfield is shared across every planet page; the chart just points at it.

Inlined, the ~5.8k dots were 93% of a planet page. These tests pin the two properties that
make sharing safe: the file is the same for everyone, and it still draws one rect per star
(the overlap of 34%-opaque dots is what makes dense regions like the Kepler field read as a
bright clump — a single merged path would flatten that).
"""

from __future__ import annotations

import re

from pipeline.models import SkyPosition
from web.sky import sky_chart_svg, sky_field_svg

_POINTS = [(10.0, 20.0), (300.0, -45.0), (10.0, 20.0), (123.4, 0.0), (359.9, 89.0)]
_TARGET = SkyPosition(
    ra_deg=10.0, dec_deg=20.0, constellation="Aries", constellation_abbr="Ari"
)
_OTHER = SkyPosition(
    ra_deg=123.4, dec_deg=0.0, constellation="Hydra", constellation_abbr="Hya"
)


def test_field_keeps_one_rect_per_star() -> None:
    """One element each, so overlapping dots still build up. No merging into a single path."""
    field = sky_field_svg(_POINTS)
    assert field.count("<rect") == len(_POINTS)
    assert "<path" not in field


def test_field_is_identical_whoever_is_being_viewed() -> None:
    """The whole point of sharing: one file serves every page, so it cannot depend on a target.

    That is also why the target keeps its own dot — see sky_chart_svg.
    """
    assert sky_field_svg(_POINTS) == sky_field_svg(_POINTS)
    assert sky_field_svg(_POINTS).count("<rect") == len(_POINTS)


def test_field_is_a_standalone_document() -> None:
    """Referenced through <image>, so page CSS cannot reach it: it carries its own namespace
    and its own fill."""
    field = sky_field_svg(_POINTS)
    assert 'xmlns="http://www.w3.org/2000/svg"' in field
    assert "<style>" in field and "rgba(205,216,242,.34)" in field


def test_chart_with_a_field_url_references_it_instead_of_inlining_dots() -> None:
    svg = sky_chart_svg(_TARGET, _POINTS, field_url="/sky-field.123.svg")
    assert '<image href="/sky-field.123.svg"' in svg
    assert 'class="skydot"' not in svg
    # Still the target's own chart: crosshair, marker and constellation label are per page.
    assert 'class="skymark"' in svg and "ARIES" in svg


def test_chart_without_a_field_url_still_inlines_and_skips_the_target() -> None:
    """The inline path is the fallback and keeps its original behaviour."""
    svg = sky_chart_svg(_TARGET, _POINTS)
    assert "<image" not in svg
    # Two of the five points are the target's own coordinates; both are skipped.
    assert len(re.findall(r'class="skydot"', svg)) == len(_POINTS) - 2


def test_compact_field_uses_the_compact_geometry() -> None:
    wide, compact = sky_field_svg(_POINTS), sky_field_svg(_POINTS, compact=True)
    assert 'viewBox="0 0 720 300"' in wide
    assert 'viewBox="0 0 400 260"' in compact
    assert wide != compact


def test_chart_geometry_matches_the_field_it_references() -> None:
    """The <image> must cover the chart's own coordinate box, or the dots land off the grid."""
    for compact, box in ((False, (720, 300)), (True, (400, 260))):
        svg = sky_chart_svg(_OTHER, _POINTS, compact=compact, field_url="/f.svg")
        assert f'width="{box[0]}" height="{box[1]}"' in svg
        assert f'viewBox="0 0 {box[0]} {box[1]}"' in svg
