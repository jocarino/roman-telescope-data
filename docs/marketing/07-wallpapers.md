# Wallpapers — and where they live

**Status:** not started · **Effort:** low · **Payoff:** medium, long half-life · **Hub:** [Marketing plan](./README.md)

## The bet

A wallpaper is the only artifact here that someone looks at every day for a year. It's also the
cheapest thing on the list — the renderer already exists, so this is an export path and a page,
not a feature. Wallpaper communities are large, self-selecting, and re-share the same images for
years, which makes this one of the few items with a genuinely long tail.

## Where it should live — the actual question

**Two places, doing two different jobs. Don't collapse them into one.**

**1. The download control on the planet page — this is the feature.**
Put it *next to the existing palette export*, in the same control cluster. That slot already
means "take this away with you", so the affordance is learned; a wallpaper button is the same
verb applied to a different artifact. Desire happens while looking at one specific planet, so
the control has to be there and not on some other page.

Keep it as small as the palette export is — a compact control, not a banner. Offer **three
compositions** and nothing more: portrait, 16:9 landscape, 21:9 ultrawide. Compositions cost
design time; *resolutions* are a loop in a script and cost nothing, so don't confuse the two.
True black is not a third size — it's the default for the portrait canvas and a variant of the
landscape one.

"Devices scale" is the one thing the biggest wallpaper sub explicitly rejects. r/wallpaper's FAQ:
*"This is what separates our community from other wallpaper communities. Users expect a curated
collection of **pixel-perfect** wallpapers, without relying on external tools or the OS to resize
them automatically."* Its automod matches an exact whitelist. So export exact sizes:

- **Portrait master 1440×3200 (20:9).** Everything else downscales, never up: Galaxy S25 Ultra /
  S25+ 1440×3120 (2.5% crop), iPhone 17 & 16 Pro Max 1320×2868 (×0.917, 2.2% crop), iPhone 17 Pro
  1206×2622, iPhone 17/16/15 1179×2556, common Android 1080×2400 (exactly ×0.75). **Never ship
  1080×1920** — 16:9 no longer exists on phones; on a 1320×2868 screen the OS crops 18% of the
  width and upscales 1.49×, so anything near a side edge is simply gone.
- **Landscape master 3840×2160.** It divides exactly into 1920×1080 (÷2) and 2560×1440 (×2/3),
  which matters because 4K is not where people are — StatCounter, worldwide desktop, June 2026:
  1920×1080 **20.2%**, 1536×864 6.94% (a 1080p panel at 125% scaling), 1280×720 6.01%,
  1366×768 5.71%. 3840×2160 isn't in the top six. Ship all three.
- **Ultrawide 3440×1440.** On r/wallpaper's whitelist, chronically underserved, and a spectrum
  band or a temperature-ordered strip is natively 21:9. Cheapest win here.

**Sub-routing, because it decides the canvas.** r/wallpaper (2.0M) is *"Desktop computer screen
resolutions size images only. No vertical/mobile/square sizes!"* and r/wallpapers (736k) Rule 4 is
*"No Portrait//Mobile wallpapers."* Neither will take a phone wallpaper — the "reuse the Amoled
pack on r/wallpapers" line in [10-reddit.md](./10-reddit.md) is wrong and will be auto-removed.
Portrait goes to r/Amoledbackgrounds, r/MobileWallpaper and r/Verticalwallpapers; landscape and
ultrawide go to r/wallpaper and r/wallpapers.

**2. A `/wallpapers` page — this is the marketing surface.**
A curated grid of the twenty or thirty that actually look good, each downloadable in the three
sizes. This exists because **you cannot post "go to my site and click around" to a wallpaper
community** — you need one link that is unmistakably a wallpaper pack. It's also the link for
[12-design-newsletters.md](./12-design-newsletters.md) and a natural thing to mention in the
daily posts from [11-bluesky-mastodon.md](./11-bluesky-mastodon.md).

Curate it by hand. Most of 5,700 planets make a mediocre wallpaper; thirty are striking. The
curation *is* the product, and the existing curation machinery
(`pipeline/curate.py`) is a reasonable starting point.

**Don't** put it in the main navigation. It's a side door, not a pillar — link it from the
planet-page control, the footer, and the posts that need it.

## Design decisions worth getting right

*Rule quotes below were read from each sub's sidebar and wiki on 2026-07-30 via a working Redlib
mirror (`safereddit.com`), which returns the real text where reddit.com returns a 403.*

- **No overlay — but a caption is explicitly fine.** "No watermark" is over-stated. r/wallpaper's
  own rules: *"Overlays that significantly detract from the usability of the image (including
  opaque watermarks or overlays that cover the majority of the image) are not allowed. Overlays or
  watermarks typically added by authors (e.g. a signature at the bottom of the image) are fine."*
  So a bottom-margin caption is permitted. Culturally, still post the clean variant. Keep the
  credit + URL in the PNG metadata for downloads from our own domain, but **don't count on it** —
  Reddit re-encodes on upload and strips it.
- **True black for the AMOLED variant.** `#000000`, not near-black. Verbatim: *"Submissions should
  be at least 50% true black in colour, as in #000000; for album/gallery submissions, the lowest
  true black percentage across all of the images must be at least 50%"* — one bright image in a
  gallery kills the whole post.
- **Format: PNG, dithered.** Their Rule 1 says so outright: *"If your post was removed for R1 and
  you're sure it had over 50% true black, please submit it as a PNG instead of JPG/jpeg"* —
  JPEG ringing pushes black off `#000000` and fails their check. Separately, an 8-bit gradient on
  near-black **bands visibly on OLED**, which is the most common quality complaint in that sub:
  add ±1 LSB blue-noise dither before export. Their rules also ask you to be ready to supply an
  uncompressed link on request — which is a rules-sanctioned way for our URL to enter the thread.
- **Composition: the two canvases have opposite safe zones.** *Phone* — iOS's lock screen owns the
  top ~35% (clock, date, widgets) and the home grid covers most of the rest; the only region
  reliably visible on both is the **lower third**, between the last icon row and the dock. Put the
  subject's centre at ~72–78% height, horizontally centred. *Desktop* — the centre is the
  **safest** place, not the worst: Windows stacks icons top-left, macOS top-right, menu bar 24pt
  top, dock ~80px bottom. Subject centre or slightly right, both top corners and the bottom 100px
  empty. Check both against a mock icon grid.
- **Include the colour — as typography, not a mark.** At 1440px wide a 24px mono label is ~1.3mm on
  glass: unreadable, so it reads as a branding smudge. Set it at ≥44px, on **one baseline in the
  bottom margin** — name / host star / hex — in the palette's shade-1 so it recedes rather than in
  white. Ship a **clean, type-free variant of every export** and post that one.
- **A palette-only variant.** Some people want the five-stop ramp as a wallpaper more than the
  planet. Cheap to generate, and it's the version the design audience shares. The strongest version
  is a ramp with data in it: one bar per discovery year, 1992→2026, each the mean colour of that
  year's planets — the palette of the entire search.

## Timing

Any evening. Genuinely low effort, and worth having before the Reddit sequence in
[10-reddit.md](./10-reddit.md), since it's the artifact that unlocks a couple of those subs.

## How we'll know it worked

Downloads are trackable but not very meaningful. The honest measure is whether a wallpaper post
sends people who then explore — same depth metric as everywhere else. Tag the `/wallpapers`
links `utm_medium=wallpaper` per source. See [99-tracking.md](./99-tracking.md).

Watch for the second-order signal: wallpapers get re-posted by other people. If you see the
images circulating without your link, that's success *and* a prompt to make the in-image name
slightly more findable.

## Risks

- **Scope creep.** This is an export path and a page. If it becomes a wallpaper generator with
  options, it has eaten a weekend that Show HN deserved.
- **Looking generic — and the fix is to give up the disc.** The internet has infinite space
  wallpapers, and a lit sphere on black is what every one of them already is. The derivation has
  to be visible *in the image*, which means the strongest wallpaper here is not the planet but
  **the spectrum**: wavelength down the frame, each row in that wavelength's own colour, brightness
  set by A(λ)×S(λ), so a methane world draws literal dark bars across the red. That is a
  measurement, it can only come from this pipeline, and it survives an icon grid better than a
  disc does. Four more concepts in the same spirit — the phase ladder, the lamp-and-world pair,
  the 5,764-planet temperature barcode, the sky sheet — are specced in
  [reviews/07-wallpapers-review.md](./reviews/07-wallpapers-review.md). Build the spectrum one
  first and see whether anyone cares before building the rest.
- **File size.** A curated page of thirty large PNGs is heavy; the shared-asset discipline from
  the perf work applies here too.

## Links

- [reviews/07-wallpapers-review.md](./reviews/07-wallpapers-review.md) — the adversarial pass: the
  five wallpaper concepts, verified sub rules, and why the disc is the wrong artifact
- [README.md](./README.md) — the hub
- [10-reddit.md](./10-reddit.md) — the communities this unlocks, and their specific rules
- [12-design-newsletters.md](./12-design-newsletters.md) — a downloadable pack is an easy placement
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — the daily post can offer these
- [02-press-kit.md](./02-press-kit.md) — shares the render-export machinery
- [99-tracking.md](./99-tracking.md)
