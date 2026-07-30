# Marketing plan — getting this in front of people

The tracking hub. One doc per channel; this page is the board that says what's live, what's
next, and what we decided against. **If you only read one page, read this one.**

Every doc has been through an adversarial second pass — see [reviews/](./reviews/), which also
documents the reviewer personas and how to re-run them. The plans were edited in place where a
reviewer found a verified error, so **the docs are current**; the reviews hold the argument.

Ground truth for status lives here, in the table below.

---

## The verdict of the second pass

Sixteen reviewers, cast as the people most likely to reject each plan, agreed on something none
of the individual docs said: **this project has correctness debt, and the plan was scheduling
promotion on top of it.**

Four defects, each found independently, each one that promotion would amplify rather than survive:

1. **The Roman band configuration in `pipeline/config.py` is wrong.** Every "as Roman would see
   it" swatch — the signature feature — is computed through the wrong filter set. Our `835 nm`
   and `6%` widths trace to no primary source at all. Details and the verified flight
   configuration in [15](./15-roman-launch.md); the astronomer's audit is in
   [reviews/15-roman-review.md](./reviews/15-roman-review.md).
2. **Analytics have never worked.** The PostHog project has not ingested a single event, so
   there is currently no way to judge any of this. [reviews/99-tracking-review.md](./reviews/99-tracking-review.md).
3. **About 97% of planet pages are orphans.** The gallery ships an empty grid built in JS with
   scroll-loading, so only ~100–200 planets sit in the crawlable link graph — and ~5,700 peek
   fragments are publicly indexable with no `noindex`. [reviews/03-seo-review.md](./reviews/03-seo-review.md).
4. **Licence and contact gaps.** No `LICENSE` for our own code or data — so the dataset is not
   actually open and cannot be deposited — an outstanding CC BY 4.0 obligation to a source we
   redistribute, and **no email address anywhere on the site**, so no journalist can reach us
   today. [13](./13-credit-the-scientists.md), [06](./06-open-data.md), [02](./02-press-kit.md).

The second theme was scope. Reviewer after reviewer, independently, said the same thing about
their own doc: *this proposes six things and one of them is worth building.* The plan as first
written would consume a year of evenings. Treat every "what to build" list as a menu with one
correct answer.

---

## The positioning

> Most "exoplanet pictures" you have ever seen are an artist's guess. These are computed from
> physics — and the site tells you exactly where the model ends and the measurement begins.

Two reviewers sharpened this in the same direction and it's worth adopting everywhere: **stop
selling the swatch, start selling the audit.** A physics-derived colour is a claim; a colour
with its provenance, its assumptions and its error bars attached is the thing nobody else has.
The strongest single line the reviews produced, for pitches and posts alike: *"HD 189733 b is
cobalt blue because sodium eats the yellow — and I can show my working."* Name one planet. A
dataset of 5,700 is not something anyone can print.

Three structural advantages that decide what's worth doing:

1. **~5,700 planets = bottomless content at zero marginal cost.** But not 5,700 keyword targets —
   nobody searches TOI-4562 c. The corpus's job is structure and citability, not head terms.
2. **Two unrelated audiences want the same artifact** — astronomers and designers. Same site,
   different words. Never use one audience's words on the other.
3. **There is a date on the calendar.** Roman launches **30 August 2026**; the coronagraph tech
   demo follows in 2027 and *that* is the beat to aim at. See [15](./15-roman-launch.md).

---

## The board

| # | Channel | Status | Review verdict | Note |
|---|---------|--------|----------------|------|
| [01](./01-newsjacking.md) | Newsjacking exoplanet headlines | not started | revise | Stop selling it as a speed play — speed is what produces the one wrong colour. Build the pre-made bench instead. |
| [02](./02-press-kit.md) | Press kit | not started | rework | Split `/about` (human) from `/press` (assets). No email on the site today — fix that first, it's a five-minute job. |
| [03](./03-seo-planet-pages.md) | SEO on planet pages | **blocked by defect 3** | rework | The link graph is the blocker, not the wording. Reverse colour index killed. |
| [04](./04-wikimedia.md) | Wikimedia Commons | small version: **do it** | partly overturned | Campaign stays parked, but the small version is unblocked today — my DOI-unblocks-it reasoning was a policy misreading. |
| [05](./05-machine-readable.md) | Machine/LLM-readable surface | not started | revise | `llms.txt` is folklore. Stable join keys and machine-checkable honesty are the real items. |
| [06](./06-open-data.md) | Open dataset | **blocked by defect 4** | revise | The file has no licence, so it isn't open yet. Licence → describe → deposit once, well. |
| [07](./07-wallpapers.md) | Wallpaper pack | not started | revise | Right delivery, wrong artifact: **make the spectrum the wallpaper, not the planet.** |
| [08](./08-short-video.md) | Short-form video | **deferred** | upheld, reshaped | ~10 h whole-clip renderer, not a frame exporter. Revisit on the tech demo, not a date. |
| [09](./09-show-hn.md) | Show HN | **blocked by defect 1** | revise | Don't submit while the band config is wrong. Weekends beat weekdays. No plan yet for the hours after you sleep. |
| [10](./10-reddit.md) | Reddit | not started | **substantially rework** | The six-week calendar *is* the ban risk. 90 days of commenting, then two posts. |
| [11](./11-bluesky-mastodon.md) | Bluesky + Mastodon | not started | strongest doc, one bad post | Start the habit now. Don't publish a Roman comparison until defect 1 is fixed. |
| [12](./12-design-newsletters.md) | Design newsletters & curators | not started | revise | Its #1 target shut down five weeks ago. Re-verify before every wave. |
| [13](./13-credit-the-scientists.md) | Credit the scientists | **blocking** | revise | Audit was ~80% right; the reviewer found more, including the band error. |
| [14](./14-educators.md) | Teachers, planetariums, clubs | not started | revise | Seven artifacts → two. The anchor lesson is the one worth building. |
| [15](./15-roman-launch.md) | The Roman launch play | **clock running** | ship after two repairs | Predict band albedos, not hex codes. Band 2 hardware *is* installed — it's untested, not absent. |
| [99](./99-tracking.md) | Tracking & measurement | **broken** | rework | Nothing is being measured. Metric changed from "depth" to "turned a knob". |

**Status values:** `not started` · `in progress` · `done` · `blocked` · `parked` · `dropped`.

---

## Sequencing

> **Phase −1 — fix what's wrong, before any promotion.** This did not exist in the first draft
> and is now the most important part of the plan. Being wrong on the site is worse than being
> unknown, and every one of these is small:
>
> 1. **The Roman band configuration** ([15](./15-roman-launch.md)) — a data-side evening, and it
>    unblocks 09, 11 and 02, all of which currently repeat the wrong figure.
> 2. **Make analytics work** ([99](./99-tracking.md)) — otherwise Phase 1 teaches you nothing.
> 3. **A `LICENSE`, the outstanding CC BY attribution, and an email address on the site**
>    ([13](./13-credit-the-scientists.md), [02](./02-press-kit.md)) — one evening for all three.
> 4. **The crawlable link graph** ([03](./03-seo-planet-pages.md)) — the only slow one; start it
>    early because it pays out over months.

**Phase 0 — before promotion.** `/about` and `/press` ([02](./02-press-kit.md)), the credits page
([13](./13-credit-the-scientists.md)). Start the daily posting habit in
[11](./11-bluesky-mastodon.md) now, so the account isn't a ghost town when traffic arrives.

**Phase 1 — the spike.** [09](./09-show-hn.md) on a day you can be present for six hours — and
per its review, a weekend is genuinely better than the classic weekday slot. Then the *reduced*
Reddit plan ([10](./10-reddit.md)): commenting first, two posts, not ten. Then
[12](./12-design-newsletters.md), re-verifying each outlet the week you pitch. Scientist emails
([13](./13-credit-the-scientists.md)) after the band fix, never before.

**Phase 2 — the long tail.** [05](./05-machine-readable.md), [06](./06-open-data.md),
[07](./07-wallpapers.md), the small Commons upload in [04](./04-wikimedia.md).

**Ongoing.** [01](./01-newsjacking.md), the daily post, [14](./14-educators.md) at whatever pace,
and building toward [15](./15-roman-launch.md).

**If you only do three things:** fix the band configuration, make analytics work, and credit the
scientists then email them. The first two are prerequisites for judging anything else; the third
is still the highest-value single action in the plan.

---

## Not decided yet

- **Palette pack** (.ase, Figma Community, Procreate) — assessed in [12](./12-design-newsletters.md).
- **Personalisation hook** — "the planet discovered the year you were born". Strongest share
  driver available, but it's a feature, not a marketing task.
- **Science press pitching** — gated on [02](./02-press-kit.md); the strongest version is the
  Roman peg in [15](./15-roman-launch.md), so holding may beat spending it now.
- **A newsletter of our own** — cheap, but a recurring obligation. Only once there's an audience.

*Dropped by review:* the reverse colour index (`/color/<hex>`) — replaced by one client-side
lookup tool plus 14 colour-family hub pages that double as the missing link scaffolding.

---

## House rules

- **One channel at a time.** The board is a queue, not a checklist to parallelise.
- **Never the same words twice.** Each audience gets its own framing.
- **Re-verify before you act.** A doc researched in July and executed in October is a doc that
  will send you to a newsletter that closed. Every list here has a shelf life.
- **Honesty is the differentiator, not a disclaimer.** The reviews turned this from a principle
  into a spec: the qualifier belongs in the noun, the caption, the image pixels, the file
  metadata and the data type — not in a paragraph a sub-editor can cut.
- **Update this board when a status changes.** A tracking doc nobody edits lies with authority.
