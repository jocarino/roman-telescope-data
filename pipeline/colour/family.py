"""Classify a base sRGB colour into a human colour family, for gallery colour filtering.

Hue + lightness buckets, tuned to the colours reflected-light planets actually take (cobalt
blues, teal Neptunes, cream/gold Jupiters, dark hot Jupiters). Families with no members simply
never appear as a filter chip. Pure stdlib — no colour library needed for a coarse bucket."""

from __future__ import annotations

# Canonical chip order; only families that have members are shown.
FAMILY_ORDER = [
    "blue", "teal", "green", "gold", "orange", "red", "pink", "brown", "grey", "white", "dark",
]


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    lightness = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, lightness
    d = mx - mn
    sat = d / (2.0 - mx - mn) if lightness > 0.5 else d / (mx + mn)
    if mx == rf:
        h = (gf - bf) / d + (6.0 if gf < bf else 0.0)
    elif mx == gf:
        h = (bf - rf) / d + 2.0
    else:
        h = (rf - gf) / d + 4.0
    return h * 60.0, sat, lightness


def colour_family(rgb: tuple[int, int, int]) -> str:
    """Map an sRGB triple (0-255) to a family name from FAMILY_ORDER."""
    h, s, lightness = _rgb_to_hsl(*rgb)
    if lightness > 0.9:
        return "white"
    if lightness < 0.1:
        return "dark"
    # Pale, weakly-saturated colours (cream Jupiters, grey-blues) read as white/grey, not a hue.
    if s < 0.18:
        if lightness > 0.72:
            return "white"
        if lightness < 0.2:
            return "dark"
        return "grey"
    if h < 15 or h >= 345:
        return "red"
    if h < 45:
        return "brown" if lightness < 0.4 else "orange"
    if h < 70:
        return "gold"
    if h < 165:
        return "green"
    if h < 200:
        return "teal"
    if h < 290:  # blue through violet fold into blue (violet is rare; keeps chips tidy)
        return "blue"
    return "pink"
