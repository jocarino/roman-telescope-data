# Review — 99 Tracking

*Reviewed by an analytics engineer with a standing grudge against vanity metrics and unread dashboards.*

## Verdict

**Right instinct, wrong instrument, and it does not currently work at all.** Refusing to optimise for visits is the best decision in the plan; but depth-as-written is device-confounded and statistically dead at this sample size, and PostHog has never received a single event from this site.

## Is "depth" the right metric?

The reasoning is correct — visits reward the bouncing spike, and "did anyone *do* anything" beats "how many arrived". Keep the reasoning. The implementation — *fraction of a source's sessions that opened ≥2 planet pages* — fails on five counts, in descending order of damage.

**1. The gallery is the product, and it is one pageview.** `app.js` builds the grid with infinite scroll (`_batch: 60` + `IntersectionObserver`). Someone who scrolls 800 swatches, filters to hot Jupiters and searches three names generates **one `$pageview` and zero events** — filter, search and sort fire nothing. Depth scores them 0. For the design half of the audience the gallery *is* the artifact, so the metric is blind to the visit the site is best at.

**2. Hold-to-peek is invisible.** `fragments/peek.html` is `fetch`ed by `app.js` (`data-peek` → `/fragments/peek/<id>.html`) on a ~450 ms press-and-hold: no navigation, no pageview, no event. A visitor who peeks fifteen planets and opens one scores 0 while being the most engaged person that day. Long-press is a phone gesture; desktop users open tabs, which *does* register. So depth under-reads mobile and over-reads desktop — and the channels differ sharply by device (Reddit and Bluesky arrive in phone in-app browsers; HN and newsletters on desktop). **You would be ranking channels partly by the device mix of their audience.**

**3. n=40 cannot be ranked.** At p=0.35 a 40-session channel has a 95% interval of roughly **20%–50%**; distinguishing 35% from 50% at conventional power needs **~175 sessions per channel**, which most channels won't clear in eight weeks. Ranking ten channels on a noisy proportion and then *dropping eight* is exactly the "optimise confidently for a number that meant nothing" failure — worse than not measuring, because the ranking looks authoritative.

**4. The good single-page visit scores zero.** Someone who reads one planet page thoroughly and bookmarks it is the best outcome available. Depth = 0 — and cookieless makes the return unobservable, so it scores zero twice.

**5. Cookieless sessions aren't the clean denominator assumed.** The doc says depth is safe because it's within-session. Sessions derive from `hash(team_id, daily_salt, ip, user_agent, hostname)`, so two people behind one NAT on the same browser version **collapse into one session** — the normal case for mobile carrier CGNAT, universities and offices. That merges strangers into one deep session and *inflates* depth for exactly the mobile sources it under-reads in (2). The errors don't cancel; they make the number unfalsifiable.

**Ruling: replace it.** Keep the intent, drop the proxy:

> **"Turned a knob" — fraction of a source's sessions firing at least one deliberate interaction:** `roman_view_toggled`, `phase_changed`, `light_source_swapped`, `palette_copied`, `palette_downloaded`, or a second `planet_viewed`.

It is a **union, not a single behaviour**, so it catches the designer (copied a palette), the astronomer (Roman toggle) and the browser (two planets) without forcing all three into one browsing style. All six events **already exist in the code** — zero new instrumentation. It is far less device-confounded: turning a knob is a tap on a phone and a click on a desktop. And those knobs only make sense to someone who understood the site's claim, which is the actual question. Keep planet-pages-per-session as a secondary diagnostic, reported as a **median** — a ≥2 threshold throws away the difference between 2 planets and 40.

**One bias that distorts any rate metric:** PostHog is blocked by every mainstream list, and `analytics.js` fails silently by design (correct). HN and r/dataisbeautiful readers block at far higher rates than newsletter readers, so comparing them on a *rate* compares a denominator missing its most technical third against a nearly complete one. Largest single bias in the scheme; unmentioned.

## What cookieless silently breaks

- **Returning visitors: not measurable — not "where measurable", not at all.** The salt rotates daily and is deleted; the same person on two days is two people, permanently. Retention and lifecycle insights will render and mean nothing. Delete the metric rather than leave it aspirational.
- **Cross-device attribution: gone.** No `identify()` runs, so phone-then-laptop is two strangers.
- **Geography: gone, and not in the doc.** Under `cookieless_mode: "always"` the IP is consumed by the hash and discarded — no country/city, empty world map. Relevant to the educator channel.
- **Bounce rate is actively wrong here.** `analytics.js` sets `autocapture: false` and never sets `capture_pageleave`. Session duration is first-to-last event, so a single-pageview session has duration 0 and is classified a bounce — *whether they left in four seconds or read for four minutes*. The doc's central story ("HN bounces, newsletters read three pages") cannot currently be told from the data. Side benefit of the knob metric: a `phase_changed` at t=90s gives that session a real duration.
- **No person profiles exist.** `person_profiles: "identified_only"` plus zero `identify()` calls means `$initial_utm_source` is never created. Source breakdowns must come off the **sessions** table (`$entry_utm_source`), so "depth by source" is a **HogQL query**, not a dropdown — thirty minutes of SQL, not three clicks.

## UTM reality

The convention is good and the granularity call (`reddit-space`, not `reddit`) is right. The gaps are all about what happens after the click.

- **The successful case poisons its own attribution.** When something works, people copy the URL from the address bar — *including the UTM*. A visitor arriving via `utm_source=bluesky` who reposts to HN files every HN click as Bluesky. This only happens when you're winning. **Fix (one line, not done here): `history.replaceState` the `utm_*` params off after PostHog's pageview fires.**
- **The site already strips query strings — possibly too early.** `sky.js:691` and `app.js:1187` call `history.replaceState(..., location.pathname)`. PostHog loads via the async `array.js` stub, so the real bundle arrives *after* those handlers can run; on `/sky` and `/compare` the UTM may be gone before capture. `/sky.html?planet=<id>` is the deep link the plan most wants shared. Five-minute network-tab check before launch; fix is to preserve `utm_*` in those two calls.
- **Mastodon is referrer-blind** (`rel="noopener noreferrer"` in most clients), as are in-app browsers. And `09-show-hn.md` deliberately ships the submitted URL untagged — correct, HN readers notice — which makes the biggest planned spike **referrer-only by choice**.
- **So: referrer first, UTM second — the doc has this backwards.** Referrer is what you actually have for HN and it survives re-sharing honestly; UTM is the tiebreaker for referrer-eating sources.
- **Never read "direct" as "nobody".** It's a known mixture: Mastodon, in-app browsers, iOS Mail, copy-pastes, ad-blocked visitors' neighbours. Read it by **timestamp join** — a direct spike within two hours of a logged post *is* that post. This is what makes the activity log load-bearing.

## Is this measurable at all?

Read `analytics.js`, `base.html`, `build.py`, `app.js`, `tours.js`, `nginx.conf`, `Dockerfile`; queried the PostHog project.

- **Nothing has ever been ingested.** The project taxonomy contains only PostHog built-ins — no `planet_viewed`, no `palette_copied`, no `roman_view_toggled`. Either `POSTHOG_KEY` (a `Dockerfile` `ARG`) is unset on Dokploy, or **"Cookieless server hash mode" is off in project settings, in which case every event is dropped silently with no error** — `analytics.js` warns about exactly this. There is no partial failure mode, only zero.
- **Works once the key is on:** `$pageview` everywhere (real multi-page site, no router), `planet_viewed` with id and name, `palette_downloaded`, `palette_copied`, `roman_view_toggled` (with `surface: gallery|planet`), `light_source_swapped`, `phase_changed` (debounced 800 ms — good call). A well-chosen, small vocabulary; no autocapture, replay or heatmaps, which is right for this site and consistent with the "not surveillance-shaped" principle. **`/roman` visits: collectable**, as the doc says.
- **Tour completions: NOT collectable.** `tours.js` contains **zero** `exoTrack` calls — only a `#stop-N` `replaceState`. You see a tour started and nothing after. The doc lists completions as a metric; today it is fiction.
- **Access logs: not durable.** `05-machine-readable.md` promises `/llms.txt` and `/api/*` hits "in the access logs". `nginx.conf` sets no `access_log`, so it goes to container stdout and dies with the container. Ship logs somewhere or drop the claim.
- **Uninstrumented:** gallery search/filter/sort, peek, `/census`, `/compare`, `/sky` interactions.

## Gaps

- No preflight that analytics is alive — and it is not. No minimum-sample rule, so the 8-week ranking will rank noise. No stated fallback attribution and no guidance for reading "direct".
- Ad-blocker bias unmentioned, though it distorts the HN-vs-newsletter comparison the exercise exists to make. No definition of a session boundary, though cookieless changes it.
- Two docs promise metrics that don't exist: tour completions (99) and access-log hits (05). `10-reddit.md`'s "Roman toggle used in >30% of sessions" is the one channel metric correctly specified against a real event — make it the template.

## Better approaches

Ranked; all fits one evening. Stop after 1–3 if the evening is short.

1. **Preflight (15 min, blocks everything).** Set `POSTHOG_KEY` on Dokploy, tick *Cookieless server hash mode*, deploy, load a planet page, confirm `planet_viewed` in the Live tab. Until this passes, every number in the plan is zero.
2. **Switch the headline to "turned a knob" (30 min).** One HogQL query joining events to `sessions` on `$session_id`, grouped by `$entry_utm_source` with `$entry_referring_domain` as fallback. One saved insight, zero code changes.
3. **Replace the markdown log with PostHog annotations (20 min).** See below.
4. **Add the sample-size gate (5 min).** Below ~200 sessions report the **absolute count** of knob-turns, never a rate. "r/dataisbeautiful: 14 palette copies; Bluesky: 3" is decision-grade and needs no denominator, no session stitching and no cookieless assumptions. Rates only above 200.
5. **Later, two events (20 min of code, out of scope here):** `tour_completed` in `tours.js`, and `peek_opened` on the hold-to-peek fetch. The second closes the biggest blind spot on the site.
6. **Strip `utm_*` after the pageview**, and preserve them in the `/sky` and `/compare` `replaceState` calls — kills attribution laundering and the deep-link race together.

## The one thing I'd change

**Kill the hand-maintained `activity-log.md`; make the log a PostHog annotation instead.**

It will not survive. One person, evenings and weekends, backfilling a "result after 7 days" column for something they did last Tuesday — that dies at row six, and the newsjack tool meant to auto-append it isn't built. But the log matters *more* than the doc realises: because cookieless destroys returning visitors, Mastodon eats referrers, HN ships untagged on purpose and ad blockers eat a biased slice, **the dated record of what you did is the strongest attribution signal you have.** Most real attribution here will be "spike at 19:40 on the 12th; posted to r/space at 19:30".

Annotations are that log, stored where it gets used. One API call or four clicks. They draw a vertical line **on every chart you already open**, so the log is consumed passively at the moment it's relevant instead of requiring you to remember a second file exists. Nothing to reconcile, and it cannot drift from the data. Keep the markdown file for the one thing annotations are bad at — the qualitative post-mortem (which framing worked, which sub removed the post, who replied). Append-only, one paragraph, no column to backfill. That version survives contact with reality.

## What I edited

In `99-tracking.md`, verified corrections only; structure, `**Status:**` line and `## Links` preserved.

- **The one metric** — replaced the depth definition with "turned a knob", depth retained as a secondary median, gallery/peek/device confounds named, ad-blocker asymmetry added.
- **Secondary metrics** — removed returning visitors (impossible under cookieless); flagged tour completions as not yet instrumented.
- **PostHog setup** — added the preflight (key + cookieless project setting; zero events to date), the geography and bounce-rate caveats, and that breakdowns come off sessions, not persons.
- **The UTM convention** — referrer-first ordering, re-share inheritance, the `/sky` + `/compare` `replaceState` race, and how to read "direct".
- **The log** — rewritten around annotations, markdown kept for qualitative notes only.
- **The review cadence** — added the ~200-session gate before ranking on any rate.
