# Review — 07 Wallpapers

*Reviewed by a product designer who has also spent ten years posting in the wallpaper subs and watching other people's posts get removed for reasons they never understood.*

## Verdict

**Right instinct, wrong artifact** — the delivery plan (control + page, no watermark, curate hard) is basically correct and survives the rules, but the thing it proposes shipping is a planet disc on black, which is the single most replaceable image on the internet; the fix is to make the *spectrum* the wallpaper, not the planet.

## The specs, corrected

**"Three sizes only" is right about compositions and wrong about exports.** Sizes are a loop in a script and cost nothing; *compositions* cost design time. Cap compositions at three — portrait, 16:9 landscape, 21:9 ultrawide — and export as many exact resolutions from each as the subs demand. The claim "devices scale" is exactly what the biggest wallpaper sub rejects: r/wallpaper's own FAQ says *"This is what separates our community from other wallpaper communities. Users expect a curated collection of **pixel-perfect** wallpapers, without relying on external tools or the OS to resize them automatically."* Its automod matches against a fixed whitelist.

**What a 1080×1920 does on a modern phone.** 1080×1920 is 16:9. No phone shipping in 2026 is 16:9. On an iPhone 17 Pro Max (**1320×2868**, ≈19.56:9, [Apple](https://support.apple.com/en-us/125091)) the OS scales to fill height — ×1.494 — producing a 1613px-wide image of which **18% of the width is cropped, 9% off each side**, on top of a 1.49× upscale from a 1080px source. Anything you put near a left or right edge, including a corner hex, is gone. This is the argument against corner placement, not against the hex.

**Portrait master: 1440×3200 (20:9), PNG.** Covers everything by down-scaling, never up:

| Device | Native | From a 1440×3200 master |
|---|---|---|
| Galaxy S25 Ultra / S25+ | 1440×3120 (19.5:9, [GSMArena](https://www.gsmarena.com/samsung_galaxy_s25_ultra-13322.php)) | 1:1 pixels, 2.5% height crop |
| iPhone 17 / 16 Pro Max | 1320×2868 | ×0.917, 2.2% height crop |
| iPhone 17 Pro | 1206×2622 | ×0.838 |
| iPhone 17 / 16 / 15 | 1179×2556 | ×0.819 |
| Common Android (S25, mid-range) | 1080×2400 (20:9) | exactly ×0.75, no crop |

**Landscape master: 3840×2160.** It divides *exactly* into 1920×1080 (÷2) and 2560×1440 (×2/3), which matters because 4K is not where people are: StatCounter, June 2026, worldwide desktop — **1920×1080 20.2%**, 1536×864 6.94% (that's a 1080p panel at 125% Windows scaling), 1280×720 6.01%, 1366×768 5.71%. 3840×2160 is not in the top six. Ship 3840×2160, 2560×1440, 1920×1080, and **3440×1440** — ultrawide is on r/wallpaper's whitelist, the ultrawide crowd is chronically underserved, and a spectrum band or a temperature-ordered strip is *natively* 21:9 content. The doc omits ultrawide entirely; it's the cheapest win in the plan.

**Ship PNG, not JPEG, and dither.** r/Amoledbackgrounds' Rule 1 says outright: *"If your post was removed for R1 and you're sure it had over 50% true black, please submit it as a PNG instead of JPG/jpeg"* — JPEG's ringing pushes true black off `#000000` and fails their automated check. Separately, an 8-bit gradient on near-black **bands visibly on OLED**, and banding is the #1 quality complaint in that sub. Add ±1 LSB blue-noise dither before export. Their Rule 4 also asks you to be ready to provide an **uncompressed link** — that is a rules-sanctioned reason to link your own PNG, and the cleanest way your URL ever enters a thread.

**Composition: the doc gives one rule for two canvases with opposite safe zones.**
- *Phone.* "A planet dead-centre is bad, icons land on it" is true — but the fix isn't "offset". iOS's lock screen owns the **top ~35%** (clock, date, widget row) and the home grid covers nearly everything else; the only region reliably visible on both is the **lower third**, in the band between the last icon row and the dock. Put the disc's centre at ~72–78% height, horizontally centred. "Leave the top-left quiet" is accidentally right on Android (Pixel's At a Glance widget) and wrong about why.
- *Desktop.* The centre is the **safest** place, not the worst — Windows stacks icons top-left, macOS top-right, menu bar 24pt top, dock ~80px bottom. Subject centre or slightly right; both top corners and the bottom 100px empty.
- *True black is not a third size.* It's the default for the phone canvas and a variant for desktop. Correct the doc's framing.

**The hex: keep it, but as a caption, not a mark.** At 1440px wide a 24px mono label is ~1.3mm on glass — unreadable, so it reads as a smudge of branding. It needs ~44px minimum, which is big enough to be a design element, so make it one: name / host star / hex on **one baseline in the bottom margin**, set in the palette's shade-1 so it recedes rather than in white. Then ship a **clean, type-free variant of every export** and post *that* one to Reddit. It's not a gimmick — the hex is the only thing that distinguishes this from a Midjourney planet — but it must be typography, not a signature.

## Would these get removed?

Rules below were read on **2026-07-30** from a working Redlib mirror (`safereddit.com`), which returns the real sidebar and wiki text — the previous reviewer of `10-reddit.md` concluded Reddit rules were unverifiable, and that is no longer true. Quotes are verbatim.

**The linking strategy survives. The doc's fear is unfounded — but only for image posts.** r/wallpapers' wiki, *On Self Promotion*: *"Every post must contain at least 1 usable wallpaper image… Promo goes in a comment to the post, not in the post body. You can say something in the post title, for example: '[OC] Beautiful Flower Art, link to wallpaper pack inside'."* And r/Amoledbackgrounds **requires** a top-level source comment containing the word `source`, `credit`, or `original`. So `/wallpapers` is linkable in both — from a comment, under a post that already contains a usable image. A link post to the page dies everywhere.

**The bigger correction: neither r/wallpaper nor r/wallpapers will take a phone wallpaper.** `10-reddit.md` lists "r/wallpapers 736k — GO, reuse Amoled pack". It will be auto-removed.
- **r/wallpaper — 2.0M** (bigger than the doc's list acknowledges; it isn't in there at all). *"Desktop computer screen resolutions size images only. No vertical/mobile/square sizes!"* · titles must contain *"the image resolution (width x height surrounded by brackets) AND… a description of the image. Generic words like 'Photograph' or 'Wallpaper' are not good enough"* · *"Submit direct links to images or imgur/reddit albums only"* · *"No URL Shorteners — …Hyperlinks you make in comments"* (UTM links are fine; bit.ly is a removal) · *"Tag AI posts by using the 'AI' flair or include the text [AI] in your title."*
- **r/wallpapers — 736.4k.** Rule 4: *"No Portrait//Mobile wallpapers. We are a place for desktop wallpapers."* Rule 3: min 1024×768. Rule 2: max 25 images per post. Reposts of a specific image: ~1 month.
- **r/Amoledbackgrounds — 345.7k.** ≥50% `#000000` (*"for album/gallery submissions, the lowest true black percentage across all of the images must be at least 50%"* — one bright image kills the whole gallery), resolution tag in the title *"horizontal first, then vertical"* plus a suggested aspect tag (`[9:20]`), `[OC]` in the title if you made it, source comment mandatory, no live wallpapers, reposts only after 90 days with credit. Its public description says **"No AI allowed."** A physics-derived coloured disc *will* be accused; the calibration figure from `10-reddit.md` is the reply.
- **Phone posts go to r/MobileWallpaper (244.2k) and r/Verticalwallpapers.** r/Verticalwallpapers Rule 4 is *"No Spam Or Promotion… Spam/promotion will lead to being banned"* — post the image there and say nothing about the site.

**"No watermark" is over-stated.** r/wallpaper's *not allowed* wiki: *"Overlays that significantly detract from the usability of the image (including opaque watermarks or overlays that cover the majority of the image) are not allowed. Overlays or watermarks typically added by authors (e.g. a signature at the bottom of the image) are fine."* A bottom-margin caption is explicitly permitted. Culturally the previous reviewer is still right that a clean variant is what you post; mechanically, you were never at risk.

**PNG metadata credit does not survive Reddit.** Reddit re-encodes on upload and strips it. Keep the metadata — it's free and it works on downloads from your own domain — but don't count it as attribution in a thread.

## Five concepts worth keeping

The doc's own risk section names the problem ("looking generic… the derivation has to be visible") and then never answers it. Here is the answer, and it starts by giving up the disc. **A lit sphere is what every space wallpaper already is. The spectrum is the thing only this project can draw.** All five are grounded in fields `pipeline/emit/build.py` already writes: `spectrum` (the albedo curve), `phase_colours` (0–180° in 10° steps with true `luminance_y`), the band-set colours and ΔE, and the host-star illuminant.

**1. The fingerprint — the spectrum *is* the wallpaper.** Full-bleed. Vertical axis is wavelength, 380 nm at the top to 780 nm at the bottom; each row is drawn in that wavelength's monochromatic sRGB, with its *brightness* set by A(λ)×S(λ) for this planet. The physics then draws itself: a methane world has literal dark bars across the red, a sodium-eaten hot Jupiter has a black stripe through the yellow, a Rayleigh-blue world is bright at the top and dead at the bottom. Over it, one 2px oscilloscope trace of A(λ) in the accent colour, wavelength ticks at 400/500/600/700 nm in the bottom margin, and exactly one labelled feature (`CH₄ 730 nm`). Icons sit on a smooth vertical gradient perfectly. It is unmistakably from this project, it is a portrait of a specific world rather than a picture of a ball, and it is the *only* wallpaper anywhere that is a real reflectance spectrum. **This is the one to build.** Not ≥50% black, so it goes to r/wallpaper (landscape re-cut) and r/MobileWallpaper, not AMOLED.

**2. The phase ladder.** Eleven discs in a single column down the phone, α = 0°→180°, each at its true terminator geometry *and* its true phase colour and `luminance_y` — so the column genuinely fades to black at the bottom, because the physics says it does. A lunar-phase chart for a world nobody will ever see. Bottom margin: `α 0° → 180°`. Horizontal across the lower third for desktop. Rhythmic enough to survive an icon grid, and it rewards a second look a year later. Clears AMOLED's 50% bar trivially.

**3. The lamp and the world.** Two discs, one calculation: the host star at its computed colour, large, upper third; the planet small in the safe lower third, lit from the star's direction; a hairline between them and one line of mono type — `A(λ) × S(λ) = #4a6ea9`. This is the entire thesis in one frame, and it's the one that makes a stranger ask what they're looking at. Pick M-dwarf hosts for the strongest ones: a deep-red lamp and a world that is that colour *because of the lamp*. On the lock screen the star sits behind the clock, which is the correct place for it.

**4. The catalogue barcode.** All 5,764 planets as hairlines in equilibrium-temperature order — stacked horizontally down a phone, vertical columns on a 3440×1440 ultrawide, temperature axis in the margin. **One strip, not two**: two strips is a chart, one strip is a wallpaper; keep the Roman comparison for the ultrawide, where there's room. Ship a variant with a single tick marking one planet (`HD 189733 b is here`), which is also the cheapest possible version of the personalisation hook the README has parked. Nobody else can make this image, because making it requires having computed 5,764 colours from physics.

**5. The sky sheet.** From the existing sky-chart data: a true-position star field for one constellation, catalogue stars in white at real magnitude — and every planet-hosting star drawn in **its planet's** computed colour, sized by planet radius. Margin: constellation, epoch, and one honest line ("coloured stars host worlds whose modelled colour is shown"). It is the only image here that answers *where*, it looks like an instrument plate, and it's the one people will print.

*Sixth, nearly free, belongs to family 4:* one bar per discovery year, 1992→2026, each the mean colour of that year's planets. The palette of the entire search, as a ramp. Perfect for the palette-only variant the doc already wants.

## Wrong or unverified

- ❌ **"Offer three sizes and nothing more… devices scale."** Directly contradicted by r/wallpaper's pixel-perfect requirement and automod whitelist. Corrected in the doc.
- ❌ **r/wallpapers as a place for the AMOLED phone pack** (from `10-reddit.md`, which I can't edit). Rule 4 bans portrait. Flagged in 07's new sub-routing note.
- ❌ **"No watermark."** Over-stated; a bottom signature is explicitly allowed at r/wallpaper. Softened to "no overlay, caption instead".
- ❌ **"Put the full credit and URL in the PNG metadata."** True on your own domain, useless on Reddit — it's stripped on upload.
- ⚠️ **"A planet dead-centre is a bad wallpaper."** True on phones, false on desktops. Split in the doc.
- ⚠️ **Pixel 9/10 Pro XL ≈1344×2992** — I could not re-verify this before the session's search budget ran out; the 1440×3200 master covers it either way. Don't quote it.
- ✅ **True black must be `#000000`, not near-black** — confirmed verbatim, and the 50% threshold is real and machine-checked.
- ✅ **"Curate it by hand; most of 5,700 make a mediocre wallpaper"** — correct, and it's the only part of this plan that can't be automated.
- ✅ **The `/wallpapers` page is safe to link.** Verified for both r/wallpapers and r/Amoledbackgrounds, from a comment. Do not make it a link post.
- Subscriber counts read live 2026-07-30: r/wallpaper 2.0m, r/wallpapers 736.4k, r/Amoledbackgrounds 345.7k (the `10-reddit` review's 324k appears stale), r/MobileWallpaper 244.2k.

## Better approaches

1. **Build concept 1 only, three canvases, twelve planets, one evening.** `web/og.py` already ports the disc shader to numpy/PIL and `spectrum` is in the JSON, so the fingerprint is a new `pipeline/wallpaper.py` that never touches WebGL. Ship it, post one image, and see whether anyone cares before building concepts 2–5.
2. **Keep `/wallpapers`, but make it a plain grid of direct PNG links** — no zip (Reddit distrusts offsite archives), no nav entry, no generator UI. The curation is choosing ~24 planets; everything else is a loop.
3. **Add ultrawide 3440×1440 from day one.** Concepts 1 and 4 are natively 21:9, the sub is starved, and it costs one line in the export list.
4. **If the evening has to go somewhere else, it should.** The calibration figure and the two-strip chart from `10-reddit.md` unlock more subs, more of the press kit, and the site's own credibility panel. Wallpapers are correctly placed in Phase 2 — don't promote them.
5. **Explicitly don't build:** a wallpaper generator with options, all 5,764 rendered, `.ase`, an app, or a fourth composition. The doc's own scope-creep warning is right and should be enforced hard.

## The one thing I'd change

Delete **"Include the colour — the hex, small, somewhere"** as the differentiator and replace it with the actual one: **the wallpaper should be the spectrum, not the planet.** A disc is a picture of a ball that anyone can fake; a reflectance spectrum painted as light is a *measurement*, it can only come from this pipeline, and it is the answer to the question the doc asks itself and drops.

## What I edited

In `07-wallpapers.md`, preserving structure, the `**Status:**` line and `## Links`:

- Replaced the "three sizes and nothing more" paragraph with the corrected export spec (portrait 1440×3200 master + exact device sizes; landscape 3840×2160 with its exact divisors; ultrawide 3440×1440), and the pixel-perfect rationale.
- Added a **sub-routing** note: r/wallpaper (2.0M) and r/wallpapers (736k) are desktop/landscape only; phone exports go to r/Amoledbackgrounds, r/MobileWallpaper, r/Verticalwallpapers. Flags the wrong routing in `10-reddit.md`.
- Split the composition bullet into phone (lower third) and desktop (centre, corners quiet) with the reasons.
- Corrected the watermark bullet (bottom caption explicitly permitted; Reddit strips PNG metadata) and the hex bullet (caption on a baseline, ≥44px, shade-1, plus a clean type-free variant).
- Added a **format** bullet: PNG not JPEG (their Rule 1 says so), blue-noise dither against OLED banding, uncompressed link on request.
- Rewrote the "looking generic" risk to point at this review's five concepts and to state the spectrum-not-disc principle.
- Added a provenance line naming the source and date of the rule quotes.
