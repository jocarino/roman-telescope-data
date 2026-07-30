# Press kit — make covering us a ten-minute job

**Status:** not started · **Effort:** one evening · **Payoff:** medium, but it unblocks several others · **Hub:** [Marketing plan](./README.md)

## The bet

A writer at a science or design outlet has ninety minutes to file, and needs an image at the
right size, a description they can quote, and a sentence about what's honest and what isn't.
If they have to email you for any of it, they cover something else instead. A `/press` page
costs one evening and converts every future pitch from "will you reply in time" to "here,
take it". It is a prerequisite for [12-design-newsletters.md](./12-design-newsletters.md),
[15-roman-launch.md](./15-roman-launch.md) and any science-press approach, so build it before
you pitch anyone.

It also does a second job that matters more than it sounds: it makes a hobby project look like
something a professional can safely link to.

## What the page contains

Build it as a normal page in the site (`/press`), not a PDF and not a Drive folder — a link
that works instantly beats a download every time. Keep it in the site's own visual language;
it's a page people will judge you by.

**1. One paragraph, three lengths.** Writers copy-paste. Give them the exact text so the
description that spreads is the one you'd have chosen:
- **~15 words** (a links roundup): *"The colour of every known exoplanet, computed from
  physics rather than imagined by an artist."*
- **~40 words** (a newsletter blurb): add the how — reflected-light spectrum, CIE colour
  matching — and the Roman comparison.
- **~150 words** (a press paragraph): the how, the Roman signature feature, the honesty rule,
  and the fact that it's one person's side project. The last part is not modesty; it's the
  human-interest hook that gets a paragraph written about *you* instead of just a link.

**2. Images, ready to publish.** This is the part that actually decides whether you get
covered. Provide direct download links, each with its dimensions stated and a caption + credit
line written for them:
- A hero shot of the gallery (wide, 2400px+) — the wall of swatches is the money shot.
- One planet page, showing the spectrum plot and the palette together.
- The true↔Roman comparison as a single still — this is the image that carries the idea, so
  make a purpose-built one rather than a screenshot.
- Two or three individual planet renders on transparent/black, usable at any size.
- A square and a 16:9 crop of each, because layout constraints are real.
- State the licence explicitly (see below). A writer who can't tell whether they may publish
  the image will not publish the image.

**3. The honesty paragraph, pre-written.** Give them the caveat in your words, so it appears in
their piece in your words: what a geometric albedo model is, why these are computed rather than
photographed, what the solar-system anchors prove about the pipeline, and why microlensing
planets are flagged. If you don't write this, a rewrite writes it worse. This paragraph is the
single highest-value item on the page.

**4. Facts and figures.** Planet count, wavelength range, the four Roman bands, the data
sources, the stack, the fact that it's static and has no tracking beyond cookieless analytics.
Bullet points, all copy-pasteable, all current — generate the numbers at build time from
`planets.json` so the page can't go stale. (Same discipline `web/meta.py` already uses for
descriptions.)

**5. Attribution and licence.** What you're built on
([13-credit-the-scientists.md](./13-credit-the-scientists.md)) and what others may do with
your images. Recommend **CC BY 4.0** on the renders: it costs nothing, removes every hesitation,
and guarantees the credit line travels with the image. Reserve all rights on nothing except
possibly the logo.

**6. Contact.** An email address that you check. Not a form.

## Copy — the 150-word version to draft first

> **Exoplanet Palette** shows the colour of every known exoplanet — around 5,700 of them —
> computed rather than imagined. For each planet it models the light reflected from its
> atmosphere, multiplies that by its host star's spectrum, and runs the result through the CIE
> 1931 colour-matching functions to get a colour a human eye would actually see. Methane makes
> a world blue-green; thick cloud pushes it toward white; a cloud-free hot Jupiter comes out
> nearly black.
>
> Every planet is also shown "as Roman would see it" — the same colour reconstructed from only
> the four visible bands of the Nancy Grace Roman Space Telescope's coronagraph — so you can see
> how much colour identity survives a real instrument's filter set.
>
> These are models, not photographs, and the site says so on every page. Five solar-system
> planets are included as a check: their computed colours can be compared against real images.
>
> Built by one person. [SITE_URL]

Trim to 40 and 15 words from this, don't write three separately — they should agree.

## How it gets used

Every pitch email in [12-design-newsletters.md](./12-design-newsletters.md) and every approach
in [15-roman-launch.md](./15-roman-launch.md) ends with the `/press` link instead of an
attachment. It's also the link you give anyone who asks "can I write about this" — including
the scientists in [13-credit-the-scientists.md](./13-credit-the-scientists.md), who often have
institutional comms people who will ask exactly that.

## Timing

Before Show HN ([09-show-hn.md](./09-show-hn.md)), because an HN front page brings writers as
well as readers, and you want them to find this on the day rather than a week later.

## How we'll know it worked

Low-traffic by design — judge it by **coverage that used our images and our framing**, not by
visits. Tag the outbound links on the page and watch for referrers you didn't pitch: those are
the cascade, and they're the reason to bother. Keep a simple list of every placement in
[99-tracking.md](./99-tracking.md).

## Risks

- **Stale numbers.** A press page claiming 5,764 planets when the site shows 5,900 undermines
  the honesty positioning worse than having no page. Generate the figures at build time.
- **Over-designing it.** It's a utility page. Two hours, not two weekends.
- **Licence ambiguity.** Half-stated terms are worse than none — a careful outlet will skip
  rather than risk it.

## Links

- [README.md](./README.md) — the hub
- [12-design-newsletters.md](./12-design-newsletters.md) — the main consumer of this page
- [15-roman-launch.md](./15-roman-launch.md) — where a ready press kit matters most
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — attribution lives on both pages; keep them consistent
- [07-wallpapers.md](./07-wallpapers.md) — shares the render-export machinery
- [09-show-hn.md](./09-show-hn.md) — have this live before launch day
- [99-tracking.md](./99-tracking.md) — the placement log
