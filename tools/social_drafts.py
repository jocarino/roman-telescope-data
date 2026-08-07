"""Auto-draft, manual send: the daily-planet post queue for Bluesky / Mastodon.

The posting plan (see the marketing notes, doc 11) runs on one rule: scheduling may be
automated, AUTHORSHIP may not. A templated caption is the thing the astronomy feeds'
moderators have seen a thousand times, and the physics sentence is the entire value of the
post. So this tool produces DRAFTS — the image, the alt text, the link, and a physics
sentence read back from the planet's own record (pipeline.explain) — and a human rewrites
the sentence in their own voice before anything is posted. If the queue empties, post
nothing rather than repeating.

For each planet id it writes  <out>/<NN>-<id>/
    post.png     1200x1200: the rendered disc, name, hex, a spectrum trace, and the
                 honesty stamp (MODELLED / MEASURED / MODEL-ONLY) burned into the pixels —
                 the editorial position travels inside the image, and the visible spectrum
                 trace is what marks it as computed physics rather than generative slop.
    caption.txt  a draft caption with the deep link (UTM-tagged) and hashtags, plus the
                 character count against Bluesky's 300.
    alt.txt      filled from the fixed template: names the colour in words, states the
                 colour is computed. Never "image of a planet" — a blind reader should get
                 the finding, and the finding IS the colour.
plus a QUEUE.md index. Nothing here posts anything, on purpose.

Usage (needs the repo venv for Pillow/numpy — data/planets.json via scripts/fetch_data.py):

    uv run python tools/social_drafts.py hd-189733-b kepler-7-b ...
    uv run python tools/social_drafts.py --site-url https://example.com --out social-queue ...

Without --site-url ($SITE_BASE_URL), links are written with a <SITE_URL> placeholder so a
draft can never ship with a broken link by accident — it fails visibly instead.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

from pipeline.colour.family import colour_family
from pipeline.explain import physics_note
from pipeline.palette.derive import derive_palette_from_hex
from web.og import (
    ACCENT,
    BG,
    FG,
    FG_DIM,
    FG_FAINT,
    GRID,
    CardSpec,
    _disc,
    _ellipsize,
    _fit_font,
    _font,
    _hex_to_rgb,
    _text_w,
)

SIZE = 1200  # square: the format both platforms crop least

# How each colour family reads as a plain word in the alt text.
_FAMILY_WORDS = {
    "white": "near-white",
    "dark": "near-black",
}


def _stamp_for(rec: dict) -> str:
    """Same honesty grammar as the OG share cards."""
    if rec.get("provenance") == "measured-albedo":
        return "FROM A MEASURED SPECTRUM · STILL A RENDER"
    if not rec.get("is_light_isolable", True):
        return "MODEL-ONLY · LIGHT NEVER ISOLABLE"
    return "MODELLED · NOT PHOTOGRAPHED"


def _honesty_clause(rec: dict) -> str:
    """The caption's ~40-character honesty allocation, per the plan's budget."""
    if rec.get("provenance") == "measured-albedo":
        return "Colour from a measured spectrum."
    if not rec.get("is_light_isolable", True):
        return "Model-only: no light from this planet can ever be isolated."
    return "Modelled, not photographed."


def post_image(rec: dict) -> Image.Image:
    """The daily-post square. Reuses the OG card's disc renderer so the post and the site
    show the same world; palette re-derived from the base hex exactly as the site build
    does (released ramps are non-monotonic by design — see web/build.py)."""
    tc = rec["true_colour"]
    ramp = tuple(s.hex for s in derive_palette_from_hex(tc["hex"])[:5])
    spec = CardSpec(
        name=rec["name"],
        palette=ramp,
        base_hex=tc["hex"],
        subtitle="",
        facts=(),
        radius_r_earth=rec["params"].get("radius_r_earth"),
        cloud_state=rec["params"].get("assumed_cloud_state", ""),
        luminance_y=tc["luminance_y"],
        caption="",
    )
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    for x in range(0, SIZE + 1, 60):
        draw.line([(x, 0), (x, SIZE)], fill=GRID)
    for y in range(0, SIZE + 1, 60):
        draw.line([(0, y), (SIZE, y)], fill=GRID)
    draw.rectangle([0, 0, SIZE, 4], fill=ACCENT)

    draw.text((72, 60), "EXOPLANET PALETTE", font=_font(False, 24), fill=ACCENT)
    name_font = _fit_font(draw, rec["name"], SIZE - 144, (72, 64, 56, 48, 40, 32))
    draw.text((72, 108), _ellipsize(draw, rec["name"], name_font, SIZE - 144),
              font=name_font, fill=FG)

    r = 330
    disc = _disc(spec, r * 2)
    img.paste(disc, (SIZE // 2 - r, 560 - r), disc)

    # Bottom rail: the hex chip (left) and the spectrum trace (right) — the trace is the
    # visible evidence this is computed physics, which the astronomy feeds' no-AI-slop rule
    # effectively requires the image itself to argue.
    hex_font = _font(True, 40)
    chip = 40
    hy = SIZE - 210
    draw.rectangle([72, hy, 72 + chip, hy + chip], fill=_hex_to_rgb(tc["hex"]))
    draw.text((72 + chip + 20, hy - 2), tc["hex"].upper(), font=hex_font, fill=FG)

    values = (rec.get("spectrum") or {}).get("values") or []
    if values:
        bx, bw, bh = SIZE - 72 - 420, 420, 110
        by = hy - 34
        mx = max(values) or 1.0
        pts = [
            (bx + i * bw / (len(values) - 1), by + bh - (v / mx) * bh)
            for i, v in enumerate(values)
        ]
        draw.line(pts, fill=ACCENT, width=3)
        draw.text((bx, by + bh + 10), "REFLECTED LIGHT 380–780 NM · MODEL",
                  font=_font(False, 16), fill=FG_FAINT)

    stamp = _stamp_for(rec)
    sfont = _font(False, 24)
    draw.text((SIZE // 2 - _text_w(draw, stamp, sfont) // 2, SIZE - 64), stamp,
              font=sfont, fill=FG_DIM)
    return img


def alt_text(rec: dict) -> str:
    tc = rec["true_colour"]
    fam = colour_family(tuple(tc["srgb"]))
    word = _FAMILY_WORDS.get(fam, fam)
    return (
        f"A rendered disc of {rec['name']}, coloured {word} ({tc['hex']}), on a dark "
        "background, with the planet's reflected-light spectrum drawn as a small line "
        "chart. The colour is computed from a model albedo spectrum, not photographed."
    )


def caption_draft(rec: dict, site_url: str, campaign: str = "potd") -> str:
    base = site_url.rstrip("/") if site_url else "<SITE_URL>"
    url = f"{base}/planet/{rec['id']}?utm_source=bluesky&utm_medium=social&utm_campaign={campaign}"
    note = physics_note(rec)
    physics = note.one_line() if note else "(no spectrum on record — write the hook by hand)"
    body = f"{rec['name']}: {physics} {_honesty_clause(rec)}\n{url} 🔭 #exoplanet #astronomy"
    warnings = ""
    if note and note.contradiction:
        warnings = f"\n⚠ CHECK BEFORE POSTING: {note.contradiction}.\n"
    return (
        "DRAFT: rewrite the physics sentence in your own voice before posting; a templated\n"
        "caption is what kills the account. Facts behind it, checkable on the planet page:\n"
        + "\n".join(f"  · {line}" for line in (note.lines() if note else []))
        + warnings
        + "\n---\n"
        + body
        + f"\n---\nBluesky budget: {len(body)}/300 characters (as drafted, link and tags "
        "included).\nMastodon: same text, swap utm_source=mastodon, add #Astrodon — 2-3 of "
        "the week's best, not all of them.\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(prog="social_drafts")
    ap.add_argument("ids", nargs="+", help="planet ids (the site URL slug, e.g. hd-189733-b)")
    ap.add_argument("--planets", type=Path, default=Path("data/planets.json"))
    ap.add_argument("--out", type=Path, default=Path("social-queue"))
    ap.add_argument(
        "--site-url",
        default=os.environ.get("SITE_BASE_URL", ""),
        help="Deep-link origin. Defaults to $SITE_BASE_URL; without it, links carry a "
        "<SITE_URL> placeholder that fails visibly rather than a broken guess.",
    )
    ap.add_argument(
        "--campaign", default="potd",
        help="utm_campaign tag (potd for the daily post; roman for two-disc comparisons).",
    )
    args = ap.parse_args()

    by_id = {r["id"]: r for r in json.loads(args.planets.read_text())["planets"]}
    missing = [i for i in args.ids if i not in by_id]
    if missing:
        raise SystemExit(f"not in {args.planets}: {', '.join(missing)}")

    args.out.mkdir(parents=True, exist_ok=True)
    index: list[str] = []
    for n, pid in enumerate(args.ids, 1):
        rec = by_id[pid]
        d = args.out / f"{n:02d}-{pid}"
        d.mkdir(exist_ok=True)
        post_image(rec).save(d / "post.png", optimize=True)
        (d / "caption.txt").write_text(caption_draft(rec, args.site_url, args.campaign))
        (d / "alt.txt").write_text(alt_text(rec) + "\n")
        index.append(f"- **{n:02d} {rec['name']}** (`{d.name}/`): {_honesty_clause(rec)}")
        print(f"  {d}/  (post.png, caption.txt, alt.txt)")

    (args.out / "QUEUE.md").write_text(
        "# Post queue: drafts, not posts\n\n"
        "Rewrite every caption in your own voice, then post by hand (or via your own\n"
        "send step). One per day is the ceiling; if the queue empties, post nothing.\n\n"
        + "\n".join(index)
        + "\n"
    )
    print(f"Queue of {len(args.ids)} drafts -> {args.out}/QUEUE.md")


if __name__ == "__main__":
    main()
