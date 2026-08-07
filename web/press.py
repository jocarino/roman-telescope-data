"""Press assets: the flagship images /press offers for download, built at site-build time.

Three images, chosen so a writer on deadline never has to screenshot the site — and so every
one of them is built from RENDERED SWATCHES ONLY. Planet pages contain third-party imagery
(ESA/Webb frames, NASA/JPL photographs) with its own terms; these three contain nothing but
our own computed colours, so the CC BY 4.0 grant on them is a licence we actually hold.

  * the wall — every planet's swatch on one sheet, hue-sorted. The money shot.
  * the Roman comparison — one planet's full-spectrum colour beside its three-band
    reconstruction. The signature feature as a single still.
  * the Band 1 still — the same planet as the one measurement Roman's coronagraph
    formally guarantees: a single 575 nm brightness, which carries no colour at all.

Honesty travels inside the file, not only in the caption a sub-editor can cut: every asset
has "COMPUTED COLOUR · NOT A PHOTOGRAPH" burned into its margin, and ships with an embedded
sRGB profile (a colour project whose press images get colour-shifted downstream has failed at
its own subject) plus PNG text metadata carrying the credit, licence and description — so the
attribution survives the picture being pulled off the page and re-shared with no caption.

Each asset is written as a 3000 px master and a 1200 px web copy, and the lot is bundled as
press.zip with a CREDITS.txt. The generator returns the asset table so the /press template
renders captions, alt text and dimensions from the same objects that made the files —
the page and the pixels cannot disagree.
"""

from __future__ import annotations

import colorsys
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw

from pipeline.config import ROMAN_CGI
from pipeline.models import PlanetRecord
from pipeline.palette.derive import derive_palette_from_hex
from pipeline.rights import RIGHTS
from web.og import ACCENT, BG, FG, FG_DIM, FG_FAINT, GRID, CardSpec, _disc, _font, _hex_to_rgb

# The margin line burned into every asset. The one phrase the whole project rests on; it is
# the only part of the image that survives a crop, a screenshot, or a repost with no caption.
STAMP = "COMPUTED COLOUR · NOT A PHOTOGRAPH"

# Master and web widths. 3000 px ≈ 300 dpi at print column width; 1200 px is what most web
# desks actually run.
MASTER_W = 3000
WEB_W = 1200

# The comparison exemplar must come from the CGI shortlist itself — using a planet Roman
# could never point at is exactly the error the marketing review caught. 47 UMa b is the
# most repeatedly-named tech-demo candidate; the others are fallbacks in shortlist order.
_EXEMPLAR_IDS = ("47-uma-b", "47-uma-c", "ups-and-d")

_SRGB_PROFILE = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


@dataclass(frozen=True)
class PressAsset:
    """One downloadable image, as both the file on disk and the row on /press."""

    slug: str  # filename stem: press-kit/<slug>.png + press-kit/<slug>-1200.png
    title: str  # plain-language name on the page
    width: int
    height: int
    caption: str  # ready to paste under the image, credit line included
    alt: str  # one sentence, supplied per asset because curators paste it verbatim

    @property
    def master(self) -> str:
        return f"/press-kit/{self.slug}.png"

    @property
    def web(self) -> str:
        return f"/press-kit/{self.slug}-1200.png"


def _png_bytes(img: Image.Image, asset: PressAsset) -> bytes:
    """Encode with the sRGB profile and the credit riding inside the file (PNG tEXt)."""
    from PIL.PngImagePlugin import PngInfo

    info = PngInfo()
    info.add_text("Title", f"{asset.title} — Exoplanet Palette")
    info.add_text("Author", RIGHTS.attribution)
    info.add_text("Copyright", f"{RIGHTS.holder} · {RIGHTS.derived_licence}")
    info.add_text("Description", asset.caption)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, pnginfo=info, icc_profile=_SRGB_PROFILE)
    return buf.getvalue()


def _stamp(draw: ImageDraw.ImageDraw, w: int, h: int, text: str = STAMP) -> None:
    """The honesty line, bottom-right, in the safe margin."""
    font = _font(False, 32)
    tw = int(draw.textbbox((0, 0), text, font=font)[2])
    draw.text((w - tw - 48, h - 72), text, font=font, fill=FG_FAINT)


def _hue_key(hexcode: str) -> tuple:
    """Sort key for the wall: saturated colours sweep the hue wheel, near-neutrals gather at
    the end ordered by brightness — a grey column in the middle of the rainbow reads as a
    printing error, at the edge it reads as the truth (many worlds are dark)."""
    h = hexcode.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    if sat < 0.12:
        return (1, 0.0, light)
    return (0, hue, light)


def _wall(records: list[PlanetRecord]) -> Image.Image:
    """Every swatch on one sheet, hue-sorted, with a title strip that states the honesty.

    Exoplanets only: the five solar-system calibration anchors are excluded, because the
    strip says "known exoplanets" and Jupiter is not one. Counts on this image get
    fact-checked by exactly the people we most want as allies.
    """
    hexes = sorted(
        (r.true_colour.hex for r in records if r.provenance != "measured-albedo"),
        key=_hue_key,
    )
    n = len(hexes)
    cols = max(1, int(n**0.5 + 0.999))
    rows = (n + cols - 1) // cols
    cell = MASTER_W // cols
    strip = 200
    w, h = cell * cols, cell * rows + strip
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    for i, hexcode in enumerate(hexes):
        x, y = (i % cols) * cell, (i // cols) * cell
        draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=_hex_to_rgb(hexcode))
    # The strip: accent rule, title, and the stamp — same grammar as the share cards.
    draw.rectangle([0, cell * rows, w, cell * rows + 4], fill=ACCENT)
    draw.text((48, cell * rows + 60), "EXOPLANET PALETTE", font=_font(False, 40), fill=FG)
    draw.text(
        (48 + 620, cell * rows + 66),
        f"the computed colour of {n:,} known exoplanets",
        font=_font(False, 32),
        fill=FG_DIM,
    )
    _stamp(draw, w, h)
    return img


def _spec_for(rec: PlanetRecord, palette: tuple[str, ...], base_hex: str,
              luminance: float) -> CardSpec:
    """A CardSpec that renders `rec`'s disc in an arbitrary palette — the true colour, the
    Roman reconstruction, or the single-band grey — without touching the record."""
    return CardSpec(
        name=rec.name,
        palette=palette,
        base_hex=base_hex,
        subtitle="",
        facts=(),
        radius_r_earth=rec.params.radius_r_earth,
        cloud_state=rec.params.assumed_cloud_state,
        luminance_y=luminance,
        caption="",
    )


def _labelled_disc(img: Image.Image, spec: CardSpec, cx: int, cy: int, r: int,
                   label: str, sub: str) -> None:
    draw = ImageDraw.Draw(img)
    disc = _disc(spec, r * 2)
    img.paste(disc, (cx - r, cy - r), disc)
    for text, font, fill, dy in (
        (label, _font(True, 44), FG, 90),
        (sub, _font(False, 30), FG_DIM, 160),
    ):
        tw = int(draw.textbbox((0, 0), text, font=font)[2])
        draw.text((cx - tw // 2, cy + r + dy), text, font=font, fill=fill)


def _graticule(img: Image.Image) -> ImageDraw.ImageDraw:
    draw = ImageDraw.Draw(img)
    for x in range(0, img.width + 1, 150):
        draw.line([(x, 0), (x, img.height)], fill=GRID)
    for y in range(0, img.height + 1, 150):
        draw.line([(0, y), (img.width, y)], fill=GRID)
    draw.rectangle([0, 0, img.width, 6], fill=ACCENT)
    return draw


def _comparison(rec: PlanetRecord) -> Image.Image:
    """Two discs: the full-spectrum colour beside the three-band reconstruction."""
    w, h = MASTER_W, 1688
    img = Image.new("RGB", (w, h), BG)
    draw = _graticule(img)
    view = rec.instrument_views[0]
    n_bands = len(ROMAN_CGI.bands)

    draw.text((96, 96), "EXOPLANET PALETTE", font=_font(False, 36), fill=ACCENT)
    draw.text((96, 168), rec.name, font=_font(True, 88), fill=FG)

    r = 480
    tc = rec.true_colour
    _labelled_disc(
        img,
        _spec_for(rec, tuple(s.hex for s in tc.palette[:5]), tc.hex, tc.luminance_y),
        870, 760, r,
        "FULL SPECTRUM", f"modelled 380–780 nm · {tc.hex.upper()}",
    )
    rc = view.colour
    _labelled_disc(
        img,
        _spec_for(rec, tuple(s.hex for s in rc.palette[:5]), rc.hex, rc.luminance_y),
        w - 870, 760, r,
        f"AS ROMAN WOULD SEE IT · {n_bands} BANDS",
        " · ".join(f"{b.center_nm:.0f} nm" for b in ROMAN_CGI.bands) + f" · {rc.hex.upper()}",
    )
    _stamp(draw, w, h, "BOTH MODELLED · NEITHER IS A PHOTOGRAPH")
    return img


def _band1_only(rec: PlanetRecord) -> Image.Image:
    """One disc in neutral grey: what the single guaranteed Roman measurement leaves.

    Band 1 photometry is one number — a brightness through the 575 nm filter. One number has
    no hue, so the honest rendering is the planet's Roman-view brightness with the colour
    removed. This is the image that makes the information budget visual.
    """
    w, h = MASTER_W, 1688
    img = Image.new("RGB", (w, h), BG)
    draw = _graticule(img)
    view = rec.instrument_views[0]

    # The Roman-view luminance, gamma-encoded to the grey a screen shows for it.
    v = max(0, min(255, round(255 * view.colour.luminance_y ** (1 / 2.2))))
    grey = f"#{v:02x}{v:02x}{v:02x}"
    ramp = tuple(s.hex for s in derive_palette_from_hex(grey)[:5])

    b1 = ROMAN_CGI.bands[0]
    draw.text((96, 96), "EXOPLANET PALETTE", font=_font(False, 36), fill=ACCENT)
    draw.text((96, 168), rec.name, font=_font(True, 88), fill=FG)
    _labelled_disc(
        img,
        _spec_for(rec, ramp, grey, view.colour.luminance_y),
        w // 2, 760, 480,
        f"THE GUARANTEED MEASUREMENT: BAND 1 · {b1.center_nm:.0f} nm",
        "one brightness, no colour — everything else is best-effort",
    )
    _stamp(draw, w, h, "MODELLED · NOT A PHOTOGRAPH")
    return img


def _credit_txt(assets: list[PressAsset]) -> str:
    lines = [
        "Exoplanet Palette — press assets",
        "",
        f"Licence: CC BY 4.0 ({RIGHTS.derived_licence})",
        f"Credit, online: {RIGHTS.attribution}",
        "Credit, print: Exoplanet Palette, CC BY 4.0",
        "Crops and colour-space conversions are fine and need no separate note.",
        "",
        "Every image here is built from this site's own computed colours only — no",
        "third-party imagery — so the licence above is the whole story. All colours are",
        "computed from physical models, never photographed. Please describe them as",
        '"computed colours".',
        "",
    ]
    for a in assets:
        lines += [f"{a.slug}.png ({a.width}x{a.height}) — {a.title}", f"  Caption: {a.caption}", ""]
    return "\n".join(lines)


def write_press_assets(records: list[PlanetRecord], out: Path) -> list[PressAsset]:
    """Render the three flagship images (master + 1200 px web copy each), bundle press.zip,
    and return the asset table for the /press template. Call after palettes are re-derived —
    the discs read the same ramps the site shows."""
    exemplar = next(
        (r for pid in _EXEMPLAR_IDS for r in records if r.id == pid),
        max(records, key=lambda r: len(r.instrument_views)),
    )
    # Exoplanets, not records: the catalogue also carries the five solar-system anchors, and
    # a press caption that counts Jupiter among "known exoplanets" is a correction waiting
    # to be published.
    n = sum(1 for r in records if r.provenance != "measured-albedo")
    n_bands = len(ROMAN_CGI.bands)
    credit = f"{RIGHTS.attribution}."

    images = {
        "colour-wall": _wall(records),
        "roman-comparison": _comparison(exemplar),
        "band1-only": _band1_only(exemplar),
    }
    titles_captions_alts = {
        "colour-wall": (
            "The wall: every exoplanet's computed colour on one sheet",
            f"The computed colour of {n:,} known exoplanets, hue-sorted, one square per "
            "planet. Not photographs — no exoplanet has ever been photographed in visible "
            f"colour. {credit}",
            f"A dense grid of {n:,} coloured squares sweeping from blue through green, gold "
            "and red to a block of dark near-neutrals, one square per exoplanet.",
        ),
        "roman-comparison": (
            "The Roman comparison: full spectrum beside the three-band reconstruction",
            f"Computed colour of {exemplar.name} from its full modelled spectrum, beside the "
            f"same planet rebuilt from the Roman Coronagraph's {n_bands} visible bands. Both "
            f"are models — neither is a photograph. {credit}",
            f"Two rendered discs of {exemplar.name} side by side, labelled full spectrum and "
            "as Roman would see it; the two colours are close but not identical.",
        ),
        "band1-only": (
            "The Band 1 still: the one measurement Roman guarantees",
            f"{exemplar.name} as the Roman Coronagraph's only guaranteed measurement would "
            "record it: one brightness through the 575 nm band — a grey, because one number "
            f"carries no colour. A model, not a photograph. {credit}",
            f"A single grey rendered disc of {exemplar.name} on a dark background, labelled "
            "as Band 1 at 575 nanometres: one brightness, no colour.",
        ),
    }

    press_dir = out / "press-kit"
    press_dir.mkdir(parents=True, exist_ok=True)
    assets: list[PressAsset] = []
    files: list[tuple[str, bytes]] = []
    for slug, img in images.items():
        title, caption, alt = titles_captions_alts[slug]
        asset = PressAsset(
            slug=slug, title=title, width=img.width, height=img.height,
            caption=caption, alt=alt,
        )
        assets.append(asset)
        master = _png_bytes(img, asset)
        web_h = round(img.height * WEB_W / img.width)
        web = _png_bytes(img.resize((WEB_W, web_h), Image.LANCZOS), asset)
        (press_dir / f"{slug}.png").write_bytes(master)
        (press_dir / f"{slug}-1200.png").write_bytes(web)
        files += [(f"{slug}.png", master), (f"{slug}-1200.png", web)]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:  # PNGs don't re-compress
        z.writestr("CREDITS.txt", _credit_txt(assets))
        for name, data in files:
            z.writestr(name, data)
    (press_dir / "press.zip").write_bytes(buf.getvalue())
    return assets
