# Second opinion: an independent expert review

A second whole-site critique, produced 2026-08-04 by a fresh reviewer working
from the built site (localhost preview), the full-page screenshots, and the
templates — deliberately **without** access to `landing-review.md`, so the two
reviews could not anchor on each other. Persona: senior product designer /
experience producer (NYT-interactive / Stripe Press / JPL-Eyes calibre).

Verbatim below.

---

# Exoplanet Palette — Design Review

## 1. Thesis

This site has a world-class thesis and hides it behind an ℹ button. The thesis
is astonishing when you finally assemble it: *no telescope has ever
photographed an exoplanet in colour; here is the colour physics predicts for
all 5,764 of them; in 26 days a rocket launches that will turn a handful of
these predictions into measurements.* That is a New York Times interactive, a
Kickstarter video, and a museum exhibit in one sentence. But the front door
says only `the colour scheme of every known exoplanet, derived from physics` —
lowercase, set beside the logo like a shrug — and everything that makes the
project matter (the "no photographs involved" claim, the `0 COLOURS MEASURED`
column, the launch countdown) lives on interior pages reachable mainly through
a hamburger menu. The craft at the component level is exceptional and the
honesty discipline is genuinely rare. The failure is at the level of
*production*: the site behaves like an instrument you're already trained on,
not an experience that earns you. Two structural symptoms carry most of the
damage: the thesis is never stated on screen without a click, and there is no
persistent navigation — most pages, including all 5,764 planet pages, are
cul-de-sacs.

## 2. The experience walked

A newcomer lands on `/`. First screen: pixel-type masthead **EXOPLANET
PALETTE**, the lowercase tagline with an `[i]`, a toolbar (`FILTER BY COLOUR`
swatches, a `SEEN FROM ROMAN` toggle with a tiny four-band glyph, four icon
buttons), a `NEW HERE?` row of tour chips, then the grid: Earth, Jupiter,
Saturn, Uranus, Neptune, each captioned `◆ MEASURED SPECTRUM`, then GJ 581 b
and the exoplanets. The grid is beautiful — the pixel-dither discs against the
sparse starfield are instantly screenshot-worthy, and opening on the solar
system is exactly right as calibration. But comprehension wobbles immediately:
*why is Earth first on an exoplanet site?* The `MEASURED SPECTRUM` caption is
the answer, but nothing says "these five are the proof the method works"
unless you take the *Start here* tour. And nothing on this screen says the
thing that reframes everything — that these colours are predictions no one has
ever photographed. That sentence exists, closed by default, behind the `[i]`
(`x-data="{ intro: false }"` in `gallery.html`): "Computed from each planet's
reflected-light spectrum … **no photographs involved**." The single most
important line on the site is opt-in.

Emotionally the toggle `SEEN FROM ROMAN` is the best hook on the page and the
most opaque: a newcomer doesn't know what Roman is, and the payoff copy —
"That gap is Roman's, not the planets'," which is *excellent* — is again
inside an `[i]` popover. Curiosity clicks through to GJ 581 b. Here attention
succeeds brilliantly: the **EXOSCOPE** panel with `Full spectrum / Roman
4-band`, the hatched region flagged `Roman is blind here`, the `ΔE2000 31.7 —
COLOUR LOST TO ROMAN'S 4 BANDS` readout, the `PALETTE OUT ► FULL SPECTRUM` hex
strip, the **HOST STAR · THE LAMP** duotone. This page teaches by manipulation
and it works. But scroll to the bottom — past `Seen in fiction` and `Could it
hold liquid water?` — and the page just… stops. No footer, no "next planet,"
no route to `/roman`, `/tours`, or `/census`. The links out of this page are
`← ALL PLANETS`, `RANDOM`, two sibling planets, compare/sky utilities — and
`/how` appears exactly once, buried inside the EXOSCOPE's `[i]` popover
(`<a class="scope-info-more" href="/how">`). The visitor who arrived here from
a shared link — the *most likely* cold entry, since there are 5,764 of these
pages with per-planet OG cards — never learns the site has a story.

## 3. Findings

**1. The thesis is never on screen. (Landing / first impression — highest
impact.)**
Evidence: intro panel defaults closed; the tagline is descriptive ("the colour
scheme of…") not declarative. Meanwhile `/how` opens with the site's real lede
— "No telescope has ever photographed these planets in colour — most have
never been seen as more than a wobble in their star's light" — and `/roman`
has the best sentence anywhere: "**No exoplanet has ever had its visible
colour measured. Every swatch below is a prediction — which is exactly what
makes the empty column worth watching.**" Why it matters: the dual-audience
requirement fails at the door; a newcomer sees a pretty grid of planets and
has no reason to believe (or doubt!) any of it. The honesty principle also
technically leaks: with the intro closed, nothing above the fold says these
are models, not photos — the site's own hard rule, satisfied only behind a
click. Fix: a two-line masthead statement on `/`, always visible, e.g. "No
telescope has ever photographed an exoplanet in colour. These are the colours
physics predicts — for all 5,764 known worlds." Keep the `[i]` for the
five-row detail; don't make the claim itself optional.

**2. No persistent navigation; most pages are dead ends. (Information
architecture.)**
Evidence: the complete site map (`Explore — other ways into the catalogue`:
Guided tours, Compare, Census, Your sky tonight, Roman target board) exists
only inside the gallery's hamburger. Link audit of real HTML: `/census` links
only to `/`; `/how` ends with `← ALL PLANETS`; planet pages cannot reach
`/tours`, `/roman`, `/census`, or `/glossary` at all. Pages end mid-thought:
`/census` terminates on the ΔE histogram, planet pages on the water panel. The
exceptions prove the rule — the tour end-card (`◀ START AGAIN · ALL TOURS ·
BROWSE ALL PLANETS`) and, ironically, the **404 page**, whose "◈ Navigation —
pick a heading" console is the best global nav on the site. Why it matters:
"curated and cohesive" is precisely a promise about *connective tissue*. A
produced experience always answers "what's next?" at the bottom of every page.
Fix: a compact site-wide footer (the 404 console, miniaturised, would do —
it's already in the design language) plus a one-line "next" ramp per page
type: planet → "See how this colour is computed → /how" and "Next in curated
order →"; census → tours; how → the target board.

**3. The launch clock is buried. (The Roman angle — this is time-critical.)**
Evidence: `/roman` carries a live countdown (`26 DAYS · 17 HOURS…`, "30 August
2026, 07:20 EDT"), the `0 COLOURS MEASURED / 23 SLOTS AWAITING / 25 ELIGIBLE
PLANETS` scoreboard, and rows like *epsilon Eridani b · MOST REACHABLE* with a
hatched `MEASURED — awaiting Roman` swatch. It is the site's news peg, its
reason to exist *now*, its reason to return *later* — and it is reachable only
via hamburger → Explore, or a link inside the closed intro panel. Why it
matters: you have ~4 weeks in which this site is topical. Launch day is the
single best traffic moment this project will ever have, and the landing page
doesn't mention it. Fix: a small persistent countdown chip in the gallery
header — `⚑ ROMAN LAUNCH · 26 DAYS →` — linking to `/roman`. After launch it
becomes `⚑ ROMAN IS UP · 0 COLOURS MEASURED →`, which is arguably even better
copy.

**4. The gallery has no rhythm after row one. (Pacing / curation.)**
Evidence: after the anchors and the hue-deal row, it's an undifferentiated
scroll of ~1,150 rows. The curation exists (`Curated is the order the gallery
opens in…` — but that explanation lives in the *sort menu*), yet nothing in
the grid marks where curation ends and the alphabet of space begins, and
nothing interrupts the scroll to re-engage. Why it matters: 5,764 of anything
is a wall; the Feltron/NYT move is to let the editorial voice surface *inside*
the data at intervals. Fix: interstitial editorial cards every N rows in
curated order — "Why is everything blue? → Colour census", "This one was
photographed for real → beta Pictoris b" (the grid already whispers this with
its lone `● PHOTOGRAPHED` caption — promote it), "Roman launches in 26 days
→". Three or four cards total; they'd also fix finding 2 for the landing
scroll.

**5. Planet pages don't say why they matter individually. (Editorial voice.)**
Evidence: GJ 581 b's header is parameters (`GJ 581 · M3.0 V · 3500 K`) and
provenance chips; the one narrative element, `EDITOR'S NOTE`, exists only
inside tours ("If we had got Earth wrong, nothing else here would be worth
reading" — superb). The tour engine proves you can generate one editorial
sentence per notable planet; the planet page never gets it. Why it matters:
shared links land here; a single line of voice ("The first world we checked
against a photograph" / "One of the darkest worlds known") is the difference
between a data sheet and a story. Fix: surface the tour-stop blurbs on the
planet pages of every planet that appears in a tour (~50 planets, the ones
people will actually share), styled as the existing EDITOR'S NOTE.

**6. `/compare` opens empty. (Curation, small but telling.)**
Evidence: the page is two `+ CHOOSE PLANET A/B` buttons and the line "Choose
two planets above to compare their colours and the data behind them" floating
in black. Why it matters: an empty state on a *curated* site is a hole in the
argument; the owner knows the great pairings and should serve one. Fix:
preload a famous matchup (HD 189733 b vs Neptune — same blue, opposite
physics, which is literally the "Two ways to be blue" tour thesis) plus three
suggested-pairing chips.

**7. `/sky` leads with a permission dialog. (Pacing.)**
Evidence: the `LOCATE · YOUR PORTION OF THE SKY` modal covers the sky view on
arrival. The copy is honest and warm ("Read once, used only on this device,
never sent anywhere") — but it's still a gate before any value has been
demonstrated, and newcomers reflexively distrust location prompts. Fix: render
the default-latitude sky immediately; put `◎ USE MY LOCATION` in the EXO·RX
receiver panel where the latitude slider already lives, and let the modal
appear only after the user touches a location control.

**8. Mobile: the scope's picture beats its point. (Mobile.)**
Evidence: in the 390px composite, the planet page order is hero disc → meta
(collapsed behind `MORE ▾`, good) → EXOSCOPE toggle → **PLANET DISPLAY knobs**
(Style/Shape/Light source) → spectrum below the fold. The signature
interaction — flip to Roman 4-band and watch the trace and colour change —
happens off-screen from where the toggle is. Also on the mobile gallery the
`NEW HERE?` chips clip mid-word ("Start here: five worlds we can check | T…"),
which does signal scroll but reads as accident at the exact spot you're
courting newcomers. Fix: on mobile, spectrum directly under the view toggle;
knobs after. Give the chip row a fade-edge or peek margin.

**9. Long-form body copy is set in the pixel voice. (Only-you-would-catch
dept.)**
Evidence: `/how` is ~400 lines of genuinely good explanatory prose — set
entirely in the mono/pixel face on black, full-width paragraphs. Why it
matters: the costume is perfect for labels, readouts and captions, but
multi-paragraph reading in a pixel mono is fatiguing, and `/how` is the page
you most need a newcomer to *finish*. Stripe and NYT solve this with a
quieter reading face for body text while chrome stays in the brand voice.
Fix: a humanist mono or plain sans for paragraphs on `/how` and popovers ≥3
sentences; keep pixel type for everything structural. Related, same panel:
the MEASURE readouts `Y BRIGHT 0.117` and `GAMUT ■ OK` are the rare labels
that break your own "labels are self-explanatory" rule — `ΔE2000` gets a
caption and a glossary underline; these two get nothing a newcomer can parse.

**10. Shareability stops at the OG card. (Shareability.)**
Evidence: per-planet OG images and strong descriptions exist ("Modelled
reflected-light colour: teal, #89d6f7. Derived from physics, not
photographed" — model OG copy, honestly). But on-page, the only export
affordances are designer-utility (`COPY ALL`, `CSS VARS`, `.ASE`). There's no
"share this planet" object for the 99% of visitors who will never open a .ase
file, and the census's **THE SPECTRUM OF WORLDS** stripe — one stripe per
planet, the whole catalogue as a single band of colour, the most poster-able
artifact on the site — has no export at all. One deploy risk while I'm here:
this build's `og:url` renders relative (`/planet/gj-581-b.html`) — confirm
`SITE_BASE_URL` is set in production or the cards degrade. Fix: a "share
card" button on planet pages (the OG PNG already exists — expose it), and a
downloadable/printable census stripe.

**11. The no-JS/loading first paint is raw.** Evidence: pre-hydration the
gallery shows unstyled controls and a bare "loading…". Minor — but for a
static site the first impression should never be the word "loading". A
CSS-only skeleton row of dimmed discs would keep the costume on.

## 4. What is already excellent — protect these

- **The honesty system as a design feature, not a disclaimer.** `MODELLED`
  chips, "a physics prediction, not a photograph" under every hero, the
  hatched `awaiting Roman` swatches, "Both are modelled predictions, not
  photographs." This is the site's moral spine and it is executed with more
  rigour than most journalism.
- **The Roman target board.** `0 COLOURS MEASURED` as a scoreboard is
  inspired — turning absence of data into suspense. "…which is exactly what
  makes the empty column worth watching" is the best line on the site. Also
  the refusal to guess ("The paper does not enumerate which ten… so this
  board does not guess").
- **The `Roman is blind here` hatched region** on the spectrum, and the ΔE
  readout phrased as `COLOUR LOST TO ROMAN'S 4 BANDS`. Instrument-truth
  turned into plain English inside the costume.
- **Solar-system anchors opening the grid.** Calibration-as-curation; Earth
  as stop 1 of *Start here*, with "If we had got Earth wrong…" — keep exactly
  as is.
- **The glossary underline system.** Site-wide, low-friction, honest about
  jargon; the intro even teaches it with a live example.
- **The 404 page.** "This page isn't on the chart", nearest-worlds readout,
  navigation console, `WARP · ON`. Charm with utility — and, as noted, the
  model for the missing footer.
- **THE LAMP.** Explaining illuminant physics as "the light this planet
  reflects" with a copyable star+planet duotone is the single cleverest
  dual-audience object on the site.
- **The worktree badge, ΔE-annotated `sun_swap` knob, per-planet OG
  descriptions** — the depth of finish in the details is what makes the
  structural gaps stand out.

## 5. The one move

**Put the thesis and the clock on the front door, and echo them at the bottom
of every page.** Concretely: (a) replace the closed-by-default intro with a
permanently visible two-line masthead — *"No telescope has ever photographed
an exoplanet in colour. These are the colours physics predicts — all 5,764
known worlds, checked against the five we could photograph."* — plus a live
`ROMAN LAUNCH · 26 DAYS →` chip; (b) add the 404's navigation console,
miniaturised, as the site-wide footer. This is one move because it's one idea
— *state the claim, then never strand the reader* — and it converts the
existing set of immaculate instruments into a produced experience. Everything
else in this review makes the site better; this is the thing that makes it
land. And the clock is running: the chip is worth ten times as much before 30
August as after.
