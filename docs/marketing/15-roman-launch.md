# The Roman launch play — be the colour reference before it flies

**Status:** not started · **Effort:** ongoing, front-loaded (3 urgent evenings, then light) · **Payoff:** highest ceiling in the plan · **Hub:** [Marketing plan](./README.md)

## The bet

Roman launches on **30 August 2026** — about four weeks from now — and its Coronagraph
Instrument will attempt the first direct image of a mature Jupiter in reflected visible light.
When that happens, every outlet on Earth needs to explain "what will Roman actually see", and
the honest answer is *a handful of photometric points in three bandpasses*, not a picture of a
planet. This site is already the only place that shows, planet by planet, exactly how much
colour identity survives that filter set — we built the answer before the question was asked.
The bet is that we get in front of the **CGI technology-demonstration** beat (early-to-mid 2027),
not launch week, and that we arrive there with a timestamped public prediction on record.

The hub currently says *"start 6 months early or don't bother."* That was written for the launch
beat and the launch beat is gone — four weeks is not six months. **The six months still exist for
the beat that actually matters.** Read the whole doc through that correction.

## The timeline

All dates below are sourced. Confidence stated honestly; do not treat the 2027 ones as firm.

| When | What | Confidence | Source |
|---|---|---|---|
| **30 Aug 2026, 07:26 EDT** | Launch. Falcon Heavy, LC-39A, Kennedy Space Center. | **High** — NASA's own countdown page carries the date and time. Florida weather in August routinely slips launches by days; treat the *date* as firm and the *day* as fluid. | [NASA Roman launch countdown](https://science.nasa.gov/mission/roman-space-telescope/roman-launch-countdown/), [SpacePolicyOnline, 2 Jun 2026](https://spacepolicyonline.com/news/nasa-sets-launch-date-for-roman-space-telescope/) |
| 25 Jul 2026 | Fuelling complete — 290 gal hydrazine loaded at KSC. Observatory is flight-ready. | High | [NASA Roman blog, 27 Jul 2026](https://science.nasa.gov/blogs/roman/2026/07/27/nasa-fuels-roman-space-telescope-for-late-august-launch/) |
| 29 Jul 2026 | Pre-launch virtual news conference (Domagal-Goldman, Townsend, McEnery, Perkins). | High — already happened; **watch the replay**, it sets launch-cycle talking points. | [NASA news release](https://www.nasa.gov/news-release/nasa-to-host-media-briefing-on-roman-telescope-launching-next-month/) |
| ~Sep–Nov 2026 | Cruise to Sun–Earth L2 + **~90 days commissioning**. | Medium-high | [Planetary Society, launch preview](https://www.planetary.org/articles/the-nancy-grace-roman-space-telescope-launch-what-to-expect) |
| **Early 2027** | Science operations begin. | Medium | Same |
| **~2027, within the first 18 months** | **CGI technology demonstration: 90 days / 2,200 hours of observing.** Community planning documents assumed a window roughly Jan–Jul 2027 *based on an October 2026 launch*; the real launch is six weeks earlier, so this may move earlier, but nothing official restates it. | **Low-medium — this is the honest gap.** No published date for first CGI observations. | [Roman Coronagraph Primer, CPP, Jan 2025](https://roman.ipac.caltech.edu/docs/RomanCoronagraphPrimer_Current.pdf); [Wolff et al. 2024, CPP observation planning](https://arxiv.org/abs/2411.17868) |

**The single most important scheduling fact:** the Primer states **"No proprietary period: Roman
data will be made immediately available."** When CGI observes a planet, we can run it through the
pipeline the same week. That is the entire follow-up story, and it costs nothing to be ready for.

**The political backdrop, because it's a recurring beat.** The White House proposed cancelling
Roman four times between 2018 and 2025, most recently in the April 2025 OMB passback that would
have cut NASA astrophysics from ~$1.5B to under $500M. Congress blocked it each time; a
$24.4B NASA budget passed in January 2026 explicitly protected Roman as *"ahead of schedule and
under budget."* ([SpaceNews](https://spacenews.com/white-house-proposal-would-slash-nasa-science-budget-and-cancel-major-missions/),
[Scientific American](https://www.scientificamerican.com/article/nasas-next-major-space-telescope-is-ready-to-launch-trump-wants-to-kill-it/))
This cycle will return with the FY2028 request, likely spring 2027 — right on top of the tech demo.

### The correction we have to make first (blocking, and it's an asset)

Our `pipeline/config.py` models CGI as **four** top-hats: 575 nm/10%, 660 nm/6%, 730 nm/6%,
835 nm/15%. The January 2025 CPP flight Primer's mode table says otherwise:

| Band | Centre | Width | Mode | Mask | Support |
|---|---|---|---|---|---|
| 1 | 575 nm | 10% | Narrow-FoV imaging | Hybrid Lyot | **Required** (imaging); best effort (polarimetry) |
| 1 | 575 nm | 10% | Wide-FoV imaging | Shaped Pupil | Best effort |
| 3 | **730 nm** | **15%** | Slit + R~50 prism spectroscopy | Shaped Pupil | Best effort |
| 4 | **825 nm** | **10%** | Wide-FoV imaging | Shaped Pupil | Best effort |

Three differences that matter: **Band 2 at 660 nm is not in the flight configuration at all**;
Band 3 is 15% wide, not 6%; Band 4 is 825 nm at 10%, not 835 nm at 15%. And the sentence
underneath the table is the real story:

> *"only observations in Band 1 with the hybrid Lyot coronagraph are formally supported; all
> other modes listed in the table below will be supported on a 'best effort' basis."*

The **only guaranteed CGI deliverable is one 10%-wide photometric point at 575 nm.** One number.
Not four. Fixing the config is a data-side evening. But the framing this unlocks is the best
editorial angle the project has ever had, and nobody else is saying it:

> **Roman's guaranteed output is a single brightness measurement per planet. Everything past
> that is best-effort. Here is exactly what one number, then two, then three, buys you — and
> what it doesn't.**

That is honest, it is *interesting*, it is a genuine public-understanding contribution, and it is
the pitch. Every hype piece will show an artist's render. We show the actual information budget.

## The news beats

Six distinct beats, each a separate content opportunity. Effort ratings assume the pre-written
assets from the runbook already exist.

1. **Pre-launch (now – 29 Aug).** Crowded and we're late — but it's where the *predictions* must
   land, because a prediction published after launch is worthless. **Highest urgency, lowest glamour.**
2. **Launch day, 30 Aug.** Enormous volume, near-zero differentiation. Do not try to win it. One
   good Bluesky post, one Reddit reply. See [01-newsjacking.md](./01-newsjacking.md) — reply, don't post.
3. **First light / first Wide Field Instrument images (~Nov 2026–Jan 2027).** Wide-audience, but
   WFI is survey imagery and *not about colour*. Our honest contribution is small: "this is
   beautiful and it is not what CGI does." One post.
4. **First CGI image (2027, date unknown). ← this is the beat.** The one moment where "what
   colour is that planet" is literally the headline. Everything else here is preparation for it.
5. **Tech-demo results / first CGI spectrum (2027).** If Band 3's R~50 spectroscopy is commissioned
   on a real planet, that's the first visible-light spectrum of a mature exoplanet ever taken, and
   we can put it beside our modelled one. The strongest possible outcome for this project.
6. **The budget cycle (recurring, next ~spring 2027).** "Roman threatened again" stories need a
   *what we'd lose* illustration; our Roman-view gallery is exactly that. Reusable, and it reaches
   policy journalists ([Jeff Foust](https://spacenews.com/author/jfoust/) at SpaceNews, Marcia Smith
   at SpacePolicyOnline) — a different audience from the science desk.

## What to own before then

When a journalist or a curious reader types the question, we should already be the answer. This is
[03-seo-planet-pages.md](./03-seo-planet-pages.md) mechanics pointed at one topic.

**Queries to rank for**, roughly by value-per-effort:

- `what will Roman actually see` / `what will the Roman telescope see`
- `can Roman photograph exoplanets` / `will Roman take pictures of exoplanets`
- `Roman Coronagraph colours` / `Roman coronagraph bands` / `Roman CGI bandpasses`
- `what colour are exoplanets` — the biggest evergreen term, and we should already own it
- `first direct image of a Jupiter in reflected light`
- `Roman coronagraph 575 nm` — small volume, but whoever searches it is exactly our reader

**Pages to publish, in order:**

| Page | By when | Why |
|---|---|---|
| `/roman/what-roman-can-see` — the explainer | **by 20 Aug** | The anchor. Everything links here. |
| `/roman/predictions` — the pre-registration | **by 25 Aug, hard deadline** | Worthless if published after launch. |
| `/roman` target board — already exists, needs a launch-status header | by 25 Aug | The namesake page should not look dormant on launch day. |
| `/roman/status` — countdown / live mission state | by 28 Aug | Cheap, and it's what people bookmark. |
| Band-model correction shipped in data | before either of the above | Publishing predictions against a wrong band model is the one unrecoverable error here. |

Every planet page should already carry a one-line Roman verdict — *"Roman would see this planet
as [hex], ΔE2000 = 12 from its true colour"* — which is presumably live; if not it outranks
everything else on this list.

## What to build

Ranked by payoff ÷ evenings. The first three are the plan; the rest are nice.

1. **Fix the band model to the flight Primer table.** Half an evening, data-side. *Blocking
   everything.* Ship a visible changelog note saying we corrected it against the CPP Primer —
   "we found our own error and fixed it" is a credibility asset, not an embarrassment.
2. **`/roman/what-roman-can-see` — the explainer.** One evening. The information-budget argument
   above, made visually: the same planet rendered from the full spectrum, then from three bands,
   then from **Band 1 alone**. Interactive if cheap, static if not. This page is the whole pitch
   and it is the thing you send journalists.
3. **The pre-registered predictions.** Two evenings. Spec below. Do it before 25 August.
4. **"Band 1 only" mode.** Half an evening once (2) exists — a toggle that collapses the Roman
   view to the single required 575 nm measurement. It's the honest floor, and visually it is
   *devastating*: a grey disc. Best single screenshot the project can produce.
5. **`/roman/status`.** One evening. Launch countdown → then "in commissioning" → then "CGI tech
   demo: not yet begun" → then, when data lands, the comparison. A page that stays correct for
   two years with a JSON edit, and it's the natural bookmark.
6. **Same-week turnaround kit for real CGI data.** Half an evening of scaffolding: a script and a
   page template that takes CGI photometry and drops it beside our prediction. Because there's no
   proprietary period, whoever publishes the comparison first owns the story, and that can be us
   by a wide margin — but only if it isn't authored under time pressure.
7. **Colour-uncertainty bars.** Real CGI points come with error bars; our reconstruction should
   propagate them. Do this *before* comparing to real data, not after someone points it out.
8. *(Skip)* A live CGI data feed. Over-engineered for a beat that fires twice.

## The pre-registered predictions play

**Verdict: yes, do it, and it is the highest-leverage thing in this document.** It costs two
evenings, requires no permission, no budget and no relationships, and it manufactures a guaranteed
future news hook out of work already done. It is also just good practice — the difference between
a model and a horoscope is whether it was written down first.

**Targets.** Selection constraints are published: host star **V ≤ 5**, stellar angular diameter
**< 2 mas** (Primer, Targets section); the CPP target database is public at
[plandb.sioslab.com](https://plandb.sioslab.com). Predict for roughly 10–20 planets:

- Everything in the CPP database meeting the V ≤ 5 / <2 mas cuts that we already have a colour for.
- The repeatedly named candidates: **47 UMa b/c** (used as *the* target in the Roman Exoplanet
  Imaging Data Challenge), **ε Eridani b** (the nearest Jupiter analog; see
  [Sanghi et al. 2026, *Worlds Next Door III*](https://arxiv.org/abs/2602.23423), which argues for
  metal enrichment and/or water-ice clouds — a directly testable albedo statement), **upsilon And d**,
  and **HIP 71618 B** ([arXiv:2512.02126](https://arxiv.org/abs/2512.02126), explicitly proposed as
  "suitable for the Roman Coronagraph Technology Demonstration").
- Deliberately include a few we expect to get *wrong*. A prediction set with no risk isn't one.

**What to predict, per target.** Full-spectrum hex; Band 1-only value; three-band reconstructed
hex; ΔE2000 between full and reconstructed; predicted geometric albedo in each flight band with
uncertainty; and the model assumptions stated inline (cloud state, metallicity, phase angle —
quadrature, per `pipeline/config.py`). Plus one paragraph of **what would falsify this**.

**How to timestamp credibly**, cheapest-first — do all three, it's twenty minutes:

1. **Git tag + signed commit.** `git tag -s roman-predictions-2026-08 -m "..."`, pushed to a public
   remote. Free, instant, verifiable, and honestly sufficient for most readers.
2. **Zenodo DOI.** Turn on the GitHub–Zenodo integration and cut a release; Zenodo mints a DOI and
   archives the exact artefact. Free, no gatekeeping, permanent, and citable — which is what makes
   a scientist willing to link to it. **This is the one that matters.** Deposit the prediction
   JSON/CSV, not just a web page.
3. **arXiv note.** Genuinely valuable if it lands — but astro-ph submissions require **endorsement**
   for first-time submitters, which is a relationship you don't have yet and can't get in four
   weeks. **Don't block on it.** Revisit after the CGI beat, when a co-author is plausible.

**How to present it.** `/roman/predictions` as a plain, dated, near-severe page: the table, the
DOI, the falsification paragraph, the assumptions, no marketing language whatsoever. The
restraint *is* the rhetoric. Link the Zenodo DOI above the fold. Then never touch it — corrections
go in a dated addendum below, never as an edit.

**The follow-up.** When CGI photometry lands: publish `/roman/predictions/results` within a week.
Score every target — the hits *and* the misses, misses first. If we were wrong, say how wrong and
why, in numbers. A project that publicly grades its own wrong predictions is more credible than
one that only reports hits, and it's a better story. Then email everyone in the next section with
one line: *"we published these before launch; here's how they did."* That email writes itself and
it is the single most pitchable thing this project will ever send.

## Who to know before it matters

Four weeks is not enough time to build a relationship. It *is* enough to make one useful, honest
contact who remembers your name in 2027. Aim for two or three, not twenty.

**Roman / NASA communications** (public press contacts, entirely appropriate to email):

- **Claire Andreoli** — Roman Communications Lead, GSFC — `claire.andreoli@nasa.gov`
- **Ashley Balzer** — Roman Science Writer, GSFC — `ashley.m.balzer@nasa.gov`. *The best single
  contact here.* She writes the Roman explainers; a physics-derived colour tool is a resource for
  her, not a favour to you.
- **Rob Garner** — GSFC media — `rob.garner@nasa.gov` · **Courtney Lee** — Roman social media lead
- Follow **@NASARoman** and **@NASAUniverse**; NASA social accounts do repost good third-party work.

**The CGI / Community Participation Program** — the people who will actually take the data.
Contacts published in the Primer:

- **Vanessa Bailey** (JPL, Coronagraph Technology Center) & **Maxwell Millar-Blanchaer** (UCSB) —
  CPP co-chairs — `cpp-co-chairs@jpl.nasa.gov`
- **Alexandra Greenbaum** (IPAC / Science Support Center) — `azg@ipac.caltech.edu`
- **Julien Girard** (STScI / Science Operations Center) — `jgirard@stsci.edu`. Runs the Roman
  Exoplanet Imaging Data Challenge — closest thing to a natural ally for this project.
- **Schuyler Wolff** (Arizona) — CPP Observation Planning — `sgwolff@arizona.edu`
- **Aniket Sanghi** (Caltech) — lead author on the 2026 ε Eri b albedo paper; if we predict ε Eri b
  we are citing his work, and [13-credit-the-scientists.md](./13-credit-the-scientists.md) says tell him.

**The one email to send, before launch.** Short, to Balzer and/or the CPP co-chairs. Not a pitch —
a correction disclosure, which is the only cold email scientists reliably answer:

> Subject: Roman CGI band model — a correction, and a public prediction set
>
> I maintain <SITE_URL>, which computes a colour for every known exoplanet from albedo models and
> host-star spectra, and shows each one as reconstructed from the CGI bandpasses. I had the flight
> configuration wrong — I'd modelled a 660 nm band and 6% spectroscopy widths; I've corrected it
> to the Jan 2025 CPP Primer table (Band 1 575/10%, Band 3 730/15%, Band 4 825/10%), and the site
> now states plainly that only Band 1 HLC imaging is a formal requirement.
>
> Before launch I'm publishing timestamped predicted colours for likely tech-demo targets (Zenodo
> DOI), so they can be checked against real data later. Two questions, if you have a minute:
> is the Primer table still current, and is there anything in the framing that's misleading?
> Happy to fix anything wrong, and happy to be told this isn't useful.

That email asks for correction rather than coverage, discloses an error, and hands them a citable
artefact. Send it once. Do not follow up twice.

**Journalists.** Verify current beats before emailing — mastheads move, and a stale contact reads
as spam. Ones I'd expect on the Roman/exoplanet story, with confidence flagged:

- **Nadia Drake** — freelance, frequently Scientific American; long exoplanet track record. *Confident.*
- **Jonathan O'Callaghan** — freelance (Sci Am, New Scientist, NYT); exoplanets and telescopes. *Confident.*
- **Jeff Foust** (SpaceNews) and **Marcia Smith** (SpacePolicyOnline) — the *budget* beat, not the
  science one. Different pitch entirely. *Confident.*
- **Lisa Grossman** (Science News), **Ashley Strickland** (CNN), **Katrina Miller / Kenneth Chang**
  (NYT), **Robin George Andrews** (freelance), **Phil Plait** (*Bad Astronomy* newsletter — an
  independent writer who links tools like this, and the lowest-friction of the lot).
  *Less certain on current assignments — check before sending.*
- **Missed:** the NASA Social program (50 digital creators at KSC for launch) closed applications
  28 June 2026. Note it for the next NASA launch; it's a genuinely good fit for this project.

Pitch mechanics, the press kit, and the boilerplate all live in [02-press-kit.md](./02-press-kit.md) —
that doc is a **prerequisite** for any of the above and should be done first.

## Launch-week runbook

The point of a runbook is that launch week contains no writing. Everything below is drafted,
proofread and queued **by Wednesday 26 August**.

**By 20 Aug** — band-model fix shipped · explainer page live · press kit done.
**By 25 Aug** — predictions page live, git-tagged, Zenodo DOI minted · the CPP/Balzer email sent.
**By 26 Aug** — everything in the queue below written and scheduled. Nothing authored after this.

Pre-written and sitting in a folder:

- Three Bluesky/Mastodon posts (launch success · scrub · delay) — see [11-bluesky-mastodon.md](./11-bluesky-mastodon.md)
- One Reddit *comment* (not a post) for the inevitable r/space launch thread
- One "what CGI actually does" thread, 4 posts, with the Band-1-only image
- A `/roman/status` state-flip that's a one-line JSON edit

**Sat 29 Aug** — Post the predictions once, quietly, framed as *"published before launch so it can
be checked after"*. Not as a launch post. Queue everything else. Charge the laptop.

**Sun 30 Aug (launch, 07:26 EDT / 12:26 BST)**
- *T-2h*: watch nasa.gov/live. Nothing to do.
- *T+0 to T+1h*: **do not post during the launch itself.** Everyone is posting. You will be noise.
- *T+2h, once separation is confirmed*: one post. The Roman-view gallery image, and one line —
  *"It's up. Here's what its coronagraph will and won't be able to tell us about colour: <link>."*
  Tagged `utm_campaign=roman-launch`.
- *T+3 to T+6h*: find the r/space and Hacker News threads. One substantive comment each, caveat
  first. This is where the actual traffic comes from — 60-minute runbook in
  [01-newsjacking.md](./01-newsjacking.md).
- *Evening*: nothing. Resist the second post.

**Mon 31 Aug – Fri 4 Sep** — Post the "what CGI actually does" thread on Tuesday, once launch noise
clears and the explainer pieces are being written; it lands better than anything on Sunday. Reply
to anyone who engaged. Log everything in [99-tracking.md](./99-tracking.md).

**If it scrubs:** post nothing but the pre-written scrub line. Re-queue. A scrub costs one day; a
panicked improvised post costs credibility.

## The fallback

Say it plainly: **this plan does not depend on Roman succeeding.**

- **Launch slips days-to-weeks (likely — it's Florida in August).** Zero impact. Re-queue the
  posts. The predictions are already timestamped.
- **Launch fails.** The site becomes a small memorial to what we were going to be able to see.
  Post nothing for several days. Then, if anything, the honest version: this is what CGI would
  have measured. Do not newsjack a launch failure in the first week.
- **CGI is never commissioned, or misses its L1 requirement.** Perfectly plausible — it is a
  *technology demonstration*, failure is a permitted outcome, and only one mode is even formally
  required. Our explainer becomes *more* accurate, not less: we were the ones saying the
  guaranteed deliverable was one number. The predictions page stands as "not yet testable."
  No credibility is lost by anyone who read what we actually wrote.
- **CGI works but observes zero planets we predicted.** Likely — target selection is still open.
  Mitigate by predicting broadly (every V ≤ 5, <2 mas host we can colour) and publishing the
  *method*, so any new target runs in an hour. The follow-up becomes "here's the target they
  picked, computed today, against our method from a year ago."
- **Roman is cancelled or descoped by the FY2028 request.** Beat 6 fires instead of beat 4: pitch
  the policy desk, and the gallery illustrates what's being given up. Different story, same asset.

The only genuinely wasted effort in this document is the two evenings on predictions, and only if
CGI never observes anything at all. That's an acceptable downside.

## How we'll know it worked

Tag everything `utm_campaign=roman-launch` (pre-launch and launch week) or
`utm_campaign=roman-cgi` (the 2027 tech-demo beat), with `utm_source=<where>` and
`utm_medium=social|reddit|hn|email|press`. Conventions in [99-tracking.md](./99-tracking.md).

**Pre-launch (by 30 Aug) — the only targets that matter now:**
- Band model corrected and shipped. Binary. **This is the real success metric for August.**
- Predictions page live with a resolvable Zenodo DOI before launch. Binary.
- ≥1 substantive reply from a NASA/CPP contact. Even "thanks, no" counts — it means the name landed.

**Launch week:**
- Not raw visits. **The share of arrivals that open a second page**, same as
  [01-newsjacking.md](./01-newsjacking.md). A launch-day spike that all bounces taught us nothing.
- Visits to `/roman/what-roman-can-see` as a fraction of total. If people arrive and *don't* read
  the explainer, the framing is wrong, not the traffic.
- Any inbound link from a NASA, JPL, IPAC, STScI or `.edu` domain. One is worth ten thousand visits.

**The 2027 beat — what we're actually playing for:**
- The predictions-vs-reality page is published within **7 days** of CGI data becoming public.
- ≥1 journalist cites the prediction set, or ≥1 CGI team member links it.
- The Zenodo DOI accrues a citation. Long shot; it's the ceiling.

## Risks

- **Publishing predictions against the wrong band model.** The one unrecoverable error in this
  plan, and we are *currently in it*. Fix `pipeline/config.py` before anything else ships.
- **Overclaiming what CGI delivers.** The failure mode is drifting into "Roman will photograph
  exoplanets in colour" because it gets clicks. It won't, and saying so is our entire position.
  Every Roman post must contain the limitation *before* the picture.
- **Being wrong in public with a DOI on it.** That's the deal. Mitigate with explicit uncertainty,
  a falsification paragraph, and grading our own misses first — not by hedging into
  meaninglessness. An unfalsifiable prediction is worth nothing.
- **The 2027 date is soft.** Build the turnaround kit now, then genuinely put it down. One calendar
  reminder for **January 2027**; do not check CGI news weekly for a year.
- **Burnout on a four-week sprint.** Three evenings before 25 August is the whole pre-launch ask.
  If only one is available, spend it on the band-model fix; the rest can slip to the 2027 beat,
  which was always the one that mattered.
- **Emailing scientists cold.** Low risk if it leads with a correction and an offer to be told
  you're wrong; high risk if it reads as a coverage request. Send one, not five.

## Links

- [README.md](./README.md) — the hub. Its "start 6 months early" note needs updating to the correction at the top of this doc.
- [02-press-kit.md](./02-press-kit.md) — **prerequisite.** No journalist or NASA contact gets emailed before this exists.
- [01-newsjacking.md](./01-newsjacking.md) — launch day is one big newsjack; the 60-minute runbook and reply-don't-post rule apply exactly.
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — **blocking.** The CPP and CGI papers cited here must be credited on the site before we email any of their authors.
- [03-seo-planet-pages.md](./03-seo-planet-pages.md) — the mechanics behind "what to own before then".
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — where the queued launch-week posts go.
- [09-show-hn.md](./09-show-hn.md) — do **not** spend the one Show HN shot on launch week; hold it for the CGI beat or fire it well before.
- [06-open-data.md](./06-open-data.md) — the Zenodo deposit is the same machinery; do them together.
- [05-machine-readable.md](./05-machine-readable.md) — the prediction set should ship as machine-readable data, not only a web page.
- [99-tracking.md](./99-tracking.md) — UTM conventions and the second-page-depth metric.
