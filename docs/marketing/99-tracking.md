# Tracking — how we judge all of it

**Status:** not started · **Effort:** one evening, then near-zero · **Payoff:** it's what makes every other doc improvable · **Hub:** [Marketing plan](./README.md)

## The bet

Ten channels and no measurement means ten guesses. The point of this page isn't a dashboard —
it's to be able to answer one question after eight weeks: **which room contains the people who
actually care?** Then stop doing the other nine.

## The one metric

Raw visits will lie to you. Hacker News and Reddit both produce enormous spikes of people who
bounce in four seconds; a design newsletter sends two hundred people who read three pages. If
you optimise for visits you will conclude the bouncing spike is the win and spend a year
chasing it.

**The metric is: of the people this source sent, what fraction opened more than one planet
page.** Call it *depth*. It's the closest cheap proxy for "found their people", it's robust
against spikes, and it's already available in cookieless analytics because it's a within-session
count, not a cross-visit one.

Secondary, in order: palette exports, tour completions, `/roman` visits (the signature feature —
if people find it, the site explained itself), and returning visitors where measurable.

Explicitly **not** metrics: follower counts, upvotes, impressions. They feel like progress and
predict nothing.

## The UTM convention

Every outbound link, everywhere, no exceptions. An untagged link is a post you learn nothing
from, and there is no way to reconstruct it later.

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

**Where UTMs don't apply:** crawlers and assistants. For [05-machine-readable.md](./05-machine-readable.md)
you're reading *referrer* segments instead — `chatgpt.com`, `claude.ai`, `perplexity.ai` — plus
access-log hits on `/llms.txt` and `/api/*`. Set those up as a saved segment once.

## PostHog setup

Analytics are already wired: cookieless, and gated on a build-time key so previews and local
builds send nothing. Two consequences to remember when reading numbers:

- **Visitor totals read high by design.** Cookieless means a returning person often counts as
  new. Never compare our absolute numbers to anyone else's; only compare our sources against
  each other, which is all we need.
- **Only the real deploy reports.** If a number looks impossibly low after a launch, check the
  key is actually set on the build before concluding the launch failed.

What to build, once:
1. A **sources dashboard** — sessions by `utm_source`, with the depth metric alongside. This is
   the only screen you need.
2. A **depth breakdown** — planet-pages-per-session, split by source.
3. A **feature-reach panel** — how many sessions touch `/roman`, a tour, the phase slider, a
   palette export. This tells you whether the site is explaining itself, which is a different
   question from whether people arrive.
4. An **assistant-referrer segment** for the machine-readable work.

Don't build more than four. A dashboard you don't read is a chore, and this is a fun project.

## The log

Analytics tell you what happened; they don't tell you what you *did*. Keep a plain markdown log
in this directory — `activity-log.md` — appended to after every action. One line each:

```
| date | channel | what exactly | link | result after 7d | notes |
```

This is the thing that makes the plan improvable. After twenty rows you can see which framings
worked, which subs removed the post, which pitch got a reply. Without it, every attempt is the
first attempt. The newsjack tool in [01-newsjacking.md](./01-newsjacking.md) should append to
this automatically — the parts you automate are the parts that survive.

Also log **placements you didn't cause**: unexpected referrers, someone else's post, a
newsletter that picked it up unprompted. Those are the cascade, and they're the best early
signal that something has legs.

## The review cadence

- **Weekly, five minutes:** glance at the sources dashboard. Anything surprising?
- **After each launch event, at 7 days:** fill in the log row's result column. Don't judge
  anything at 24 hours — the spike is not the outcome.
- **At 8 weeks, thirty minutes:** the real review. Rank the channels by depth, not volume. Pick
  the top two and drop or park the rest on the board in [README.md](./README.md). Write down
  *why* — the reasoning is worth more later than the ranking.

## Risks

- **Measuring instead of doing.** The setup is one evening. If it becomes a project, it has
  eaten the time it was meant to allocate.
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
