# Marketing plan — getting this in front of people

The tracking hub. One doc per channel; this page is the board that says what's live, what's
next, and what we decided against. **If you only read one page, read this one.**

Ground truth for status lives here, in the table below. Each channel doc repeats its own
status line at the top — if the two disagree, this table wins.

---

## The positioning

> Most "exoplanet pictures" you have ever seen are an artist's guess. These are computed from
> physics — and the site tells you exactly where the model ends and the measurement begins.

That sentence is the whole pitch, and it works on both audiences at once: the astronomy
crowd hears *honest*, the design crowd hears *real*. Every pitch, post and title in these
docs is a variation on it. When in doubt, lead with the honesty, not the prettiness — the
prettiness is visible in one glance anyway.

Three structural advantages worth remembering, because they decide what's worth doing:

1. **~5,700 planets = ~5,700 unique pages and ~5,700 unique images.** Bottomless content and
   a very long SEO tail, at zero marginal cost. Almost every good idea below is a way of
   spending that asset.
2. **Two unrelated audiences want the same artifact** — astronomers and designers. Same site,
   different words. Never use one audience's words on the other.
3. **There is a date on the calendar, and it is close.** Roman launches **30 August 2026** —
   about four weeks out — and its coronagraph tech demo follows in 2027. When that happens every
   outlet needs "what will Roman actually see", and the honest answer is our signature feature.
   See [15-roman-launch.md](./15-roman-launch.md), which also flags a **factual correction we
   owe to our own CGI band model** before we say anything publicly about Roman.

---

## The board

| # | Channel | Status | Effort | Payoff | Note |
|---|---------|--------|--------|--------|------|
| [01](./01-newsjacking.md) | Newsjacking exoplanet headlines | not started | low, recurring | **high** | Needs the watcher tool + a place to post. Highest ratio in the plan. |
| [02](./02-press-kit.md) | Press kit `/press` | not started | one evening | medium | Prerequisite for 12, 15, 19. Do early, it unblocks others. |
| [03](./03-seo-planet-pages.md) | SEO on planet pages | not started | one session | **high**, slow | Own session — it's a code change. Half the plumbing already exists. |
| [04](./04-wikimedia.md) | Wikimedia Commons uploads | **parked** | medium | low–medium | Honest verdict inside: worth less than it looks. Read before doing. |
| [05](./05-machine-readable.md) | Machine/LLM-readable surface | not started | medium | **high**, rising | Your instinct was right — this beats human embeds. |
| [06](./06-open-data.md) | Open dataset release | not started | low | medium | Cheap, reaches a crowd nothing else here reaches. |
| [07](./07-wallpapers.md) | Wallpaper pack | not started | low | medium | Answer to "where does it live" is inside. |
| [08](./08-short-video.md) | Short-form video | **deferred** | 40–70 h before any signal | worst ratio here | Verdict inside: *later, conditionally*. The one thing to do now is the clip exporter, which five other docs use. |
| [09](./09-show-hn.md) | Show HN | not started | one day, high focus | **high**, one shot | Don't fire this until 02 and 03 are done. Weekend beats weekday — see inside. |
| [10](./10-reddit.md) | Reddit | not started | medium, recurring | high but spiky | Several subs ban this outright; the sub-specific asset (the two-strip chart) is the real prize. |
| [11](./11-bluesky-mastodon.md) | Bluesky + Mastodon | not started | low, daily | **high** | The daily poster lives here. Start before you need it. Personal account, not a bot. |
| [12](./12-design-newsletters.md) | Design newsletters & curators | not started | one evening | medium | Free, email-pitchable, cascades. Several classics are dead or pay-to-play — list is verified. |
| [13](./13-credit-the-scientists.md) | Credit the scientists | **blocking, and overdue** | 1 weekend + 1 evening | **highest** | The audit found a CC BY licence obligation we are not meeting. Fix before any outreach. |
| [14](./14-educators.md) | Teachers, planetariums, clubs | not started | medium | medium, durable | Slowest payoff, longest half-life. |
| [15](./15-roman-launch.md) | The Roman launch play | **clock is running** | 3 urgent evenings, then light | **highest ceiling** | Launch **30 Aug 2026**. Aim at the 2027 coronagraph tech demo, not launch week. Contains a band-config correction to make first. |
| [99](./99-tracking.md) | Tracking & measurement | not started | one evening | — | UTM conventions + how we judge everything above. |

**Status values:** `not started` · `in progress` · `done` · `parked` (decided against for now,
with a reason) · `dropped` (decided against permanently).

---

## Sequencing

Ordered by dependency, not by excitement. The temptation is to fire Show HN first; resist it —
a launch spike lands on whatever the site is on that day, and you get one.

> **The calendar overrides the phases.** Roman launches 30 Aug 2026. Two things are genuinely
> time-critical and jump the queue: the **CGI band-config correction** (we currently model four
> bands; the flight configuration isn't four — [15](./15-roman-launch.md)) and the
> **credits page**, which has a licence obligation attached ([13](./13-credit-the-scientists.md)).
> Both are wrong-on-the-site problems, and being wrong on the site is worse than being unknown.
> Do those before anything promotional, then resume the phases below.

**Phase 0 — before any promotion (2–3 evenings)**
Do [13](./13-credit-the-scientists.md) (the credits page — this is an obligation, not just
tactics), [02](./02-press-kit.md), [03](./03-seo-planet-pages.md), and
[99](./99-tracking.md). Start the daily posting habit in
[11](./11-bluesky-mastodon.md) *now* so the account isn't a ghost town when traffic arrives.

**Phase 1 — the spike (one focused week)**
[09](./09-show-hn.md) on a day you can be present for six hours. Then
[10](./10-reddit.md) staggered over the following weeks — never two subs in one day.
Then [12](./12-design-newsletters.md) pitches. Scientist emails
([13](./13-credit-the-scientists.md)) go out the day *after* HN, so you can honestly say it
got some attention.

**Phase 2 — the long tail (weeks 5–12)**
[05](./05-machine-readable.md), [06](./06-open-data.md), [07](./07-wallpapers.md),
[04](./04-wikimedia.md) if it survives its own verdict. These pay out over months.

**Ongoing, forever**
[01](./01-newsjacking.md) whenever a planet makes news, the daily post from
[11](./11-bluesky-mastodon.md), [14](./14-educators.md) at whatever pace, and building
quietly toward [15](./15-roman-launch.md).

**If you only do three things:** the daily poster, Show HN done properly, and crediting +
emailing the scientists. Those three have the best effort-to-outcome ratio by a wide margin.

---

## Not decided yet

Ideas from the original list that haven't been ruled in or out. Parked here so they don't get
silently lost — decide on them when the phase they belong to comes up.

- **Reverse colour index (`/color/4a6ea9`).** A page per quantised hex → the nearest exoplanet.
  Designers search hex codes constantly; this is enormous long-tail coverage for one
  nearest-neighbour lookup over data we already have. Belongs with
  [03-seo-planet-pages.md](./03-seo-planet-pages.md); worth a decision before that session runs.
  Caveat: it's thousands of thin generated pages, which is exactly the shape search engines
  penalise — it only works if each page is genuinely useful. See the doc for the honest take.
- **Palette pack** (.ase + Figma Community + Procreate swatches). Assessed inside
  [12-design-newsletters.md](./12-design-newsletters.md) — Figma Community has its own search
  and effectively zero astronomy content.
- **Personalisation hook** — "the planet discovered the year you were born", or paste a hex and
  find its planet. Strongest share driver available, but it's a feature, not a marketing task.
  Overlaps the reverse colour index above.
- **Science press pitching** (Universe Today, Sky & Telescope, Colossal, Nautilus). Gated on
  [02-press-kit.md](./02-press-kit.md); the strongest version of it is the Roman peg in
  [15-roman-launch.md](./15-roman-launch.md), so it may be better to hold rather than spend
  the pitch now.
- **Newsletter of our own** ("colour of the week"). Cheap on Buttondown's free tier, but it's a
  recurring obligation — only worth starting once there's an audience to send it to.

---

## House rules

- **One channel at a time.** A solo maintainer running five channels badly beats nothing, but
  loses to one channel run well. The board is a queue, not a checklist to parallelise.
- **Never the same words twice.** Each audience gets its own framing. Copy-pasting a Reddit
  title into a design newsletter is how both bounce.
- **Every outbound link is tagged.** No exceptions — see [99-tracking.md](./99-tracking.md).
  An untagged link is a post you learn nothing from.
- **Honesty is the differentiator, not a disclaimer.** Never let a post imply a colour was
  photographed. It's the one thing that makes this project trustworthy, and trust is the only
  reason a scientist would ever share it.
- **Update this board when a status changes.** A tracking doc nobody edits is worse than none,
  because it lies with authority.
