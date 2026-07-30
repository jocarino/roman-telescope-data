# Tracking — how we judge all of it

**Status:** not started · **Effort:** one evening, then near-zero · **Payoff:** it's what makes every other doc improvable · **Hub:** [Marketing plan](./README.md)

## The bet

Ten channels and no measurement means ten guesses. The point of this page isn't a dashboard —
it's to be able to answer one question after eight weeks: **which room contains the people who
actually care?** Then stop doing the other nine.

## The one metric

Raw visits will lie to you. Hacker News and Reddit both produce enormous spikes of people who
glance and go; a design newsletter sends two hundred people who actually use the thing. If you
optimise for visits you will conclude the spike is the win and spend a year chasing it. (Note
that "bounced in four seconds" is *not* something our setup can see — see PostHog setup below.
That's an argument for measuring an action, not a duration.)

**The metric is: of the sessions this source sent, what fraction turned a knob** — fired at
least one deliberate interaction: `roman_view_toggled`, `phase_changed`, `light_source_swapped`,
`palette_copied`, `palette_downloaded`, or a second `planet_viewed`. It's a union, not a single
behaviour, so it catches the designer who copied a palette, the astronomer who flipped the Roman
toggle and the browser who opened two planets, without forcing all three into one browsing style.
All six events already exist in the code, so this costs no new instrumentation. And those knobs
only make sense to someone who understood what the site is claiming, which is the actual question.

*Why not "opened more than one planet page" (call it depth), which is the obvious choice:* three
reasons, and they compound.

- **The gallery is one pageview.** It's an infinite-scroll grid, and filter/search/sort fire no
  events. Someone who scrolls 800 swatches and leaves delighted scores zero. For the design half
  of the audience the gallery *is* the artifact.
- **Hold-to-peek is invisible.** The long-press peek is a `fetch` of a static fragment — no
  pageview, no event. Peeking fifteen planets and opening one scores zero. Long-press is a phone
  gesture and tab-opening is a desktop one, so depth under-reads mobile — and channels differ
  sharply by device, so you'd be ranking channels partly by their audience's phone/laptop mix.
- **A great single-page visit scores zero.** Someone who reads one planet page properly and
  bookmarks it is the best outcome available.

Keep depth as a **secondary diagnostic, reported as a median** (planet pages per session). A
"≥2" threshold throws away the difference between 2 planets and 40.

Secondary, in order: palette exports, `/roman` visits (the signature feature — if people find it,
the site explained itself), and median depth.

**Not yet collectable, don't promise it:** tour completions (`web/static/tours.js` fires no
events at all — you can see a tour *started* and nothing after) and returning visitors
(structurally impossible, see below).

Explicitly **not** metrics: follower counts, upvotes, impressions. They feel like progress and
predict nothing.

### The bias to hold in your head

Ad blockers remove PostHog, and the code fails silently by design. HN and r/dataisbeautiful
readers block at far higher rates than design-newsletter readers. So comparing those two on any
*rate* compares a denominator missing its most technical third against a nearly complete one.
This is the single largest distortion in the whole scheme; it always makes the technical channels
look worse than they are. Prefer absolute counts of rare good events when the two audiences are
being compared directly.

## The UTM convention

Every outbound link, everywhere, no exceptions. An untagged link is a post you learn nothing
from, and there is no way to reconstruct it later.

**But read referrer first, UTM second.** Referrer is what you actually have for the biggest
planned spike — [09-show-hn.md](./09-show-hn.md) deliberately submits an untagged URL, which is
the right call — and it survives re-sharing honestly, because a repost to a new site produces
that site's referrer. UTMs are the tiebreaker for sources that eat referrers: Mastodon clients
emit `rel="noopener noreferrer"`, and in-app browsers often send nothing.

```
?utm_source=<where>&utm_medium=<kind>&utm_campaign=<what>
```

- **`utm_source`** — the specific place: `hn`, `reddit-space`, `reddit-dataisbeautiful`,
  `bluesky`, `mastodon`, `naiveweekly`, `zenodo`, `esero-pt`. Be granular; "reddit" as a single
  source is useless because the subs behave completely differently.
- **`utm_medium`** — the kind of thing: `social`, `newsjack`, `launch`, `newsletter`, `press`,
  `wallpaper`, `dataset`, `email`, `talk`.
- **`utm_campaign`** — the specific effort: `showhn-2026-08`, `wasp-76b-ironrain`,
  `roman-launch-week`, `palette-pack`.

Keep the vocabulary in this file and add to it rather than inventing on the fly. Two spellings
of the same source is the single most common way this kind of tracking quietly stops working.

**Three ways UTMs lie, all of which happen:**

- **Re-sharing inherits the tag.** When something works, people copy the URL from the address bar
  — *including the UTM*. Someone who arrives via `utm_source=bluesky` and reposts that URL to HN
  files every HN click as Bluesky. This only happens when you're winning, which is what makes it
  dangerous. The fix is one line of site code (not yet done): `history.replaceState` the `utm_*`
  params off the URL *after* the pageview fires, so a copied link is always clean.
- **`/sky` and `/compare` may strip the tag too early.** Both pages already call
  `history.replaceState(..., location.pathname)` to tidy their own query strings, and PostHog
  loads asynchronously — so the UTM can be gone before the pageview is captured. `/sky?planet=…`
  is the deep link this plan most wants shared. Check it in the network tab before any launch;
  the fix is to preserve `utm_*` in those two calls.
- **"Direct" never means "nobody happened".** It's a known mixture: Mastodon, in-app browsers,
  iOS Mail and Messages, copy-pastes, and everyone whose referrer was stripped. Read it by
  **timestamp join** — a direct spike within two hours of a logged post *is* that post. That is
  what makes the activity log below load-bearing rather than optional.

**Where UTMs don't apply:** crawlers and assistants. For [05-machine-readable.md](./05-machine-readable.md)
you're reading *referrer* segments instead — `chatgpt.com`, `claude.ai`, `perplexity.ai` — plus
access-log hits on `/llms.txt` and `/api/*` — though that second half isn't plumbed yet, see the
caveat on dashboard 4 below. Set the referrer segment up once.

## PostHog setup

Analytics are wired in the code: cookieless, and gated on a build-time key so previews and local
builds send nothing.

**Preflight — do this first, it currently fails.** As of this writing the PostHog project has
received **zero** events: its taxonomy contains no `planet_viewed`, no `palette_copied`, no
`roman_view_toggled`. Two things must both be true, and there is no partial failure mode:

1. `POSTHOG_KEY` is set as a build arg on Dokploy (it's a `Dockerfile` `ARG`, empty by default).
2. **"Cookieless server hash mode" is enabled** in PostHog project settings → Web analytics.
   With it off, every event is dropped silently, with no error anywhere.

Then load a planet page on the live site and watch `planet_viewed` appear in the Live tab. Until
that passes, every number in this plan is zero — and zero looks exactly like a failed launch.

What cookieless costs, once it *is* running:

- **Visitor totals read high by design.** The identifying hash is salted daily and the salt is
  deleted, so a returning person counts as new. Never compare our absolute numbers to anyone
  else's; only compare our sources against each other, which is all we need.
- **Returning visitors are not measurable at all** — not "where measurable". Same cause. Retention
  and lifecycle insights will render and mean nothing. Cross-device (phone then laptop) is gone
  for the same reason: nobody is ever identified.
- **Sessions merge behind shared IPs.** The hash is over `(daily salt, IP, user agent, hostname)`,
  so two people on one NAT with the same browser version become one session — normal on mobile
  carrier networks, universities and offices. Treat any per-session *rate* as approximate.
- **No geography.** In `always` mode the IP is consumed by the hash and discarded, so country and
  city are never captured and the world map stays empty.
- **Bounce rate is meaningless here, so don't quote it.** We deliberately run no autocapture and
  no `$pageleave`, so a single-pageview session has a computed duration of zero and is classified
  a bounce whether the visitor left in four seconds or read for four minutes. This is exactly why
  the headline metric is an interaction and not a duration — a knob turned at 90 seconds is the
  only thing that gives a session a real length.
- **Source breakdowns come off sessions, not persons.** No person profiles are ever created, so
  `$initial_utm_source` doesn't exist; use the sessions table's `$entry_utm_source` and
  `$entry_referring_domain`. Practical consequence: the by-source tile is a short HogQL query,
  not a dropdown in the insight builder. Budget half an hour of SQL, once.

What to build, once:
1. A **sources dashboard** — sessions by `$entry_utm_source`, falling back to
   `$entry_referring_domain`, with the knob-turn rate alongside. This is the only screen you need.
2. A **depth breakdown** — median planet-pages-per-session, split by source. Diagnostic, not the
   verdict.
3. A **feature-reach panel** — how many sessions touch `/roman`, a tour page, the phase slider, a
   palette export. This tells you whether the site is explaining itself, which is a different
   question from whether people arrive. Note the tour row is *starts* only until `tours.js`
   gets a `tour_completed` event.
4. An **assistant-referrer segment** for the machine-readable work. Caveat for
   [05-machine-readable.md](./05-machine-readable.md): the referrer half works, but the
   access-log half doesn't exist — `nginx.conf` sets no `access_log`, so `/llms.txt` and `/api/*`
   hits go to container stdout and die with the container. Ship logs somewhere or drop the claim.

Don't build more than four. A dashboard you don't read is a chore, and this is a fun project.

## The log

Analytics tell you what happened; they don't tell you what you *did*. And given how much
attribution the section above just took away — no returning visitors, no referrer from Mastodon,
an untagged HN submission by choice, ad blockers eating a biased slice — **the dated record of
what you did is the strongest attribution signal available.** Most real attribution here will be
"spike at 19:40 on the 12th; posted to r/space at 19:30". It is not a nice-to-have.

Which is exactly why it must not be a markdown table with a "result after 7 days" column to
backfill. One person, evenings and weekends, will abandon that around row six.

**Log it as a PostHog annotation.** One API call, or four clicks in the UI, at the moment you
post. Annotations draw a vertical line on *every chart you already open*, so the log gets read
passively when it's relevant instead of requiring you to remember a second file exists. Nothing
to reconcile, and it can't drift from the data. Format: `<channel> · <what exactly> · <link>`.

Keep a plain `activity-log.md` in this directory for the one thing annotations are bad at — the
qualitative post-mortem. Which framing worked, which sub removed the post, which pitch got a
reply. Append-only, one short paragraph, **no result column**. After twenty entries you can see
which framings worked; without it, every attempt is the first attempt. The newsjack tool in
[01-newsjacking.md](./01-newsjacking.md) should write the annotation automatically — the parts
you automate are the parts that survive.

Also log **placements you didn't cause**: unexpected referrers, someone else's post, a
newsletter that picked it up unprompted. Those are the cascade, and they're the best early
signal that something has legs.

## The review cadence

- **Weekly, five minutes:** glance at the sources dashboard. Anything surprising?
- **After each launch event, at 7 days:** write the qualitative note. Don't judge anything at
  24 hours — the spike is not the outcome.
- **At 8 weeks, thirty minutes:** the real review. Rank the channels by knob-turns, not volume.
  Pick the top two and drop or park the rest on the board in [README.md](./README.md). Write down
  *why* — the reasoning is worth more later than the ranking.

**The sample-size gate, which is not optional.** Below roughly **200 sessions from a source, do
not compare rates** — report the absolute count of knob-turns instead. A 40-session channel with
a 35% rate has a 95% interval of about 20–50%; telling 35% from 50% reliably needs ~175 sessions
per channel. "r/dataisbeautiful: 14 palette copies; Bluesky: 3" is decision-grade, needs no
denominator, and survives cookieless intact. Ranking ten small channels by a percentage and then
dropping eight of them is how you confidently delete the thing that was working.

## Risks

- **Measuring instead of doing.** The setup is one evening. If it becomes a project, it has
  eaten the time it was meant to allocate.
- **Silent zero.** This is the live failure mode, not a hypothetical: a missing `POSTHOG_KEY` or
  an unticked cookieless setting drops every event with no error, and the result is
  indistinguishable from "nobody came". Run the preflight before the launch, not after it.
- **Judging too early.** SEO ([03-seo-planet-pages.md](./03-seo-planet-pages.md)), educators
  ([14-educators.md](./14-educators.md)) and the machine-readable work
  ([05-machine-readable.md](./05-machine-readable.md)) all take months and will look like
  failures at week four. Exempt them from the 8-week review explicitly.
- **Over-instrumenting the site.** The project's appeal includes being light and not
  surveillance-shaped. Don't add tracking that you'd be uncomfortable describing on the press
  page.

## Links

- [README.md](./README.md) — the board this feeds
- [01-newsjacking.md](./01-newsjacking.md) — the log is a side effect of the watcher tool
- [05-machine-readable.md](./05-machine-readable.md) — referrer segments instead of UTMs
- Every other doc's `How we'll know it worked` section defers to this one.
