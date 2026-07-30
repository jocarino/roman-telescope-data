"""Per-page metadata: what a link to this site says when it travels.

Every page used to ship one shared `<meta name="description">` and nothing else, so all ~5.8k
planet pages were indistinguishable to a search engine and unfurled as a bare URL in Slack,
iMessage, Discord and X. This module builds the per-page title / description / Open Graph /
Twitter set, plus sitemap.xml and robots.txt.

Descriptions are generated from the record, never hand-written, so they cannot go stale
against the data. They keep the site's honesty rule: the colour is always described as
modelled, and a microlensing planet says outright that its light is never isolable.

Absolute URLs: Open Graph wants them, and several unfurlers refuse relative ones outright.
The canonical origin is not knowable from the repo, so it is a build input (`--base-url` /
`SITE_BASE_URL`). With no base URL configured the tags still emit, using root-relative paths
-- correct for most unfurlers, and the sitemap is skipped rather than published wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from pipeline.classify import planet_type
from pipeline.colour.family import colour_family
from pipeline.models import PlanetRecord

SITE_NAME = "Exoplanet Palette"
TAGLINE = "The colour scheme of every known exoplanet, derived from physics."

_LY_PER_PC = 3.26156

# Colour families as they read in a sentence. The bucket names are filter chips; two of them
# ("white", "dark") are lightness buckets rather than hues and need hedging so the sentence
# doesn't claim a hue the planet hasn't got.
_FAMILY_PHRASE = {
    "teal": "teal",
    "azure": "azure",
    "blue": "blue",
    "periwinkle": "periwinkle",
    "green": "green",
    "gold": "gold",
    "orange": "orange",
    "red": "red",
    "pink": "pink",
    "violet": "violet",
    "brown": "brown",
    "grey": "grey",
    "white": "near-white",
    "dark": "near-black",
}


@dataclass(frozen=True)
class PageMeta:
    """One page's share identity. `image` and `url` are page-relative; `absolute()` on the
    Site turns them into the absolute URLs Open Graph asks for."""

    title: str  # the <title> and og:title
    description: str
    path: str  # site-root-relative, e.g. "/planet/hd-189733-b.html"
    image: str | None = None  # site-root-relative PNG path
    image_alt: str | None = None
    noindex: bool = False
    in_sitemap: bool = True
    # Sitemap hints. Planet pages are the long tail; the hubs change every build.
    priority: str = "0.5"
    changefreq: str = "monthly"


@dataclass(frozen=True)
class Site:
    """Build-time site identity. `base_url` is the canonical origin, without a trailing slash."""

    base_url: str = ""
    default_image: str = "/og/default.png"
    pages: list[PageMeta] = field(default_factory=list)
    # Visitor analytics. `posthog_key` is a PostHog *project* token (the public, write-only
    # `phc_...` one that ships in the page, not a personal API key). Empty is the default and
    # means no analytics code is emitted at all — which is what every local preview and every
    # worktree's `exohub serve` should be, since a browsing session on :8800 otherwise lands
    # in the same dashboard as a real visitor. Set it only for the deploy build.
    posthog_key: str = ""
    posthog_api_host: str = "https://eu.i.posthog.com"
    posthog_assets_host: str = "https://eu-assets.i.posthog.com"

    def absolute(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}" if self.base_url else path


def _light_years(distance_pc: float | None) -> int | None:
    if not distance_pc or distance_pc <= 0:
        return None
    return int(round(distance_pc * _LY_PER_PC))


# How each size class reads mid-sentence. Written out rather than derived from TYPE_LABELS by
# lowercasing, because three of the six labels carry a proper noun: naive lowercasing gives
# "a hot jupiter" and "a super-earth".
_TYPE_PHRASE = {
    "rocky": "a rocky world",
    "super-earth": "a super-Earth",
    "neptune": "a Neptune-like world",
    "gas-giant": "a gas giant",
    "hot-jupiter": "a hot Jupiter",
    "unknown": "a planet",
}


def _type_phrase(rec: PlanetRecord) -> str:
    key = planet_type(
        rec.params.radius_r_earth, rec.params.mass_m_earth, rec.params.equilibrium_temp_k
    )
    return _TYPE_PHRASE.get(key, "a planet")


def planet_description(rec: PlanetRecord) -> str:
    """One honest sentence-pair, ~150-200 chars: what it is, where it is, what colour we
    model it as, and the fact that the colour is modelled.

    It opens with the planet's own name, and not only because that reads better. Type + host
    + distance + colour is NOT unique: all seven TRAPPIST-1 planets are rocky worlds 41
    light-years away in the same colour family, and shipped the same sentence -- which is the
    duplicate-description problem this module exists to fix, one level down.
    """
    colour = rec.true_colour
    family = _FAMILY_PHRASE.get(colour_family(tuple(colour.srgb)), "distinctive")
    ly = _light_years(rec.params.distance_pc)
    # Solar-system anchors orbit "Sun" in the archive's naming; in prose it takes the article.
    host = "the Sun" if rec.host_star.name == "Sun" else rec.host_star.name
    where = f"orbiting {host}"
    if ly:
        where += f", {ly:,} light-year{'s' if ly != 1 else ''} away"

    lead = f"{rec.name} is {_type_phrase(rec)} {where}."
    colour_bit = f" Modelled reflected-light colour: {family}, {colour.hex}."
    if not rec.is_light_isolable:
        tail = (
            " Found by microlensing — no telescope can ever isolate its light, so this"
            " palette is model-only."
        )
    else:
        tail = " Derived from physics, not photographed."
    return lead + colour_bit + tail


def planet_meta(rec: PlanetRecord) -> PageMeta:
    return PageMeta(
        title=f"{rec.name} · {SITE_NAME}",
        description=planet_description(rec),
        path=f"/planet/{rec.id}.html",
        image=f"/og/{rec.id}.png",
        image_alt=(
            f"{rec.name} rendered in its modelled colour {rec.true_colour.hex}, "
            f"beside its five-stop palette"
        ),
        priority="0.6",
    )


def static_pages(n_planets: int) -> list[PageMeta]:
    """The hub pages. Descriptions say what you can DO there, not what the site is."""
    n = f"{n_planets:,}"
    return [
        PageMeta(
            title=SITE_NAME,
            description=(
                f"The colour of {n} real exoplanets, computed from their reflected-light "
                "spectra. Search, filter and sort the whole catalogue by colour, size and "
                "temperature — and see how much of each colour survives Roman's four filters."
            ),
            path="/",
            priority="1.0",
            changefreq="weekly",
        ),
        PageMeta(
            title=f"How we get the colours · {SITE_NAME}",
            description=(
                "Albedo spectrum times host-star spectrum, convolved with the CIE 1931 "
                "colour-matching functions, converted to sRGB. Every assumption stated: "
                "cloud state, metallicity, phase angle."
            ),
            path="/how.html",
            priority="0.8",
        ),
        PageMeta(
            title=f"Compare planets · {SITE_NAME}",
            description=(
                "Put any two exoplanets side by side: colour, palette, spectrum, host star "
                "and the orbital numbers that drive them."
            ),
            path="/compare.html",
            priority="0.7",
        ),
        PageMeta(
            title=f"Colour census · {SITE_NAME}",
            description=(
                f"What colour is the galaxy? The whole modelled catalogue of {n} planets as "
                "one dataset — which colours are common, which are rare, and why."
            ),
            path="/census.html",
            priority="0.7",
        ),
        PageMeta(
            title=f"Your sky tonight · {SITE_NAME}",
            description=(
                "Which exoplanet host stars are above your horizon right now, where to look, "
                "and what equipment you would need to see each one."
            ),
            path="/sky.html",
            priority="0.7",
        ),
        PageMeta(
            title=f"Guided tours · {SITE_NAME}",
            description=(
                "Curated walks through the catalogue: the darkest worlds, the bluest, the "
                "ones you could almost see from your garden."
            ),
            path="/tours/",
            priority="0.7",
        ),
        PageMeta(
            title=f"Glossary · {SITE_NAME}",
            description=(
                "Every piece of jargon on this site in plain English — albedo, equilibrium "
                "temperature, metallicity, phase angle, coronagraph."
            ),
            path="/glossary.html",
            priority="0.4",
        ),
    ]


def tour_meta(tour_id: str, title: str, blurb: str, n_stops: int) -> PageMeta:
    return PageMeta(
        title=f"{title} · Guided tour · {SITE_NAME}",
        description=f"{blurb} A guided tour of {n_stops} planets, ordered and explained."[:300],
        path=f"/tours/{tour_id}.html",
        priority="0.6",
    )


def roman_meta() -> PageMeta:
    """The target board. Not in static_pages() because the page is conditional — it is only
    built when the curated board file resolves — and a sitemap must not name a 404."""
    return PageMeta(
        title=f"The Roman target board · {SITE_NAME}",
        description=(
            "The shortlist of exoplanets the Roman Coronagraph could measure in colour "
            "rather than model: predicted colours now, empty slots waiting for real data, "
            "and a clock counting down to launch."
        ),
        path="/roman.html",
        priority="0.8",
        changefreq="weekly",
    )


def not_found_meta() -> PageMeta:
    return PageMeta(
        title=f"404 · off the chart · {SITE_NAME}",
        description="No such page. Here is a random world instead.",
        path="/404.html",
        noindex=True,
        in_sitemap=False,
    )


# ── sitemap / robots ────────────────────────────────────────────────────────────────────


def sitemap_xml(site: Site, lastmod: str | None = None) -> str:
    """One urlset for the whole site. ~5.8k URLs is an order of magnitude inside the 50,000
    URL / 50 MB limit, so it stays a single uncompressed file with no index."""
    rows = []
    for page in site.pages:
        if not page.in_sitemap or page.noindex:
            continue
        row = [f"    <loc>{escape(site.absolute(page.path))}</loc>"]
        if lastmod:
            row.append(f"    <lastmod>{escape(lastmod)}</lastmod>")
        row.append(f"    <changefreq>{page.changefreq}</changefreq>")
        row.append(f"    <priority>{page.priority}</priority>")
        rows.append("  <url>\n" + "\n".join(row) + "\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def robots_txt(site: Site) -> str:
    lines = ["User-agent: *", "Allow: /", ""]
    if site.base_url:
        lines.append(f"Sitemap: {site.absolute('/sitemap.xml')}")
        lines.append("")
    return "\n".join(lines)
