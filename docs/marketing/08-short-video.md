# Short-form video

**Status:** not started · **Effort:** high — 5–7 h for the first video, ~2 h steady state, and ~40–70 h before the experiment means anything · **Payoff:** the worst hours-to-visitors ratio in this plan; real value is reusable assets, not clicks · **Hub:** [Marketing plan](./README.md)

## The objection

> "Not engaging enough — I feel like this is a completely new avenue that requires understanding audience and medium."

**Half of this holds absolutely, and it is the half that decides the verdict.**

The "not engaging" half is right about the thing that was implicitly being proposed — a screen recording of the phase slider — and wrong about the raw material. A slider demo is a *product tour*. Short-form does not reward product tours, because a product tour asks the viewer to already care about the product. But the project does own the one structure short-form reliably rewards: **a question with a visual answer and a number attached.** "What colour is the planet where it rains molten glass?" is not a product tour. It is a quiz whose answer happens to be the product.

The "new avenue" half holds completely. It is a genuinely separate discipline with its own craft, its own failure modes, a 20-video minimum before the data means anything, and — critically — the weakest conversion path to a website of any channel in this plan. That is the reason to defer, and it does not go away just because the format is good.

So: the format objection is answerable. The cost objection is not. Both conclusions are in [The verdict](#the-verdict).

## What actually works in science short-form

Four real accounts, chosen because each isolates a different variable.

- **[@physicsfun](https://www.instagram.com/physicsfun/)** (Dr Raymond Hall, Fresno State physicist) — ~2M Instagram followers, **completely faceless**: hands, one object, one caption, black background, no voice. This is the existence proof that a faceless science account can carry millions on nothing but *object + text*. The structural reason it works: every post is a physical thing doing something visually impossible, and the caption exists only to explain the thing you already watched. **Never** the reverse.
- **[Astro Alexandra](https://www.tiktok.com/@astro_alexandra)** (Alexandra Doten, ~3.5M TikTok) — the opposite pole: face-led, news-pegged, and the retention mechanism *is* her delivery. Studied here to rule it out. This account cannot be reverse-engineered without a performer, and the maintainer is not one. Do not benchmark against it.
- **[Astrum](https://www.youtube.com/@astrumspace)** (Alex McColgan, ~2M subs, running since 2013) — faceless, narration over archive imagery. Proves faceless space content scales, but on *voice and scripting*, over 10 years. His Shorts are excerpts of long-form, not native shorts. Relevant lesson: the Shorts feed a channel, they aren't the channel.
- **SEA / Cosmoknowledge and the wider faceless-space genre** — multi-million-subscriber channels built on AI voiceover plus public-domain footage. Cautionary, not aspirational: it is commodity content at high volume, and it is exactly the category audiences have started to distrust. This project's entire positioning is *the honest one*; adopting the visual grammar of AI slop would cost more than the reach is worth.

**The structural mechanics, with numbers:**

- **The first 1–3 seconds decide everything.** Reported analyses put ~80% of completion variance in the first three seconds. A sharp drop at second 3 means the hook failed; a *flat* retention curve is the signal that gets a video pushed. There is no recovering a bad opening with a good middle.
- **Length that wins now (2026):** TikTok clusters at **21–34 s**; Reels has a viral pocket at 7–15 s and a "value" pocket at 30–45 s; Shorts land one idea in **20–45 s**. A 20 s video held to 80% beats a 60 s video that loses half its audience at second 12.
- **Text carries the claim; voice is optional.** The default viewing state is sound-off. Text-led hooks make the payoff legible in frame one, and burned-in captions are mandatory regardless. **A faceless, voiceless account is fully viable here** — @physicsfun has proved it for a decade.
- **The quiz/reveal structure is the highest-performing faceless format**, for a mechanical reason: the question is a hook, the pause before the answer is a retention *spike* rather than a decay, and the reveal generates comments from people defending their guess. High watch time plus high comment rate is precisely what every one of these algorithms optimises for.
- **Loopability.** An ending that cuts cleanly back into the opening frame counts rewatches as watch time. Cheap, and worth more than most edits.

**What reliably fails:** screen recordings of UI, slow zooms with no payoff, "here's a cool website" as the hook, and anything that requires the viewer to already know what an exoplanet albedo is.

## Does this project have a format?

Five candidates, judged on: is it native to the medium, is it repeatable ~50 times, does it need a performer, does the reveal *require* the site's actual output?

| # | Candidate | Native? | Repeatable | Verdict |
|---|-----------|---------|------------|---------|
| 1 | **Guess the colour** — planet's stats, hold, reveal the computed hex | Yes — it's a quiz | ~5,700 | **Winner** |
| 2 | **The same planet under six suns** — the lamp swap, M dwarf → A star | Beautiful, but it asks no question | High | B-roll / filler, not a format |
| 3 | **"It rains glass / iron / rubies"** — extreme-world hooks | Yes, as a *hook supply* | ~15 genuinely striking worlds | Feeds #1, isn't its own format |
| 4 | **The true → Roman collapse** — what a real telescope actually gets | Strongest single video in the plan | ~3 before it's stale | One-off, not a series |
| 5 | **Colour countdown of the strangest worlds** | Yes (listicle) | Medium | 5× the assets per video for the same payoff |

**The pick: #1 "Guess the colour", using #3 as the hook supply and #4 as the recurring twist.**

Why it wins on the objection's own terms. It is a quiz, not a demo — the medium's own most-proven faceless structure. The reveal *is* the product: the moment of payoff is literally the thing the site computes, so the video cannot be watched without understanding what the site does. It is repeatable across ~5,700 planets, which is the project's structural advantage (see [README](./README.md)) spent in the one place volume actually matters. It needs no camera, no voice, and no performer. And the honesty caveat, which every other channel treats as a disclaimer, becomes a *second reveal* here: "and this is not a photograph — nobody has ever photographed this planet."

Why not the others. #2 has no question, so it has nothing to hold on — it's a texture loop, and texture loops need an existing audience. #4 is genuinely the best *single* video available but goes stale by the third, so it's a recurring beat inside #1's format, not a series. #5 needs five reveals per video and produces one.

**Rejected outright:** site demos, "how the pipeline works", anything with a UI chrome visible in frame.

**Format spec.** 20–26 s · 1080×1920 · text-led, no voice, music bed · four beats: **Setup** 0–4 s, **Hold** 4–12 s, **Reveal** 12–18 s, **Caveat + loop** 18–25 s · CRT/oscilloscope visual language, accent colour reserved for the reveal and the caveat only.

## 3 scripts

Rule for all three: **every hex, spectrum and palette ramp is exported from the site's own output for that planet.** Never eyeball a colour. Placeholders below are written `{true_hex}` / `{roman_hex}` — fill them from the planet page at render time.

### Script 1 — HD 189733 b · the credibility anchor

The one planet whose visible colour was actually *measured* (Hubble/STIS, 2013). Lead the series with it, because it earns the right to show modelled ones later.

| t (s) | Shot | On-screen text |
|---|---|---|
| 0.0–1.4 | Black. CRT grid fades to 20%. Two lines slam in, mono, huge. | **IT RAINS GLASS HERE** <br> sideways · 8,700 km/h winds |
| 1.4–4.0 | Planet disc appears **desaturated to grey**, 1°/s rotation. Slug bottom-left. | HD 189733 b · 63 light-years |
| 4.0–8.5 | Stat rows type on, one per 0.9 s, oscilloscope readout style. | ~1,000 °C dayside <br> clouds of silicate and quartz <br> tidally locked |
| 8.5–11.5 | Four labelled colour chips slide in beneath the grey disc. | **WHAT COLOUR IS IT?** |
| 11.5–13.5 | Chips pulse; a 3·2·1 counter ticks in the accent colour. | 3 · 2 · 1 |
| 13.5–14.0 | **Hard cut.** Disc floods with `{true_hex}`. Spectrum plot draws left→right underneath in 0.5 s. | **B** |
| 14.0–18.5 | Hold on the lit disc. Five-stop palette ramp slides up from the bottom. | Deep cobalt blue. <br> Not water — blue light scattering off molten glass droplets. |
| 18.5–22.0 | Accent-colour caveat bar, lower third. | Colour **measured** by Hubble, 2013. <br> One of the very few that were. |
| 22.0–24.0 | Disc desaturates to grey over 6 frames, cut to frame 0. | 5,700 more · `<SITE_URL>` |

### Script 2 — WASP-12b · the anti-reveal

The joke is that the payoff is *almost nothing*, and the number is the punchline. Subverted expectation is a retention mechanic in its own right.

| t (s) | Shot | On-screen text |
|---|---|---|
| 0.0–1.5 | Black. A single grey disc, barely visible against the background. | **THIS IS A PLANET** <br> you are not failing to see it |
| 1.5–4.5 | Disc slowly rotates. Nothing else happens. Deliberate dead air. | WASP-12b · 1,400 light-years |
| 4.5–9.0 | Stats type on. | 2,600 °C dayside <br> being torn apart by its star <br> so hot that hydrogen molecules break |
| 9.0–12.0 | Two reference chips slide in: lunar grey and asphalt. | HOW DARK? |
| 12.0–13.0 | Counter. | 3 · 2 · 1 |
| 13.0–14.0 | **Reveal:** the disc lights to `{true_hex}` — and it is near-black. Reference chips stay for contrast. | **0.064** |
| 14.0–19.0 | The albedo number scales up, then the comparison lands. | It reflects 6% of the light that hits it. <br> The Moon reflects twice as much. <br> Darker than fresh asphalt. |
| 19.0–22.0 | Caveat bar. | Hubble upper limit, 290–570 nm. <br> Nobody has ever photographed it. |
| 22.0–24.0 | Cut back to the near-invisible disc, loop. | `<SITE_URL>` |

### Script 3 — the Roman collapse · the once-per-quarter twist

The signature feature as a reveal. Pegged to the launch ([15-roman-launch.md](./15-roman-launch.md)) — currently scheduled for **30 August 2026** on a Falcon Heavy.

| t (s) | Shot | On-screen text |
|---|---|---|
| 0.0–1.5 | Six lit planet discs in a 2×3 grid, all in true colour, gently rotating. | **NASA'S NEXT TELESCOPE <br> SEES FOUR COLOURS** |
| 1.5–4.0 | Four narrow vertical bands sweep across the grid — 575, 660, 730, 835 nm — leaving the rest greyed. | that's it. four filters. |
| 4.0–7.5 | Grid holds in true colour. Prompt appears. | HOW MANY SURVIVE? |
| 7.5–9.0 | Counter over the grid. | 3 · 2 · 1 |
| 9.0–10.0 | **Snap.** All six discs jump simultaneously from `{true_hex}` to `{roman_hex}`. No transition — the hard cut is the whole effect. | — |
| 10.0–15.0 | Ticks/crosses stamp onto each disc in sequence, 0.5 s apart, as each is judged near-identical or collapsed. | ✓ HD 189733 b <br> ✓ Kepler-7b <br> ✗ … <br> **{n} of 6** |
| 15.0–19.5 | Grid holds. Verdict line. | Four bands keep most of the identity. <br> The blues survive. The subtle ones don't. |
| 19.5–23.0 | Caveat bar, then launch peg. | Modelled through the real Roman Coronagraph bandpasses. <br> Launches 30 Aug 2026. |
| 23.0–25.0 | Discs snap back to true colour, loop. | `<SITE_URL>` |

**Hook bank for future videos** (each is a verified fact, and each is a first-frame line): WASP-76b — iron vapour on the 2,400 °C dayside condenses and *rains as molten iron* on the 1,500 °C night side (VLT/ESPRESSO, *Nature*, 2020). HAT-P-7b — clouds of corundum, the mineral that makes rubies and sapphires, in winds that visibly change between orbits (Kepler, 2016). Kepler-7b — the first cloud map of another world, reflective clouds bunched 41° west of the substellar point, geometric albedo 0.35. GJ 1214 b — a Bond albedo of 0.51, half the light thrown straight back off a haze so thick JWST couldn't see through it. 55 Cancri e — the "diamond planet" headline is contested and *saying so on camera is the brand*; what JWST 2024 actually suggests is a second atmosphere outgassed from a magma ocean. TRAPPIST-1 — seven planets around a star so red that the colour of everything there is decided by the lamp, which is the six-suns format's best episode.

## Production cost

**Hours, honestly, for someone with no editing background:**

| | First video | Videos 2–5 | Steady state (template + exporter) |
|---|---|---|---|
| Asset generation | 1.5 h | 45 min | **10 min** (script params) |
| Edit / timing / text | 3–4 h | 2 h | 45 min |
| Captions, export, upload ×3 | 1 h | 45 min | 30 min |
| **Total** | **5–7 h** | **3.5 h** | **1.5 h** |

**Free tooling on a Mac, current:**

- **DaVinci Resolve (free tier)** — the right base. Genuinely full-featured, native 9:16 timelines, no watermark, no subscription. Steep for one evening, but the template is built once.
- **Not CapCut.** The Mac desktop build is locked to 16:9 with no native vertical output, which is disqualifying, and its licence terms drift.
- Fallbacks with weaker text tooling: Shotcut, Kdenlive, OpenShot — all free, all watermark-free, all 9:16 capable.
- **The actual cost saver is code, not editing.** This project can *render* frames rather than record them. `planet-render.js` and its share-card port already draw the disc; a headless-Chrome frame dump driven by a JSON script → `ffmpeg` gives pixel-perfect 60 fps clips with correct colours and zero manual keyframing. That is a **4–6 h build once** which collapses per-video asset work from 1.5 h to ~10 minutes, and it is a code task — the maintainer's actual skill — rather than a video-editing task. **If short-form ever happens, it happens because this exists first.**
- Music: platform in-app libraries only for TikTok/Reels/Shorts; YouTube Audio Library or CC0 for any self-hosted copy (a licensed track in a press-kit MP4 is a real problem).

**How many before you know:** **20–30 videos over 8–10 weeks**, at 3–5/week. Under 15 is noise — each video is independently tested, so the first several tell you nothing. That is **40–70 hours minimum to a real signal**, and that assumes the exporter exists.

**Against the rest of the plan:** [Show HN](./09-show-hn.md) is ~8 h for one shot at thousands of visitors. [Reddit](./10-reddit.md) is ~2 h per post. [SEO on planet pages](./03-seo-planet-pages.md) is one session that compounds forever across 5,700 URLs. [Crediting and emailing the scientists](./13-credit-the-scientists.md) is ~6 h for the highest-trust outcome available. Short-form is **roughly an order of magnitude worse** on hours-to-visitors than any of them.

## Platforms

- **YouTube Shorts — the one worth the effort.** Only platform where the description link is clickable for everyone with no follower gate; the only one with *search and a long tail* (a Short from 2026 still surfaces in 2028, which matters enormously for an evergreen catalogue of 5,700 planets); and the only one where the Shorts feed a channel that could later host a five-minute "how the colours are computed". Audience match for space explainers is strongest here.
- **TikTok — biggest ceiling, worst conversion.** Best cold-start discovery for a faceless account by a distance. But: link-in-bio only, and bio-link CTR benchmarks run ~1–3% *of profile visitors*, while profile visits are themselves a low-single-digit share of views. Realistic view→site conversion is **0.01–0.1%**. 100,000 views is maybe 30–100 sessions. Plan for that number, not for the view count.
- **Instagram Reels — worst discovery, best audience match for the design half.** Colour and palette accounts live here and the currency is *saves and shares*, not clicks. If Reels is used, measure save rate and treat traffic as a bonus.
- **Cross-posting is not penalised across platforms** — they do not detect each other. But a **visible TikTok watermark suppresses Reels reach substantially** (reported 40–70%). The rule is absolute: export one clean master from Resolve and upload it natively to all three. Never download from TikTok to repost.
- **The honest weakness.** Short-form does not send traffic to websites, full stop. Anyone claiming otherwise is selling a link-in-bio tool. Mitigations that genuinely help: burn `<SITE_URL>` **in-frame as static text** on the last two seconds (survives re-uploads and screen-recording theft), pin a comment containing the URL, and keep the domain short enough to type from memory. Accept that a meaningful share of any traffic will arrive as *direct type-ins* and be invisible to attribution.

## The verdict

**Do it later, conditionally — and never as a "content channel". Three parts:**

**1. Not now. Not close.** Every Phase 0 and Phase 1 item on the [board](./README.md) beats it on every axis. Firing 40–70 hours at an unproven channel while the credits page, the press kit, and Show HN are undone would be the single worst allocation available.

**2. Do build the clip exporter, though — as a code task, not a video task.** 4–6 hours, and it is *not* spent on this doc: a silent 15-second MP4 of the true→Roman snap is the highest-value asset the project can own, and its first homes are [Bluesky/Mastodon](./11-bluesky-mastodon.md) (video massively outperforms stills there), a [Reddit](./10-reddit.md) post, the [press kit](./02-press-kit.md), and the [Roman launch](./15-roman-launch.md) push. Five docs use it. Short-form is the fifth, not the first.

**3. Revisit as a channel at month 4**, and only if **all three** gates pass: (a) the site has a real audience and referral base, so a video has somewhere to send people; (b) the exporter exists and per-video cost is under ~90 minutes; (c) the maintainer will genuinely commit 3 posts/week for 8 weeks. **If you can't commit to 20 videos, post zero** — 5 videos is not a small experiment, it's a wasted one.

**On the Roman window specifically:** the launch is roughly four weeks out. That is *not* enough runway to build a cold account into it, and trying is the classic failure mode — a brand-new account's first videos get the smallest test audiences precisely when the peg is live. Make the Roman clip and post it where there is already an audience. Do not open a TikTok account in August.

**What would turn this into a clear yes:** the exporter dropping per-video cost below ~45 minutes; *or* one clip posted on an existing channel organically clearing ~50k views, which would be evidence the reveal lands without needing an algorithm to be courted; *or* a collaborator who edits.

**What would make it a permanent no:** 20 videos in, median views under 2,000 and under 100 total sessions to the site. At that point the format has been tested fairly and lost.

## How we'll know it worked

- **Primary:** sessions with `utm_source` in (`tiktok`, `reels`, `shorts`). **Bar after 20 videos: 300 sessions total.** Below that, stop. This is a deliberately low bar and it is still hard.
- **The metric that actually matters, since clicks won't come:** *median views per video at #10 vs #20*. Rising means the account is learning; flat means the format doesn't fit the medium and no amount of persistence fixes it.
- **Retention:** average watch ≥60% with a flat curve. A cliff at second 3 means the hook is wrong; a cliff at the reveal means the payoff isn't one.
- **Comments per reveal video** — the guess format's own signal. If people aren't posting their guess, the quiz isn't working.
- **UTM:** `?utm_source=<tiktok|reels|shorts>&utm_medium=video&utm_campaign=guess-the-colour&utm_content=<planet-slug>`. Because most viewers type the URL rather than click, also stand up a short vanity path per campaign so type-ins are attributable at all. Scheme in [99-tracking.md](./99-tracking.md).

## Risks

- **Sunk evenings.** The highest hours-per-outcome item in the plan, and the one most likely to feel productive while achieving nothing.
- **Honesty erosion — the serious one.** The format's power is the reveal, and the reveal's temptation is to say "this is what the planet looks like". Every video must carry *modelled from physics* or *measured* **in frame**, never only in the description. Short-form strips context by design; a clip re-uploaded without its caption must still be honest. This is non-negotiable — it is the positioning ([README](./README.md)).
- **Fake-space-image backlash.** Astronomy audiences are primed to punish AI and artist renders passed off as real. Being the honest one is protection *only if the honesty is visible in the frame*. It also means avoiding the visual grammar of the AI-voiced space channels entirely.
- **Music licensing.** In-app libraries are fine on-platform and a liability the moment the same MP4 is self-hosted.
- **Unbudgeted time:** comment moderation, DMs, and the pull to post daily.
- **Format fatigue.** Guess-the-colour tires somewhere around video 40. The six-suns loop and the countdown exist as variants — do not start the series without them planned.
- **Opportunity cost against the Roman window,** covered above: the temptation to rush a channel into a launch that is four weeks away is the specific mistake this doc exists to prevent.

## Links

- [Marketing plan](./README.md) — hub; the positioning line every script has to survive
- [15-roman-launch.md](./15-roman-launch.md) — Script 3's peg, and the reason to build the clip exporter regardless of this doc's verdict
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — where the clips should actually be posted first; video outperforms stills and the audience is already there
- [99-tracking.md](./99-tracking.md) — UTM scheme, and the vanity-path workaround for untrackable type-ins
- [09-show-hn.md](./09-show-hn.md) — the direct comparison on hours-to-visitors; do this first
- [07-wallpapers.md](./07-wallpapers.md) — shares the render pipeline; if the exporter gets built, both benefit
- [01-newsjacking.md](./01-newsjacking.md) — a 15 s clip is the strongest possible newsjack payload
- [02-press-kit.md](./02-press-kit.md) — needs a self-hostable, correctly-licensed motion asset
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — Script 1 rests on Evans et al. 2013 and Script 3 on the Roman CGI bandpasses; credit before broadcast
- [10-reddit.md](./10-reddit.md) — the other home for the clips, with a real conversion path
- [12-design-newsletters.md](./12-design-newsletters.md) — the Reels audience overlaps the design half of the project
