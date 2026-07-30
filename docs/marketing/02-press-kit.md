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

Build it as a normal page in the site, not a PDF and not a Drive folder — a link that works
instantly beats a download every time (though still offer one `press.zip` for the picture desk).
Keep it in the site's own visual language; it's a page people will judge you by.

**Two pages, not one, and the order matters.** A hobby project with a corporate-looking `/press`
page reads as a startup pretending to be a person, which is precisely wrong for the curator
audience in [12](./12-design-newsletters.md) — Naive Weekly, Web Curios and Waxy are buying
"one person, evenings", and a media-relations page argues against it. But a NASA comms officer
or a science desk genuinely does need a stable asset URL. Resolve it by splitting audiences:

- **`/about`** — the human page, and the one you build first. Name, face, one-line bio, what
  this is, why you made it, email address, and a plain "Using these images" block that links to
  the assets. This is what a curator, a scientist or a reader lands on, and it's what the site
  is currently missing entirely.
- **`/press`** — the thin asset page: downloads, specs, credit lines, captions, facts, second
  sources. Titled in plain language (**"Images and information for writing about this"**), never
  "Media Centre", never with a logo lockup or a "brand guidelines" section. `/about` links to
  it; you paste it into pitch emails; nobody arrives at it by accident.

Same evening's work, correctly aimed. And a footer email on every page, which is the thing that
actually catches the enquiries neither page will.

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
- The **Band-1-only** still (one grey disc where the colour was) — see
  [15-roman-launch.md](./15-roman-launch.md), which correctly calls this the best single
  screenshot the project can produce. It is also the picture that makes the honesty visual.
- Two or three individual planet renders on transparent/black, usable at any size.
- A square and a 16:9 crop of each, because layout constraints are real.
- State the licence explicitly (see below). A writer who can't tell whether they may publish
  the image will not publish the image.

**Specifications, because "2400px" is not a spec.** Every asset ships as:

| Property | Value | Why |
|---|---|---|
| Colour space | **sRGB IEC61966-2.1, profile embedded** | A colour project whose press images get colour-shifted by a CMS has failed at its own subject. Untagged PNGs are re-interpreted downstream. Non-negotiable. |
| Screenshots / UI | PNG-24, no browser chrome, no cursor, no scrollbar | Chrome dates the image and looks amateur |
| Renders / photographic | JPEG q90 **and** PNG; each under 5 MB | Some CMSes reject PNG over a few MB |
| Longest edge | 3000 px master, plus a 1200 px web copy of each | 3000 px ≈ 300 dpi at print column width; the 1200 px copy is what most web desks actually run |
| Crops | 16:9, 1:1 and 3:2 of every hero, with ~8% dead margin on the subject | You will be cropped. Decide where. |
| Metadata | **IPTC/XMP `Creator`, `Credit`, `Description`, `CopyrightNotice`, `WebStatement` written into every file** (`exiftool`, scriptable) | This is the one that matters: the credit and the "modelled, not photographed" line then travel *inside the file*, and survive the picture being pulled off the page, dropped into a CMS, or re-shared with no caption |
| Alt text | Supplied per asset, one sentence | Curators paste it verbatim ([12](./12-design-newsletters.md) says so explicitly) |
| Bundle | One `press.zip` (~<60 MB) with everything, plus per-file links | A writer on deadline wants one download; a picture editor wants one file |

**Motion, which the current list omits entirely.** [12-design-newsletters.md](./12-design-newsletters.md)
treats it as a hard requirement (Design Spells and Hover States effectively won't run a static
site), and any broadcast or YouTube-science approach will ask on the first email:
- **Phase-slider clip** — 8–12 s, 1200 px wide, MP4 (H.264) *and* GIF under 5 MB.
- **Broadcast-safe version** — 1920×1080, H.264, ~10 Mbps, **no music, no on-screen text, no
  logo**, clean head and tail. Anything with a soundtrack or burnt-in captions is unusable to a
  TV or video desk and they will not ask twice.
- **Vertical 1080×1920** cut of the same thing, for social and for anyone doing a Short.
- One line stating whether the motion is licensed the same as the stills. It should be.

**3. "How to describe these images" — not a caveat, a spec.** Give them the honesty in your
words so it appears in their piece in your words: what a geometric albedo model is, why these
are computed rather than photographed, what the solar-system anchors prove about the pipeline,
and why microlensing planets are flagged.

But a paragraph is the *weakest* place to put it, because paragraphs are what a sub-editor cuts
from the bottom, and the person who rewrites your piece never read this page. Assume the
paragraph dies. Put the honesty where it can't be cut instead — see
**[Making it survive the rewrite](#making-it-survive-the-rewrite)** below, which is the real
content of this item and the highest-value thing on the page. Never head this section
"Caveats" or "Disclaimer"; head it **"How to describe these images"**. One is a condition you
impose on the writer, the other is a service you do for them, and they get filed accordingly.

**4. Facts and figures.** Planet count, wavelength range, the Roman CGI bandpasses, the data
sources, the stack, the fact that it's static and uses only cookieless PostHog analytics.
Bullet points, all copy-pasteable, all current — generate the numbers at build time from
`planets.json` so the page can't go stale. (Same discipline `web/meta.py` already uses for
descriptions.)

> **Do not write "the four Roman bands" on this page.** The January 2025 CPP flight Primer
> lists Band 1 (575 nm/10%), Band 3 (730 nm/15%) and Band 4 (825 nm/10%) — there is no 660 nm
> band in the flight configuration — and **only Band 1 imaging with the hybrid Lyot coronagraph
> is a formal requirement**; everything else is best-effort. See
> [15-roman-launch.md](./15-roman-launch.md). Shipping a press page that gets Roman's own
> instrument wrong, on a project whose entire pitch is accuracy, is the worst single error
> available here. The band-model fix is blocking for this page, not just for `/roman`.

**5. Attribution and licence.** What you're built on
([13-credit-the-scientists.md](./13-credit-the-scientists.md)) and what others may do with
your images. **CC BY 4.0** on your own renders is right — it's what ESO, ESA/Webb and ALMA all
use for press imagery, so science desks already have a workflow for it, and it guarantees the
credit line travels with the image. Three things the current draft gets loose, though:

- **You cannot blanket-license the screenshots.** A planet page contains third-party imagery
  with its own terms: the ESA/Webb and JWST direct-image frames are CC BY 4.0 credited to
  *"NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)"*, and the five
  solar-system photographs are NASA public domain credited to NASA/JPL, NASA/JPL-Caltech,
  NASA/JPL/Space Science Institute and the Apollo 17 crew (`pipeline/observations.py` already
  carries every credit string — use it). Offering all of it as "CC BY 4.0, João" is a licence
  you don't hold. Fix: a **per-asset licence table**, and build the hero, the true↔Roman
  comparison and the Band-1 still from *rendered swatches only*, so the flagship images are
  yours outright and carry no encumbrance.
- **Write the credit line for them, in both forms**, and say that using it exactly satisfies
  the licence — ESO's page does this and it's why their credit survives. Online:
  `Exoplanet Palette / [YOUR FULL NAME] (CC BY 4.0)`, with the name linked to the site. Print,
  where a hyperlink can't carry the attribution: `Exoplanet Palette / [J. SURNAME], CC BY 4.0`.
  Add one line: *"Crops and colour-space conversions are fine and need no separate note."* CC BY
  4.0 formally requires indicating changes; pre-authorising the two changes every desk actually
  makes removes the only clause a cautious picture desk stalls on.
- **CC BY 4.0 is irrevocable.** That's the point, but say it deliberately: anything you publish
  under it can be reused commercially, forever, by anyone, including people you'd rather not.
  Reserve all rights on nothing except the site name and favicon.

**6. Contact — and the human.** This is the largest gap in the current draft. "Built by one
person" is the hook, and the page never names the person. A desk cannot run "built by one
person"; it runs a name, an age or a job, a town and a face. Supply, without being asked:

- **Full name, spelled as it should appear in print**, plus the accent-free fallback some CMSes
  will force (`João` → `Joao`) so the version that ships is the one you chose.
- **A one-line bio** you'd be happy to see quoted whole. Include what you do for a living and
  that this is evenings and weekends, and state plainly that you hold no astronomy affiliation.
  A desk that discovers mid-edit that its source isn't credentialed kills the piece; a desk
  told up front runs it as "a software engineer in Portugal, in his own time", which is better.
- **A headshot** — 1200 px square, JPEG, same CC BY 4.0 terms, plain background. They will run
  it, and if you don't supply one they will crop your LinkedIn photo badly.
- **Location and timezone** — Portugal, WEST (UTC+1) / WET (UTC+0) in winter — and **languages:
  Portuguese and English**, which is worth stating because Portuguese-language desks (Público,
  Observador, RTP) are a real and completely uncontested audience for this.
- **Availability, honestly.** "Email is answered within a few hours in European daytime.
  Available for a recorded video or phone call with about a day's notice." If you're willing to
  do a live spot, say so; if you're not, say that too — an unanswered request is worse than a no.
- **The launch-night line.** Roman lifts off 30 Aug at 07:26 EDT — 12:26 in Lisbon — and US
  desks will be filing until well past midnight your time. Put one sentence on the page:
  *"For anything Roman-related between 29 August and 2 September, mark the subject line URGENT
  and it reaches my phone."* Then set that filter and actually honour it. A reachable amateur
  beats an unreachable institution on deadline night, and this is the one week where being a
  single person with a phone is an advantage rather than a limitation.
- **An email address you check. Not a form.** Also put it in the site footer — the site
  currently has no footer, no About page and no contact address anywhere, which means today
  there is no way to reach you at all.

**7. Three stories you could write, and what's wrong with the project.** Two short blocks that
cost nothing and mark you as someone who has done this before. A story menu — *the honesty
angle · what Roman can actually deliver · the one-person craft story* — because a press officer
supplies angles, not just facts. And a genuine **known-limitations** list: blackbody
illuminants, cloud assumptions, no phase-curve validation, unmeasured albedos. Publishing your
own weaknesses is what a fact-checker is trying to establish anyway, and it converts a
five-email verification into zero.

**8. Second sources.** Name three people a journalist can call who are *not you*: the authors
whose albedo work you use, the PICASO maintainers, and the CPP contacts in
[15-roman-launch.md](./15-roman-launch.md). Every science desk needs one independent voice
before it runs a claim. Handing them that list is the single most professional thing on the
page — and it makes the [13-credit-the-scientists.md](./13-credit-the-scientists.md) emails
land better, because you're offering those scientists coverage rather than asking for a favour.

## Copy — the 150-word version to draft first

> **Exoplanet Palette** shows the colour of every known exoplanet — around 5,700 of them —
> computed rather than imagined. For each planet it models the light reflected from its
> atmosphere, multiplies that by its host star's spectrum, and runs the result through the CIE
> 1931 colour-matching functions to get a colour a human eye would actually see. Methane makes
> a world blue-green; thick cloud pushes it toward white; a cloud-free hot Jupiter comes out
> nearly black.
>
> Every planet is also shown "as Roman would see it" — the same colour reconstructed from the
> visible bandpasses of the Nancy Grace Roman Space Telescope's coronagraph, and from the single
> 575 nm band that is the instrument's only guaranteed measurement — so you can see how much
> colour identity survives a real instrument.
>
> These are models, not photographs, and the site says so on every page. Five solar-system
> planets are included as a check: their computed colours can be compared against real images.
>
> Built by [YOUR FULL NAME], one person, in Portugal, on evenings and weekends. [SITE_URL]

Trim to 40 and 15 words from this, don't write three separately — they should agree.

## Making it survive the rewrite

The [12](./12-design-newsletters.md) risk list already names the failure: an outlet prints
"photographs of exoplanets" and the project's core claim is gone. Writing a good caveat does not
prevent this. Caveats are cut, and understanding *why* tells you where to put the honesty
instead. They get cut because they sit in their own paragraph and pieces are trimmed from the
bottom; because they're phrased as negatives and negatives are the cheapest words to lose;
because nothing else in the piece depends on them; and above all because the person who cuts
them is a sub-editor on deadline who never saw your press kit and is working from the headline,
the picture and the caption. Plan for that person, not for the writer you emailed.

Six places to put it, in descending order of survivability. Do all six; together they cost an
evening and no single edit can remove them.

**1. Inside the noun.** Stop saying "the colours (which are modelled)". Say **"computed
colour"**, every single time, in every asset, filename, caption, alt text and blurb. A modifier
inside a noun phrase cannot be cut without rewriting every sentence that contains it, and no sub
does that. This is exactly why *"artist's impression"* has survived forty years of science
desks: it isn't a disclaimer, it's the name of the thing. You are competing with that phrase
and you need one of your own. Pick it once and never vary it — "computed colour" and
"photographed" are the two words the whole project rests on.

**2. In the caption.** Captions almost never get cut: the space is already allocated, and they
are usually assembled last, from whatever the supplier wrote, by someone with no time to
rewrite. So the caveat's real home is a 25-word caption, supplied per image, ready to paste:

> *Computed colour of HD 189733 b, derived from its modelled reflected-light spectrum and its
> star's light. Not a photograph — no exoplanet has ever been photographed in visible colour.
> Exoplanet Palette / [J. SURNAME] (CC BY 4.0).*

**3. Burned into the image.** A small label in the safe margin — `COMPUTED COLOUR · NOT A
PHOTOGRAPH` — in the site's own type, on every hero render. This is the only version that
survives the picture being cropped, screenshotted, lifted off Bluesky, or run with no caption
at all. Observatories watermark artist's impressions for exactly this reason. It costs credible
effectively nothing and it is the difference between honesty you asserted and honesty that is physically
attached to the file. Ship it with the IPTC `Description` field saying the same thing.

**4. Inside the only quotable sentence.** Journalists lift whole sentences. Give them exactly
one and repeat it in every pitch, so the sentence that spreads carries the caveat as its subject:

> *"Nobody has ever photographed the colour of a planet around another star. So I computed all
> 5,700 of them, and the site tells you where the model ends."*

If that's the quote, the caveat cannot be cut without cutting the quote.

**5. As a number, not a hedge.** *"Five of these 5,700 worlds have ever been photographed —
and all five are in our own solar system."* Editors cut hedges and keep statistics, because a
number reads as reporting and a hedge reads as legal. That sentence belongs in the standfirst
and it will often get there. Same trick for Roman: *"one guaranteed measurement per planet."*

**6. By making the honesty the story.** The strongest protection is structural: if the honesty
is the news, cutting it costs the editor the piece. The current framing invites "pretty planet
colours (with caveat)", which is a picture story with a hedge attached and will be cut to the
picture. The available framing is a genuine one nobody else is running:

> **Almost every exoplanet image you have ever seen is an artist's guess. This is what we
> actually know — and Roman, the telescope launching this month to look at these planets, will
> return one number per planet, not a picture.**

Now the caveat is the premise, the antagonist is the artist's impression, and the tension is
real. [15-roman-launch.md](./15-roman-launch.md)'s information-budget argument and the
pre-registered predictions are the same move: honesty *demonstrated* rather than asserted. A
project that publicly grades its own wrong predictions cannot have its honesty edited out,
because the honesty is the thing being reported.

**Two mechanical extras that punch above their weight.**

- A short **"please write this, not that"** box. Two columns, four lines. Subs are not trying
  to be wrong, they are trying to be fast: ✗ *"photograph of an exoplanet"*, *"NASA image"*,
  *"what the planet looks like"* → ✓ *"computed colour"*, *"independent project using NASA
  data"*, *"the colour physics predicts"*. This is the cheapest item on the whole page and it
  is the one that most often works.
- **Offer to check the caption.** One line: *"Send me your caption and I'll check it within the
  hour — no approval, no changes to your copy, just the physics."* It costs the writer nothing,
  protects them, and is accepted far more often than you'd expect. Pair it with a stated
  corrections policy, and never ask to see the article.

And never use the words "caveat" or "disclaimer" anywhere on the page. They signal a condition
being imposed, and they get filed with the legal boilerplate — which is the one part of a press
kit nobody reads.

## How it gets used

Every pitch email in [12-design-newsletters.md](./12-design-newsletters.md) and every approach
in [15-roman-launch.md](./15-roman-launch.md) ends with the `/press` link instead of an
attachment. It's also the link you give anyone who asks "can I write about this" — including
the scientists in [13-credit-the-scientists.md](./13-credit-the-scientists.md), who often have
institutional comms people who will ask exactly that.

**Reconcile the asset list with what the two consumers actually specify**, because they ask for
things this doc doesn't list. [12](./12-design-newsletters.md) needs a **palette-export
screenshot** (1600×1200, showing hex / CSS variables / .ase), a **full-grid poster** (3000 px
square, for Colossal and social), a **canonical site OG card** (1200×630), and per-asset alt
text. [15](./15-roman-launch.md) needs the **Band-1-only** still, the
`/roman/what-roman-can-see` explainer as a linkable page, and the predictions DOI. Build the
union, not this doc's list — otherwise the first two pitches you send both need an asset you
haven't made.

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
- **Getting Roman's instrument wrong on the press page.** The "four bands" figure is not the
  flight configuration ([15](./15-roman-launch.md)). This is the highest-consequence error
  available: it would be reprinted, it would be caught by exactly the CGI people you most want
  as allies, and it would be caught in the one document whose subject is accuracy.
- **Licensing images you don't own.** Screenshots contain ESA/Webb and NASA/JPL imagery with
  their own credits. Blanket "CC BY 4.0, all of it" is a false grant. Per-asset table, and keep
  third-party frames out of the flagship images.
- **Over-designing it.** It's a utility page. Two hours, not two weekends.
- **Looking like a press office.** For half the audiences in this plan, "one person" is the
  entire pitch. Plain language, a real name, no brand guidelines, no third person. Never write
  "Exoplanet Palette is pleased to announce".
- **Licence ambiguity.** Half-stated terms are worse than none — a careful outlet will skip
  rather than risk it.
- **The unreachable moment.** The one email that matters will arrive at 22:00 on a Sunday in
  launch week. If it goes unanswered for eighteen hours the story runs with someone else's
  picture. Set the filter before 29 August.

## Links

- [README.md](./README.md) — the hub
- [12-design-newsletters.md](./12-design-newsletters.md) — the main consumer of this page
- [15-roman-launch.md](./15-roman-launch.md) — where a ready press kit matters most
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — attribution lives on both pages; keep them consistent
- [07-wallpapers.md](./07-wallpapers.md) — shares the render-export machinery
- [09-show-hn.md](./09-show-hn.md) — have this live before launch day
- [99-tracking.md](./99-tracking.md) — the placement log
