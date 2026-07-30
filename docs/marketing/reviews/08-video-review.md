# Review — 08 Short-form video

*Reviewed by the maintainer of a faceless short-form science channel — weekly uploads for years, no face, real numbers, and a working memory of what a Tuesday costs.*

## Verdict

**Upheld — but the shape is wrong.** The deferral is right and the reasoning behind it is mostly right. What I overturn is the *size of the "do this now"* and the *revisit trigger*: the doc recommends a 4–6 h frame exporter and a calendar date (month 4). It should recommend a ~10 h **whole-clip renderer** — text and timings included, no editing software in the loop — and a trigger that is an event (the 2027 coronagraph tech demo) plus evidence from six clips posted on surfaces that already exist. That converts a 40–70 h experiment into a ~12 h one, which is the difference between a plan that survives a bad Tuesday and one that doesn't.

## The numbers, checked

**The first video is 8–12 h, not 5–7 h.** The table costs the work and omits the friction: installing Resolve, learning where a text generator even lives, discovering vertical safe margins by exporting something with the caption under the UI, and the first three-platform upload with three sets of metadata and three caption tools. On my own first video I lost an entire evening to caption burn-in alone. The 5–7 h is what the *second* attempt feels like in memory. Corrected in the doc.

**Steady state is over-estimated, and this is the finding that matters.** The doc keeps 45 minutes of "edit / timing / text" in the steady-state column even after the exporter exists — which quietly assumes an NLE is still in the loop. If the JSON script carries the text beats and their timings, there is no timeline: you edit a file, run a command, upload. That is **~20 minutes**, not 90. The doc's own verdict is built on a number its own architecture makes obsolete.

**Conversion.** The stated 0.01–0.1% view→site is right, but assembled from a wrong part: published bio-link CTR benchmarks run **3–8% of profile visitors**, not the 1–3% claimed. Multiplied against a low-single-digit profile-visit rate you land in the same place, so the conclusion survives — 100k views is 30–100 sessions, and that matches what I see. Two things the doc gets right that people never believe until they've lived them: a meaningful share arrives as untracked type-ins, and burning the URL in-frame beats any bio-link tool ever built.

**Volume before signal: 20–30 is correct and the doc undersells *why*.** It isn't that early videos are unrepresentative. It's that on a cold account the variance between consecutive videos is ~100×. One video at 40,000 and nineteen at 300 is a completely normal month and it means *the format works and the account is still new* — a fact you cannot extract from fewer than about twenty samples. So the bar is right. What the doc misses is that 20 videos is roughly the **entire supply of good hooks** (below), so the channel experiment consumes the format rather than sampling it.

**Verified externally:** Roman launches 30 Aug 2026, 07:26 EDT, Falcon Heavy, LC-39A. TikTok's 21–34 s completion band and Reels' 7–15 / 30–45 s pockets check out; Shorts is 30–45 s, not 20–45. Bluesky's video sweet spot is 10–45 s, so the 20–26 s format spec is already correct for the surface I'd actually post on.

## The scripts, second by second

All three share one fault, and it is the fault the doc itself warns against four sections earlier: **they explain first and show second.** The doc correctly identifies the @physicsfun rule — the object does the impossible thing, *then* the caption explains what you watched — and then every script opens on black or on setup text and holds the payoff past second 9. On a cold account, an opening frame with no image is a swipe before the text has finished rendering.

**Script 1 — HD 189733 b.** The hook line is genuinely strong; "IT RAINS GLASS HERE" is top-decile. Three problems. (a) It plays over **black with a grid fading in** — the strongest line in the doc is spent on an empty frame. (b) Two lines compete at 1.4 s; nobody reads the wind speed. (c) The real killer: the question — "WHAT COLOUR IS IT?" — arrives at **8.5 s**. In a quiz format, the question *is* the retention device, and there is nothing holding the viewer for the eight seconds before it exists. Then a 3·2·1 counter eats another two. Counters read as padding in 2026; the pause alone is the tension. Ask the question by 2 s, reveal by 8, and you have a 16-second video that outperforms this 24-second one.

**Script 2 — WASP-12b.** Best hook of the three: "THIS IS A PLANET / you are not failing to see it" creates a perceptual problem in frame one and the second line rewards reading it. Then it spends **1.5–4.5 s on deliberate dead air**. Deliberate dead air is a technique you earn at 500k followers; on a cold account it's the swipe. The deeper risk is structural: the payoff is that nothing happens, which produces no screenshot and no argument — and the comment engine of a guess format is people defending a guess. Nobody defends "very dark." Move the Moon/asphalt comparison to second 3 and let the *comparison* be the reveal.

**Honesty flag, and it's the serious one.** The reveal card read `0.064` and the line read "It reflects 6% of the light that hits it." Bell et al. 2017 published an **upper limit**, Ag < 0.064 at 97.5% confidence. Stating a limit as a value, in the reveal frame, on the project whose entire positioning is knowing where measurement ends — that is the one error that would actually cost something. Fixed in the doc.

**Script 3 — the Roman collapse.** The best idea and the worst 1.5 seconds. "NASA'S NEXT TELESCOPE SEES FOUR COLOURS" is an institutional headline, not a viewer's problem, and it's only surprising if you already know telescopes normally see more. Worse, it opens on a **2×3 grid** — six small discs at 1080×1920 means no focal point, and vertical wants one big object. But the snap at 9.0 s is the single best second anywhere in this doc, and the fix is to build backwards from it.

**Rewritten hook (Script 3):**

| t (s) | Shot | On-screen text |
|---|---|---|
| 0.0–0.6 | **One** planet disc, already lit, already in true colour, filling the frame. No grid, no fade, no black. | *(none — the colour is the hook)* |
| 0.6–0.7 | **Hard cut.** Same disc, `{roman_hex}`. No transition. | **A REAL TELESCOPE DID THAT** |
| 0.7–1.5 | Disc holds in the collapsed colour. Second line snaps in. | it only sees four colours |
| 1.5–3.0 | Snap back to true, then pull out to the six-disc grid. | HOW MANY SURVIVE? |

Effect first, explanation second, question by 1.5 s — and it now obeys the rule the doc itself wrote down. Everything from 3 s onward can stay as scripted.

## The strongest case for doing it now

Argued properly, because it is not weak.

Short-form is **the only line item in the entire plan with genuine cold reach.** Show HN is one shot at an audience that must already be browsing. Reddit is permission-gated and several relevant subs ban this outright. SEO compounds but only answers questions people already know to ask. Bluesky requires an audience you don't have. Short-form is the sole channel where a stranger with zero context, who has never heard of an exoplanet albedo, gets the thing pushed at them.

And the usual reason not to do it doesn't apply here. For most people the cost of short-form is *making the assets*. Here the assets are a function call — this project can render pixel-perfect, physically-correct footage for free, forever, which inverts the standard economics completely. The doc proves this itself and then doesn't follow it through.

The hook is also a **category hook, not a product hook**: "every planet picture you have ever seen is an artist's guess." A stranger can be surprised by that, and mildly annoyed by it, and annoyance is distribution. Nothing else in the plan has a line that works on someone who owes the project nothing. Layer on the calendar — a launch in four weeks, a coronagraph demo in 2027 — and the honesty positioning is *most* valuable precisely where AI-voiced space slop is thickest. The contrast is sharpest where the noise is loudest.

**Why it still loses.** Three reasons, in order of how hard they are to argue with. First, the credits page is an unmet **CC BY licence obligation** ([13](../13-credit-the-scientists.md)). Broadcasting to the largest cold audience available while in breach of the licence on the data you're broadcasting is the one genuinely indefensible move on this board. Second, the site is **factually wrong about Roman's band configuration**, and Script 3 — the strongest video in the plan — is that error rendered at 1080×1920 and pushed to strangers. Publishing your best asset with your known error inside it is exactly how a trust-positioned project dies, and it dies permanently. Third, four weeks is not runway for a cold account, and the doc's diagnosis of why is exactly right: a new account's first videos get the smallest test audiences, which is the worst possible timing against a live peg.

And the creator-honest one. Three posts a week for eight weeks, alone, in the evenings, with a day job — I have done that stretch. The failure mode is never "the format didn't work." It is week five, Tuesday, tired, median 400 views, two posts still owed. At 5–7 h a video that plan does not survive contact. At 20 minutes it might. Which is why the renderer is the real decision, not the channel.

## Gaps

- **Script 3 is blocked by the site's own known CGI band error** and the doc never says so. Added.
- **All three scripts invert the doc's own show-first rule.** Named in the doc now, as a rule the scripts must be judged against.
- **Hook supply is ~20 worlds, not ~5,700.** The doc borrows the catalogue's SEO advantage and applies it to a medium where every opening line must be independently astonishing. Reveals are bottomless; hooks are not. This is the format's actual ceiling and it changes the 20-video gate from "a fair test" into "the whole inventory."
- **The music bed contradicts the verdict.** The verdict wants a silent MP4; the scripts assume a track. Resolved: ship the master silent, add music in-app on the platform.
- **Reddit as a video surface is narrower than implied** — r/spaceporn is images-only, r/space gates gif-like video to weekends. The clip's Reddit home needs checking per sub, not assuming.
- **No account-identity decision.** Faceless isn't nameless, and on a faceless account the personality lives entirely in comment replies — which is real unbudgeted time the risks section only gestures at.
- **Shorts' link advantage is overstated** (descriptions are collapsed); its search/long-tail advantage is understated, and the long tail is the actual reason to be there.

## Wrong or unverified

- **CapCut is not locked to 16:9 on Mac.** It has native 9:16 timelines and per-platform export presets on Apple Silicon and Intel. The claim as written is simply false; the real objections (paywall creep, ByteDance terms, cloud upload) are softer. **Corrected in the doc** — this is the kind of checkable error that makes a reader distrust the rest.
- **"~80% of completion variance in the first three seconds"** — no source. The documented funnel is ~65% of second-3 viewers reaching second 10, ~45% reaching second 30. Same conclusion, real number. Corrected.
- **"TikTok watermark suppresses Reels reach 40–70%"** — no published study supports a percentage. What is documented: Instagram has deprioritised watermarked reposts since 2021, excluding them from Explore and recommendations while still serving followers. Direction real, number invented. Corrected, and the rule kept.
- **Bio-link CTR "1–3% of profile visitors"** — benchmarks say 3–8%. Corrected; the net range is unchanged.
- **WASP-12b Ag = 0.064 is an upper limit**, not a measurement. Corrected in Script 2.
- **Unverified this session** (search budget exhausted): follower counts for @physicsfun (~2M), Astro Alexandra (~3.5M), Astrum (~2M). Directionally plausible, treat as approximate. Reddit native-video reach vs link posts also unchecked — the per-sub rules in [10](../10-reddit.md) are the binding constraint anyway.

## Better approaches

Ranked by hours-to-outcome, best first.

1. **Whole-clip renderer, then post natively to surfaces that already exist.** ~10 h build, ~20 min/clip, six clips tied to real pegs: Bluesky and Mastodon (video outperforms stills; 10–45 s is the sweet spot), a permitted Reddit sub, YouTube Shorts as a permanent search archive. No new account, no cadence promise. ~12 h all-in versus 40–70, and it answers the only real question — does the reveal land on strangers — cheaply. **This is the recommendation.**
2. **The Roman clip as a press and newsjack payload, with no channel at all.** One silent 15 s MP4. Journalists need a motion asset and almost never have one; a single outlet placement beats 100k algorithmic views on this project's conversion maths. Highest ratio available, and it's already half-written.
3. **YouTube Shorts only, no cadence, ship on pegs.** Sacrifices the algorithm entirely and buys the long tail, which is the asset that will still be working during the 2027 coronagraph demo. Lowest-guilt option for a solo maintainer: nothing is owed on a Tuesday.
4. **Hand the renderer's output to an existing faceless astronomy creator.** The doc mentions "a collaborator who edits" only in passing; it deserves a rank. One creator with 200k followers running a guess-the-colour clip is the exact ~50k-view evidence the doc says would flip the verdict — obtainable for the cost of one email rather than 40 hours. It also pairs naturally with [13](../13-credit-the-scientists.md), where you're already writing to people.
5. **The full cold TikTok/Reels channel, 3/week.** Last, but not zero — it is the only true cold-reach option and the renderer makes it survivable. Revisit at the 2027 tech demo, when the peg is largest and a 2026 back-catalogue is already indexed.

## The one thing I'd change

**Make the renderer emit the finished clip, not the frames.** The doc scopes a frame exporter at 4–6 h and then still budgets 45 minutes of editing per video forever — which silently keeps an NLE, and therefore an editing skill the maintainer doesn't have, on the critical path of every single video. Spend the extra four hours to put the text beats and timings in the JSON. It removes the discipline the objection was actually about, drops per-clip cost to ~20 minutes, and turns the whole question from "will I learn video editing" into "will I edit a JSON file" — which the maintainer will, on a Tuesday, tired.

## What I edited

In `08-short-video.md`: replaced the unsourced 3-second stat with the documented funnel and added the show-first rule to the mechanics list; corrected Shorts to 30–45 s; corrected WASP-12b to an upper limit in Script 2's reveal and caveat; added a blocker note to Script 3 for the unfixed CGI band config; corrected the CapCut claim and reframed its real objections; rescoped the exporter to a whole-clip renderer (~10 h, ~20 min/clip) and added the silent-master rule; added honest first-video (8–12 h) and steady-state (~20 min) corrections under the cost table; corrected bio-link CTR to 3–8% and the resulting range to 0.02–0.1%; replaced the invented watermark percentage with what is actually documented; reframed the Shorts advantage from links to search; added the ~20-hook ceiling and changed the format table's repeatability from ~5,700; rewrote the verdict into four parts with an evidence-based trigger and a pointer to this review. The `**Status:**` line and `## Links` section are preserved.
