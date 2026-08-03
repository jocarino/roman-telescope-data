# Product review: why the website?

A whole-site design review, written 2026-08-03 against `origin/main` (release
`data-20260727-1038`, 5,764 planets). Reviewed by walking the built site at
1440px and at 390px: `/`, a planet page, `/how`, `/tours`, a tour, `/census`,
`/roman`, `/sky`, `/compare`, `/glossary`, `/404`.

This is a critique of **packaging, not substance**. The instrument is excellent.
It does not introduce itself.

---

## 1. The finding, in one paragraph

The site has a thesis. It never says it on the front door.

The three best sentences on the site all exist already, and all three are behind
a click:

- `/roman` — *"No exoplanet has ever had its visible colour measured. Every
  swatch below is a prediction — which is exactly what makes the empty column
  worth watching."*
- `/how` — *"No telescope has ever photographed these planets in colour — most
  have never been seen as more than a wobble in their star's light."*
- `/tours/start-here` — *"If we had got Earth wrong, nothing else here would be
  worth reading."*

Any one of those, on the landing page, answers "why the website." Instead the
landing opens `h1` → toolbar → 5,764-cell grid, and the only statement of
purpose is a tagline that describes *what it is* ("the colour scheme of every
known exoplanet, derived from physics") rather than *why anyone should care*.

**The thesis, stated plainly:** nobody has ever seen the colour of another
world; here are 5,764 physics-derived guesses; and a telescope launches in
weeks that could start checking them.

That is a claim with stakes, a deadline, and falsifiability. It is a far
stronger opening than a catalogue index.

---

## 2. What the numbers say (and don't)

From PostHog (`Exoplanets`, project 237022), last 30 days:

| metric | value |
| --- | --- |
| visitors | 6 |
| sessions | 7 |
| pageviews | 32 |
| avg session | 8m 41s |
| bounce rate | 28.6% |
| channel (90d) | 100% Direct — no search, no social, no referral |

Two honest conclusions:

1. **There is no behaviour to diagnose.** Nothing below is derived from
   analytics; it is a heuristic review. At n=6 it has to be.
2. **That is itself the finding.** An 8m41s median session and a 28% bounce say
   the few people who land engage *deeply* — the product is good. Zero
   non-direct traffic in 90 days says the premise is not legible from outside
   and the site gives nobody a reason to pass it on. The front door's problem is
   not conversion. It is that it doesn't earn arrival or sharing.

---

## 3. Findings, by product impact

### 3.1 The landing page has no lede — the "why" is hidden behind an ℹ

`gallery.html` opens with `x-data="{ intro: false }"`, so the intro panel is
closed on every visit including the first. When opened it is a five-row spec
sheet (Coverage / The colour / Two views / Honesty / Jargon) — a *reference
panel*, correct in content, wrong in job. It answers "what are the rules here"
for someone already committed. It does not make a stranger care.

`CLAUDE.md` prescribes ℹ buttons for "complex or easily-misread ideas." The
*premise* is not one of those. It is the one thing that must be unconditional.
Jargon on demand, thesis always.

### 3.2 The countdown is the site's single best asset, and it is three clicks deep

`/roman` carries a live launch clock (T-26 days as of writing, 30 Aug 2026) next
to the line *"0 colours measured · 23 slots awaiting."* That is a reason to
visit today, a reason to come back, and the most shareable thing on the site.

It reaches the visitor via: a 16px folded-map glyph → dropdown → "The Roman
target board." Nobody finds that.

*(Design consequence to plan for: the countdown needs a defined post-launch
state — "launched, commissioning" then "N targets observed, 0 measured" — or it
turns into a stale clock the day it matters most.)*

### 3.3 There is no site wrapper — seven microsites hung off one grid

Verified across every template:

- **No footer.** Anywhere. `grep -rn "<footer" web/templates` returns nothing.
- **No About, no credits page, no byline, no source link.**
- **No global nav.** Every non-gallery page's entire navigation is
  `back_link()` → "← ALL PLANETS". The Explore menu (tours, compare, census,
  sky, Roman) exists *only* on the gallery.

So `/how`, `/roman`, `/census`, `/sky` and every planet page are cul-de-sacs. A
visitor arriving on a shared planet link — which the OG-card work exists
specifically to encourage — has no way to learn that a sky map, a census, or a
launch countdown exist. They can go to the grid, or leave.

This is the largest single gap against "curated and cohesive," and the cheapest
to close.

### 3.4 The front door serves the visitor who already has a planet in mind

Search, colour filter, dice, sort, eight filter sections — every control on the
toolbar is an instrument for someone who arrived with a question. The one
concession to newcomers is the `NEW HERE?` strip: one 28px row of three tour
chips, competing with a 5,764-item grid immediately beneath it.

The curated default order (five solar-system anchors, then one planet per colour
family) is a genuinely good editorial decision — and it is invisible *as* a
decision. Nothing on the page says "we chose this order, and here's why." A
curation nobody is told about reads as arbitrary sorting.

### 3.5 Cohesion is visual, not rhythmic

The retro-instrument language is consistent and rare — the EXOSCOPE, the sky
receiver, the cockpit 404, the census panels all clearly belong to one object.
That part is done.

What's missing is *rhythm*. Every page opens at maximum intensity: full
controls, full data, full density, from the first pixel. There is no quiet
moment, no single hero image, no "look at this one thing" beat anywhere on the
site. Cohesion is not only consistency of parts; it is a controlled sequence of
loud and quiet. Currently it is flat-out throughout.

### 3.6 `/compare` is a cold, empty room

It loads as two empty slots, one line of instruction, and ~700px of black. It is
listed as a peer destination in Explore but has no default state and no
suggestion. Every other page on the site shows you something the moment it
loads.

### 3.7 Nothing is designed as the shareable moment

OG cards and a sitemap exist (good). But no surface in the UI says "this is
worth sending to someone." Palette export is designer-facing; the *colour
identity of a named world* is the thing a person forwards. 100% direct traffic
over 90 days is exactly what a site with no built-in reason to be passed on
looks like.

### 3.8 The name addresses one of the two audiences

"Exoplanet Palette" reads as a designer resource — swatches for your CSS. That
is a real use, and the `.ase` export supports it. But it undersells the actual
claim (*we computed what alien worlds look like, and we can show our work*).
`CLAUDE.md` makes dual-audience a hard requirement; the name currently speaks to
the designer and not to the curious.

---

## 4. What I would do

Reframe the landing from **catalogue index** to **claim → evidence → deadline**,
without losing the grid.

**A. A one-screen opening statement**, above the toolbar.
- The claim, unconditional: *Nobody has ever seen the colour of another world.*
- The move: *These are 5,764 physics predictions of what they'd look like.*
- The stake: the live countdown — *In 26 days, Roman launches. It could start
  checking them.*
- One primary action: **Start with the five we can check →** (the tour whose
  entire job is proving the method works against measured spectra).
- One secondary: **See all 5,764 ↓**, scrolling to the grid.

`gallery.html` calls vertical space above the grid "the most expensive on the
site." That is true for a returning visitor and exactly backwards for the ~100%
of traffic that is new.

**B. Let the returning visitor skip it.** Remember that the opening has been
seen (localStorage — the same mechanism filters and menu sections already use)
and collapse it to a single strip on later visits. Resolve the tension honestly
rather than by splitting the difference.

**C. A real footer, sitewide.** Identity, one line of what this is, the seven
destinations as named links, data credits (NASA Exoplanet Archive, Cahoy et al.,
PICASO), the honesty statement, source link. Highest cohesion-per-effort on this
list.

**D. A persistent minimal masthead.** The wordmark currently scrolls away
entirely — mid-grid there is no site identity on screen at all. Keep it, and
carry the Explore menu on *every* page so the other six destinations stop being
cul-de-sacs.

**E. Give `/compare` a default pair.** Preload two planets that make the point —
same colour, opposite physics. The "Two ways to be blue" tour already identifies
them.

**F. Name the editorial voice.** The curated order, the tour kickers and the
editor's notes are already the best writing on the site. Surface that layer: a
byline, an About, and one line under the curated grid saying what was chosen and
why.

**G. A permanent subtitle, not a rename.** Keep "Exoplanet Palette"; add the
thesis beneath it — e.g. *the colour of every known world, computed rather than
photographed.*

---

## 5. What not to touch

- **The retro instrument language.** Coherent, distinctive, and rare. It is the
  brand.
- **The honesty discipline.** Modelled vs measured, stated on every surface,
  never overclaimed. This is the site's moral spine *and* its differentiator
  against every "artist's impression" on the internet. Do not soften it to make
  the landing louder — the claim in §4A works *because* it is honest.
- **Jargon marks, the tour system, `/how`, the census, the sky map.** All strong.
  They need distribution, not redesign.

---

## 6. Suggested order of work

1. Footer + persistent masthead with Explore on every page (§4C, §4D) — turns
   seven microsites into one site.
2. Landing opening statement with the live countdown (§4A, §4B) — answers "why
   the website" on the front door.
3. `/compare` default pair (§4E) — removes the one dead room.
4. About / byline / curation note (§4F) and the subtitle (§4G).
5. Post-launch state for the countdown, before 30 Aug 2026.
