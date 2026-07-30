# Review — 01 Newsjacking

*Reviewed by: a wire-service breaking-news editor, twenty years on the desk. I have killed more copy for being fast than for being dull.*

## Verdict

**revise** — the tactics are sound and the honesty instinct is right, but the doc rests on a
lead-time claim that doesn't survive checking, and it has no answer for the case that comes up most
often: the planet in the news isn't in the catalogue.

## What's right

- **"Reply, don't post" is correct**, and most people get it wrong. A useful comment in someone
  else's thread beats your own post by an order of magnitude and carries no self-promo risk.
- **Tier 3, the dated note on the planet page**, is the best idea here and the most underweighted —
  the only part of a newsjack that still exists in six months.
- **The metric is right.** Fraction who open a second page, not visits. Nearly every plan I read
  measures the spike, the least informative number available.

## Gaps

**1. One hour is wrong in both directions, and the allocation was inverted.** The old runbook gave
10 minutes to Bluesky and 30 to Reddit/HN. Backwards. The reply to the announcing researcher has a
hard ~2-hour window and is where the relationship value is. The Reddit/HN thread usually doesn't
*exist* at minute 40 — those form when the aggregator layer picks the story up six to eighteen
hours later, and a comment on a four-comment thread is worth nothing. Meanwhile the page note, the
only durable artifact, sat under "later, if it's a big one" and should never be written fast. Now
three separate clocks. And *"if it takes longer than an hour it isn't worth doing"* is the exact
sentence that produces a wrong colour. Missing a story is free; being wrong on the day everyone is
reading is not. Removed.

**2. The three-question test measures us, not the story.** Two of three questions are about our
catalogue and our angle — that tells you whether you *can* post, never whether anyone will read it.
The desk test takes sixty seconds off the headline: is there a noun a civilian already owns
("habitable", "nearest", "first", "life", "water"); is there a picture; is a big press office behind
it; is it one named planet or a population result. Added as Test One, doc's questions demoted to
Test Two.

**3. The most common case got one bullet.** `pscomppars` holds **6,324 planets today**; the site
ships **5,764**. Some of that is deliberate filtering, but new confirmations are missing *by
construction* — the data is a dated offline release (`data-20260727-1038`) and `planets.json` isn't
even in the repo. On a "new planet discovered" story the default answer is "we can't". That's the
central design problem, not bullet 6 of a tool spec. Fix: a `pipeline build --planet "<name>"` fast
path, worth more than the watcher.

**4. The infrared case is most exoplanet headlines and got half a parenthesis.** "This tells us
nothing about visible colour" is a standing, ownable position, not a consolation prize — write it
once and keep it, because improvised at 23:40 it gets over-claimed. One boundary the doc would have
blown: optical *secondary-eclipse* photometry (TESS, CHEOPS, Kepler) does constrain geometric albedo
near 0.6–0.8 µm. "Infrared tells us nothing about colour" is defensible; "space telescopes tell us
nothing about colour" is the public correction you'd have earned.

**5. "Never email a journalist after publication" is one rule doing two jobs.** Never *pitch*, yes —
but a **correction** is the most welcome email a reporter gets, and it's how you stop being a
supplicant and become a source. Related: nothing said what happens when you're wrong. A correction
path isn't pessimism, it's the infrastructure that lets a desk move fast at all.

**6. `newswatch.py` polls fine and matches badly.** *Misses:* the name in the news isn't the name in
the archive — press writes `TRAPPIST-1e`, `K2-18b`, `HD189733b`, `Gliese 1214 b`, and `HD \d+`
requires a space popular coverage drops. Absent entirely: `HAT-P`, `HATS`, `KELT`, `KOI`, `NGTS`,
`MASCARA`, `TIC`, `Wolf`, `Ross`, `LP`, `HR 8799`, `beta Pic`, `51 Peg`, `2M1207`, `PSR B1257+12`,
`OGLE`/`MOA`/`KMT`, and the IAU NameExoWorlds names press loves (Dimidium, Osiris). Fix is a
normalised alias table from `pscomppars` + `ps`, not a better regex. *False alarms — the week-three
death:* `HD \d+` fires on every HD star in a stellar paper; `TOI-\d+` fires 200 times on one TESS
catalogue paper; `LHS`/`LTT`/`HIP` as written aren't anchored to digits. Today's astro-ph.EP feed
was 17 items of which **6 were `replace`** — with no `announce_type` filter every v2 re-alerts
forever — and most of the category is asteroids, disks and DART ejecta. A 40-line digest with two
useful lines is closed unread by day twenty. Fix: **three items a day, hard**, ranked by press-feed
presence first, plus **30-day suppression**. It must also print facts, not ready-to-post copy — doc
11 says a templated caption kills the account. And it needs `planets.json`, which isn't in the repo:
call `scripts/fetch_data.py` or fail loudly, not at 23:50.

## The accuracy checklist

Now in the doc. Five minutes; steps 1–2 are 80% of the value.

1. **Open the paper, not the press release.** Copy out its radius, mass, T_eq, host T_eff.
2. **Diff those four against ours.** >10% on radius/mass or >100 K on either temperature → our
   swatch used superseded numbers. Post the *change*, not the swatch — it's the better story.
3. **Read the provenance flag** (`model` / `model-microlensing` / `simulated-cgi` / `measured-cgi` /
   `measured-albedo`) and put it in the post text, not just on the page.
4. **Say the release date.** `data/RELEASE` is a snapshot. If it predates the paper, state it.
5. **Name the assumption you trust least** — cloud state, metallicity, phase angle. Can't name one?
   You don't know this planet well enough to post about it.
6. **State the wavelength the news is about.** Beyond ~1 µm the colour claim is independent of the
   news; say so, or you imply the result confirms your number.
7. **Sleep-on-it triggers:** contradicts the paper · says "habitable"/"not habitable" · names a
   person. Those wait until morning. The exceptions are always the ones that end careers.
8. **Write the correction before you post.** One pre-drafted sentence.

Then a 24-hour reminder to re-check the archive; reply to your own post if the colour moved.
Publicly correcting yourself is the cheapest credibility available.

## Wrong or unverified

All checked 2026-07-30.

- **"arXiv gives 1–3 days on the press cycle" — false in both directions.** Routine journal papers:
  preprint at acceptance, release at publication, often *weeks* apart. Embargoed or coordinated news
  (Nature/Science, NASA/ESA/ESO events, AAS press conferences): journalists are briefed *before* the
  paper is public. Worked example — the K2-18 b DMS paper (arXiv:2504.12267) was submitted
  16 Apr 2025 13:28 ET, inside the 14:00 ET cutoff, announced 20:00 ET that evening, press wave
  17 Apr. Hours, and that's the *good* case. Rewritten.
- **`rowupdate` is not a column in `pscomppars`** — TAP returns `ORA-00904: 'ROWUPDATE': invalid
  identifier`. It exists on `ps` only. Fixed.
- **The NASA Exoplanet Archive has no RSS feed** — email list only. Weekly updates land
  **Thursdays** (2, 9, 16 July 2026 all Thursdays), not the Wednesday some sources claim.
- **ESO's feed is `https://www.eso.org/public/news/feed/`** — the obvious guess
  (`/public/rss/news/en/`) 404s. Exact URLs now pinned for NASA, ESA and ESO, all resolved live.
- **arXiv's canonical host is `rss.arxiv.org`** (`export.arxiv.org` 301s, legacy). Announcements are
  20:00 ET **Sun–Thu only**; the feed regenerates at midnight ET and carries **one day** of items,
  so a missed poll is a lost day.
- **ESA's Space Science feed is live but slow** (latest item a week old) — keep, don't rely on.
  **Verified good:** aasnova.org, phys.org astronomy, universetoday.com, nasa.gov.
- **"Nobody else on Earth can do that"** is unfalsifiable — fine internally, keep it out of posts.

## Better approaches

1. **The pre-built bench (20 planets).** Obituaries are written before anyone dies. The headline set
   is small and knowable: the TRAPPIST-1 / K2-18 / LHS 1140 / Proxima / GJ 1214 / WASP-39 / 55 Cnc
   cluster, JWST cycle targets, `data/roman-targets.json`, and the AAS press-conference programme —
   published ~2 weeks ahead and the only *verified* lead time in this doc. Write it in daylight with
   the checklist done; the jack then costs five minutes.
2. **The one-planet fast path.** `pipeline build --planet "<name>"`. The only fix for the majority
   case. Build before the watcher.
3. **Own the standing counter-story.** "The picture on that article is an artist's guess, here's
   why" is the same argument every time. Publish it once and every jack is one link, no new claims,
   no new risk. Docs 10 and 11 already draft it; 01 should deliver it, not duplicate it.
4. **The watcher, scoped down** — press feeds first, three-item budget, facts not copy. One evening.
5. **The AAS meeting diary.** January is the year's densest exoplanet news day and it's on a
   calendar. A diary entry, not a tool.
6. **Rejected: racing bots to arXiv.** `@astrophep-bot` posts that firehose to 75 followers. Speed
   is not the moat. The colour is.

## The one thing I'd change

Stop selling this as a speed play. Speed is the part most likely to produce the one mistake that
costs the project its only real asset. Build the twenty-planet bench and the one-planet fast path,
and let the sixty-minute runbook shrink to the twenty minutes that genuinely have a clock on them.

## What I edited

In `01-newsjacking.md` — structure, `**Status:**` line and `## Links` preserved:

- **Feed table rewritten**: exact live URLs for NASA/ESA/ESO, canonical arXiv host, NASA Archive
  marked "no RSS · Thursdays · email list", press feeds promoted above arXiv. **Added the lead-time
  correction** (K2-18 b example + arXiv announcement mechanics), reframing arXiv as stock-building.
- **Added "stock beats speed"** to The bet (the twenty-planet bench) and a new section, **"The case
  the plan has to survive"** — the 6,324 vs 5,764 gap and the one-planet fast path.
- **Rewrote the `newswatch.py` spec**: alias table, `announce_type` filter, three-item budget,
  30-day suppression, facts-not-copy output, `planets.json` dependency.
- **Rewrote the runbook** as three clocks, deleting the "not worth doing over an hour" rule, and
  added **`## The accuracy checklist`** (8 items) plus the 24-hour re-check.
- **Rewrote the judging section** as Test One / Test Two; expanded the infrared case with the
  secondary-eclipse boundary; softened "never email a journalist" to "never pitch"; pointed the
  "being wrong, fast" risk at the new checklist.
