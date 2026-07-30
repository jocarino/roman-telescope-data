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

Keep it as small as the palette export is — a compact control, not a banner. Offer three sizes
and nothing more: phone, desktop, and a true-black AMOLED variant. A dropdown of fourteen
resolutions is a worse experience than three good defaults; devices scale.

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

- **No watermark.** Wallpaper communities actively downrank watermarked images, and a watermark
  on a wallpaper is a small daily insult to the person who chose it. Put the planet name
  discreetly in a corner instead — that's what makes someone search for it later — and put the
  full credit and URL in the PNG metadata, where it costs nothing.
- **True black for the AMOLED variant.** `#000000`, not near-black. That community is specific
  about it and it's the difference between a top post and a removal.
- **Composition matters more than the render.** A planet dead-centre is a bad wallpaper — icons
  land on it. Offset the disc, leave the top-left quiet, and check it with a mock icon grid.
  This is ten minutes of thought that decides whether anyone keeps it.
- **Include the colour.** The hex, small, somewhere. It's the thing that makes it *this* project's
  wallpaper rather than a generic space render, and it's a quiet advert every time someone
  screenshots their phone.
- **A palette-only variant.** Some people want the five-stop ramp as a wallpaper more than the
  planet. Cheap to generate, and it's the version the design audience shares.

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
- **Looking generic.** The internet has infinite space wallpapers. Ours are only interesting
  *because* the colour is derived — so the derivation has to be visible in the image or on the
  page. Lead with that framing, not with "pretty planet".
- **File size.** A curated page of thirty large PNGs is heavy; the shared-asset discipline from
  the perf work applies here too.

## Links

- [README.md](./README.md) — the hub
- [10-reddit.md](./10-reddit.md) — the communities this unlocks, and their specific rules
- [12-design-newsletters.md](./12-design-newsletters.md) — a downloadable pack is an easy placement
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — the daily post can offer these
- [02-press-kit.md](./02-press-kit.md) — shares the render-export machinery
- [99-tracking.md](./99-tracking.md)
