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

**But stock beats speed.** The wire-room version of this job is not chasing; it's having the piece
already written when the story breaks. The set of planets that generate exoplanet headlines is
small and largely knowable in advance: the TRAPPIST-1 / K2-18 / LHS 1140 / Proxima / GJ 1214 /
WASP-39 / 55 Cnc cluster that produces most of them; the JWST cycle targets with allocated time;
the Roman CGI tech-demo list we already ship in `data/roman-targets.json`; and whatever is on the
AAS meeting press-conference programme, which is published roughly two weeks ahead and is the only
lead time in this doc that is verifiably longer than a day. **Pre-write the physics sentence, the
caveat and the dated page note for twenty of those planets, in daylight, with the accuracy
checklist done.** Then a newsjack is a five-minute publish instead of a sixty-minute scramble, and
the reacting machinery below only has to cover the genuine surprises.

## Where the news actually breaks

Watch these, in priority order. All free, all RSS or a mailing list, none needing an account.
Every URL below was resolved on **2026-07-30**.

| Source | What it gives you | Feed |
|---|---|---|
| **NASA / ESA / ESO press releases** | The moment the general-audience cycle starts — and, for anything embargoed, the *first* public trace of the story. | `https://www.nasa.gov/feed/` · `https://www.esa.int/rssfeed/Our_Activities/Space_Science` · `https://www.eso.org/public/news/feed/` |
| **AAS Nova** | Editorially chosen results, written for humans. Good signal that something will travel. Daily. | `https://aasnova.org/feed/` |
| **Phys.org astronomy + Universe Today** | The aggregator layer — if it's here, Reddit is about to have a thread. | `https://phys.org/rss-feed/space-news/astronomy/` · `https://www.universetoday.com/feed/` |
| **arXiv `astro-ph.EP`** | The papers. A *stock-building* feed, not an early-warning one — see the lead-time note below. | `https://rss.arxiv.org/rss/astro-ph.EP` (the old `export.arxiv.org/rss/…` still 301s here, but this is the canonical host) |
| **NASA Exoplanet Archive updates** | New confirmed planets, **Thursdays**. Tells you when your own catalogue is stale. **No RSS feed exists** — sign up for the email list on the archive's Connect page, or scrape the news page. | `https://exoplanetarchive.ipac.caltech.edu/docs/exonews_archive.html` |
| **Bluesky astro feed / list** | Fastest human signal, and where you'll reply anyway. | See [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) |

Skip Google Alerts. It's slow, noisy, and always behind the sources above.

**The lead-time correction — read this before building anything around arXiv.** An earlier draft of
this doc claimed arXiv gives 1–3 days on the press cycle. That does not survive checking, and it is
wrong in *both* directions:

- **For a routine journal paper** the preprint goes up at acceptance and the institutional press
  release goes out at journal publication — often *weeks* later. The lead is much longer than three
  days, and you have that long to prepare properly.
- **For anything embargoed or coordinated** — Nature/Science papers, NASA/ESA/ESO press events, AAS
  meeting press conferences — the press release is the first public thing that exists. Journalists
  are briefed under embargo *before* the paper is public. Worked example: the K2-18 b DMS paper
  (arXiv:2504.12267) was submitted 16 Apr 2025 13:28 ET, just inside arXiv's 14:00 ET cutoff, so it
  announced at 20:00 ET that evening — hours, overnight, before the 17 Apr press wave. That is the
  *best* case, and it is hours, not days.

Also mechanical: arXiv announces at **20:00 ET, Sunday–Thursday only** (no Friday/Saturday
announcements), and the RSS feed is regenerated at midnight ET and carries **only that one day's
items**. Miss a poll and the day is gone. In Portuguese time the feed lands around 05:00, so a
morning cron is already ~7 hours behind a bot — and per [11-bluesky-mastodon.md](./11-bluesky-mastodon.md),
the arXiv firehose bots have 75 and 90 followers between them. Being first to a preprint is worth
approximately nothing. **Treat arXiv as the thing that tells you what to pre-build, not what to
react to.**

## The tool that makes this actually happen

Without automation this dies in week two — you will not remember to check six RSS feeds. So
build the smallest thing that removes the remembering:

**`tools/newswatch.py`** — stdlib-only, in the spirit of `tools/exohub.py`:

1. Poll the feeds above (cache ETags; be polite). Persist seen IDs — the arXiv feed is one day
   deep, so a skipped run is a lost day, and the log should say so loudly.
2. **Match names against an alias table, not a regex.** A regex over designations is where this
   tool dies. The press writes `TRAPPIST-1e`, `K2-18b`, `HD189733b`, `Gliese 1214 b`; the archive
   writes `TRAPPIST-1 e`, `K2-18 b`, `HD 189733 b`, `GJ 1214 b`. Build the lookup once, from
   `pscomppars` (`pl_name`, `hostname`, `hd_name`, `hip_name`, `tic_id`) plus the extra name
   variants in the `ps` table, normalised by lowercasing and stripping all spaces and hyphens.
   Add a small hand-curated file for the IAU NameExoWorlds names (Dimidium, Osiris, …) and the
   prefixes a designation regex always forgets: `HAT-P`, `HATS`, `KELT`, `KOI`, `NGTS`, `MASCARA`,
   `TIC`, `Wolf`, `Ross`, `LP`, `HR 8799`, `beta Pic` / `β Pic`, `51 Peg`, `2M1207`, `PSR B1257+12`,
   and `OGLE` / `MOA` / `KMT` for microlensing. Twenty lines of lookup beats a hundred of regex.
3. **Filter before you rank.** Drop arXiv items whose `announce_type` is `replace` (today's feed:
   17 items, of which 6 were replacements — without this filter every v2 re-alerts on the same
   planet forever). Drop any item naming more than three planets: a TOI catalogue paper is not a
   news story and a 200-line alert on week one is what gets this tool ignored by week three.
4. **Hard budget: at most 3 items surfaced per day**, ranked; everything else to a file you never
   open. Rank by, in order: (a) it appeared in a *press* feed, not just arXiv — press presence is
   the best single predictor that a story travels; (b) exactly one planet named in the title;
   (c) that planet is in our catalogue; (d) the title contains a travel-noun (below).
   **Suppress anything seen in the last 30 days** — paper, press release and aggregator are the
   same story arriving three times.
5. For each surfaced item, print **facts, not copy**: planet name, our page URL, the true-colour
   hex, the Roman-view hex, the ΔE2000, the provenance flag, the `data/RELEASE` tag our numbers
   came from, the four archive parameters we used (radius, mass, T_eq, host T_eff), and the
   headline. Deliberately *not* a ready-to-post sentence — a templated caption is the exact thing
   [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) says kills the account. The sentence is the
   only part of the post that has value; write it by hand.
6. Append every hit to `docs/marketing/newsjack-log.md` so the tracking is a side effect of the
   tool rather than a discipline you have to maintain.
7. Flag misses loudly: *"HD 12345 b is in the news and NOT in our catalogue"* — that's a data
   task, and it's also the most valuable output, because a planet in the news that we can't
   colour is the one gap that makes us look incomplete. See the coverage note below: this is the
   *majority* case, not an edge case.

Note it needs `data/planets.json`, which is **not in the repo** — it comes from the release named
in `data/RELEASE`. Have the tool call `scripts/fetch_data.py` or fail with a clear message,
otherwise it breaks on a fresh clone at exactly the wrong moment.

Run it from cron once a day, or as a `/loop`. One evening to build, and it converts a habit
you won't keep into a notification you can't miss.

## The case the plan has to survive: the planet isn't ours

This is the common case, not the exception. `pscomppars` holds **6,324 planets today**; the shipped
catalogue is **5,764**. Some of that gap is deliberate filtering, but newly confirmed planets — the
ones that generate "new planet discovered" headlines — are missing *by construction*, because the
data ships as a dated offline release (currently `data-20260727-1038`). On the single most common
newsjackable story, the default state is that we cannot post at all.

**Build the one-planet fast path before the watcher.** A `pipeline build --planet "<name>"` that
pulls one row from `pscomppars`, runs the full pipeline and emits one page turns "we don't have it"
into a five-minute job. It is higher value than `newswatch.py` and should be built first.

If even that fails — no radius, no mass, no host T_eff — the honest output is *"we can't compute a
colour for this one yet, and here's exactly which number is missing."* That is still a post, and
it's a better one than a guess.

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

**Never *pitch* a journalist about their own story after it's published.** Too late to be useful,
reads as self-promotion. Journalists you want *before* the story — that's
[02-press-kit.md](./02-press-kit.md) and [15-roman-launch.md](./15-roman-launch.md). Two standing
exceptions, both of which reporters actively want: a **correction** ("the radius in para 4 is the
2023 value") is always welcome and is how you become a source rather than a supplicant; and so is
answering a journalist who has publicly asked what colour something would be.

## The runbook

Pre-decide everything so the event itself is mechanical. But note that the channels decay at
wildly different rates, and an earlier draft of this runbook had the allocation backwards — 30 of
its 60 minutes went to the *slowest*-decaying channel and 10 to the fastest.

**Same hour (the only genuinely urgent move).**
- **0–10 min** — `newswatch` flags it. Run the accuracy checklist below. It is short on purpose.
- **10–25 min** — Write the one sentence of physics. Not a summary of the news — the *colour*
  angle they can't get anywhere else. "Why is this one blue" beats "scientists discover".
- **25–35 min** — Post to Bluesky + Mastodon with the image and alt text, and reply to the
  researcher or journalist who announced it. **This is the part with a real clock on it** — that
  reply window is roughly two hours wide and then it's over.

**Same evening or next morning.** Find the Reddit and HN threads. There is usually no thread to
join at minute 40: the big r/space or HN thread typically appears when the *aggregator* layer picks
the story up, six to eighteen hours later. A comment on a four-comment thread is worth nothing; a
comment on a two-hour-old thread that is climbing is worth a lot. Check, don't rush.

**Within the week, and never in a hurry.** The dated note on the planet page. It's the only part
that still earns traffic in six months, so it is the last thing that should be written fast.

The old rule — *"if it takes longer than an hour it isn't worth doing"* — is the rule that produces
the wrong-colour post. The deadline is negotiable; the numbers aren't. If the checklist below isn't
clean, you miss the story. Missing one is free. Being wrong on the day is not.

## The accuracy checklist

The failure mode is asserting a colour computed from parameters that the very paper being reported
has just superseded. Five minutes, every time, no exceptions.

1. **Open the paper, not the press release.** Find the parameter table. Write down its radius,
   mass, equilibrium temperature and host T_eff.
2. **Diff those four against ours.** More than ~10% on radius/mass, or >100 K on T_eq or T_eff, and
   our swatch was computed from superseded numbers. Don't post the swatch — post the fact that the
   colour *changed*, which is a better story anyway.
3. **Read the provenance flag** — `model` · `model-microlensing` · `simulated-cgi` · `measured-cgi`
   · `measured-albedo` — and put it in the post text, not just on the page.
4. **Say the release date out loud.** `data/RELEASE` is a dated snapshot. If it predates the paper,
   that's a caveat you state every time.
5. **Name the assumption you're least sure of** — cloud state, metallicity, or phase angle — and
   put it in the post. If you can't name it, you don't know this planet well enough to post.
6. **State the wavelength the news is about.** If the measurement is beyond ~1 µm, the colour claim
   is *independent* of the news; say so, or you are implying the result confirms the colour.
7. **Sleep-on-it triggers.** Anything that contradicts the paper, says "habitable" or "not
   habitable", or names a person — waits until morning. No exceptions, ever.
8. **Have the correction written before you post.** One pre-drafted sentence: *"I got X wrong —
   here's the corrected value and why."* A wire desk's speed comes from the retraction path being
   built in advance, not from being sure.

Then set a 24-hour reminder to re-check the archive for that planet. If our colour moves, update
the page *and* reply to your own post with the change. That one habit converts the biggest risk in
this doc into the most credible thing the project does.

## Judging it — is this one worth jacking?

Two tests, in this order. The first is about the *story*; the second is about *us*. Doing them the
other way round is how you spend an evening on a result nobody was ever going to read.

**Test one — will it travel?** Answerable from the headline in sixty seconds, without reading the
paper. Stories travel on nouns, not results.
1. Does it contain a **noun a non-astronomer already owns** — "Earth-like", "habitable", "life",
   "nearest", "first", "water", "seven planets", "diamond"?
2. Is there a **picture**? A story with an institution-supplied artist's impression travels several
   times further than one without — and that picture is precisely what our swatch argues with, so
   this test doubles as our relevance test.
3. Is a **big press office behind it** — NASA, ESA, ESO, MIT, Harvard, Cambridge? A fine A&A paper
   with no press office does not travel, however good it is.
4. Is it **one named planet**, or a population/statistical result? Population results don't travel
   and we can't jack them.

Two or more yes → it's a story. Then, and only then:

**Test two — can we add to it?**
1. Is the planet **in our catalogue** with a colour we're not embarrassed by — or can the one-planet
   fast path get us there in five minutes?
2. Does the colour angle **add something the article doesn't have**?
3. Is there a **live thread** to join, or an audience actually paying attention?

**The infrared case deserves better than a parenthesis, because it is the most frequent exoplanet
headline there is.** JWST transmission spectroscopy is what makes the news, and it constrains
composition, not visible colour. "This measurement tells us nothing about what the planet looks
like, and here's why that's interesting rather than disappointing" is a *standing, ownable
position* — so write that paragraph once, keep it, and reuse it. Don't improvise it at 23:40. One
boundary to get right or a scientist will correct you: optical *secondary-eclipse* photometry
(TESS, CHEOPS, Kepler) does constrain geometric albedo around 0.6–0.8 µm. "Infrared tells us
nothing about colour" is true; "space telescopes tell us nothing about colour" is not.

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
  just changed in the very paper you're reacting to. The accuracy checklist above exists for
  exactly this and is not optional. Read past the headline to the actual numbers, every time.
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
