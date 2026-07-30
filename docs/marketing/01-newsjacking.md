# Newsjacking — be the colour of today's headline

**Status:** not started · **Effort:** low per event, recurring · **Payoff:** high · **Hub:** [Marketing plan](./README.md)

## The bet

When an exoplanet makes the news, thousands of people spend an afternoon curious about one
specific planet — and every article illustrates it with an artist's impression. We can put the
computed colour of that exact planet in front of them within an hour, from data we already
have. Nobody else on Earth can do that. Over a year this out-earns any single launch post,
because it compounds: each event is small, but there are dozens, and each one lands on people
who are *already interested in that planet right now*.

Your two objections were the right ones — **where do I post, and how do I keep track** — so
this doc is mostly those two answers.

## Where the news actually breaks

Watch these, in priority order. All free, all RSS or a mailing list, none needing an account.

| Source | What it gives you | Feed |
|---|---|---|
| **arXiv `astro-ph.EP`** | The paper, 1–3 days *before* the press cycle. This is the edge — you can have the page ready before the news exists. | `http://export.arxiv.org/rss/astro-ph.EP` |
| **NASA Exoplanet Archive updates** | New confirmed planets, weekly. Tells you when your own catalogue is stale. | Archive "recent updates" page / TAP query on `rowupdate` |
| **AAS Nova** | Editorially chosen results, written for humans. Good signal that something will travel. | `https://aasnova.org/feed/` |
| **NASA / ESA / ESO press releases** | The moment the general-audience cycle starts. | Each has an RSS feed |
| **Phys.org astronomy + Universe Today** | The aggregator layer — if it's here, Reddit is about to have a thread. | RSS |
| **Bluesky astro feed / list** | Fastest human signal, and where you'll reply anyway. | See [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) |

Skip Google Alerts. It's slow, noisy, and always behind the sources above.

## The tool that makes this actually happen

Without automation this dies in week two — you will not remember to check six RSS feeds. So
build the smallest thing that removes the remembering:

**`tools/newswatch.py`** — stdlib-only, in the spirit of `tools/exohub.py`:

1. Poll the feeds above (cache ETags; be polite).
2. Extract candidate planet/star designations from titles and abstracts with a regex over the
   known naming conventions (`Kepler-\d+ ?[a-h]`, `TOI-\d+`, `WASP-\d+ ?b`, `HD \d+ ?[a-h]`,
   `GJ \d+ ?[a-h]`, `K2-\d+`, `TRAPPIST-1 ?[a-h]`, `LHS`, `LTT`, `HIP`, `55 Cnc`, …).
3. Cross-reference against `data/planets.json`.
4. For each hit, print a **ready-to-post block**: planet name, our page URL with the UTM tag
   already appended, the true-colour hex, the Roman-view hex, the ΔE2000, one line of the
   physics, and the headline that triggered it.
5. Append every hit to `docs/marketing/newsjack-log.md` so the tracking is a side effect of the
   tool rather than a discipline you have to maintain.
6. Flag misses loudly: *"HD 12345 b is in the news and NOT in our catalogue"* — that's a data
   task, and it's also the most valuable output, because a planet in the news that we can't
   colour is the one gap that makes us look incomplete.

Run it from cron once a day, or as a `/loop`. One evening to build, and it converts a habit
you won't keep into a notification you can't miss.

## Where to post — the actual answer

The instinct is to make a new post about it. **Don't.** For newsjacking, you want to be *inside*
the conversation that already exists, not starting a competing one.

**Tier 1 — reply, don't post.** This is the whole tactic.
- **The r/space / r/astronomy thread that already exists.** Find it, and be a genuinely useful
  top-level comment: *"If you're curious what this one would actually look like — here's the
  colour computed from its albedo model. Big caveat: it's a model, not a photo, and here's why
  that matters for this particular planet."* One link. No pitch. This routinely outperforms
  your own post by an order of magnitude and carries zero self-promo-rule risk *if* you have a
  real comment history — see [10-reddit.md](./10-reddit.md).
- **The Hacker News thread** on the same story, same approach.
- **Bluesky: quote-post or reply to the researcher/journalist who announced it.** Astronomers
  actually engage back. This is also how you build the relationships that
  [13-credit-the-scientists.md](./13-credit-the-scientists.md) depends on.

**Tier 2 — your own post.** Bluesky + Mastodon, always, since that's your home turf and the
daily-poster habit means it costs nothing. Format is in
[11-bluesky-mastodon.md](./11-bluesky-mastodon.md).

**Tier 3 — the site itself.** If the story is big enough, the planet's page gets a short dated
note: *"In the news, 3 Aug 2026: [result]. Here's what that does or doesn't change about the
colour we compute."* This is what makes the newsjack durable instead of disposable — it's the
thing that still earns traffic in six months via [03-seo-planet-pages.md](./03-seo-planet-pages.md).

**Never:** email a journalist about their own story after it's published. Too late to be useful,
reads as self-promotion. Journalists you want *before* the story — that's
[02-press-kit.md](./02-press-kit.md) and [15-roman-launch.md](./15-roman-launch.md).

## The 60-minute runbook

Speed is the whole product here. Pre-decide everything so the event itself is mechanical.

- **0–5 min** — `newswatch` flags it. Confirm the planet is in the catalogue and its colour
  isn't embarrassing (check the provenance flag — if it's microlensing or a wild extrapolation,
  say so *in the post*, don't hide it; the caveat is the interesting part).
- **5–20 min** — Write the one sentence of physics. Not a summary of the news — the *colour*
  angle they can't get anywhere else. "Why is this one blue" beats "scientists discover".
- **20–30 min** — Post to Bluesky + Mastodon with the image and alt text.
- **30–60 min** — Find the Reddit and HN threads; leave one real comment on each.
- **Later, if it's a big one** — add the dated note to the planet page.

If it takes longer than an hour it isn't worth doing. The value is being early and small, not
thorough.

## Judging it — is this one worth jacking?

Three questions, all must be yes:
1. Is the planet **in our catalogue** with a colour we're not embarrassed by?
2. Does the colour angle **add something the article doesn't have**? (Almost always yes — but if
   the story is about an infrared transit spectrum, the honest answer is "this tells us nothing
   about colour", and *saying that* is a good post too.)
3. Is there a **live thread** to join, or an audience actually paying attention?

If it's a "potentially habitable planet found" story, add a fourth: does our habitable-zone
lens agree? A quiet, well-sourced disagreement with a hype cycle is the most shareable thing
this project can produce — but only make that argument when you're certain.

## How we'll know it worked

Tag every newsjack link `utm_source=<where>&utm_medium=newsjack&utm_campaign=<planet-slug>`.
See [99-tracking.md](./99-tracking.md).

The metric is **not** visits — it's **the fraction who open a second planet page**. A newsjack
that sends 500 people who all bounce taught us nothing; one that sends 80 who go exploring
found us actual audience. Log both in `newsjack-log.md` and after ten events you'll know which
source and which framing is worth the hour.

## Risks

- **Being wrong, fast.** The failure mode is asserting a colour for a planet whose parameters
  just changed in the very paper you're reacting to. Always read past the headline to the actual
  numbers before posting.
- **Reading as an ambulance chaser.** Mitigated entirely by being useful and by *leading with
  the caveat*. If your comment's first job is to say what the model can't do, nobody minds the
  link.
- **Self-promo rules.** Comment-replies are near-zero risk; new posts are not. Read
  [10-reddit.md](./10-reddit.md) before your first one.
- **Burnout.** Cap it. Two newsjacks a month is a sustainable, winning pace. This is a fun
  project — if it becomes an on-call rotation you'll stop entirely.

## Links

- [README.md](./README.md) — the hub
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — where the posts go, and the daily habit that makes this cheap
- [10-reddit.md](./10-reddit.md) — thread-reply etiquette and self-promo rules
- [03-seo-planet-pages.md](./03-seo-planet-pages.md) — dated news notes are what make a newsjack durable
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — replying to researchers is how that relationship starts
- [15-roman-launch.md](./15-roman-launch.md) — the biggest scheduled newsjack of all
- [99-tracking.md](./99-tracking.md) — UTM conventions and the depth metric
