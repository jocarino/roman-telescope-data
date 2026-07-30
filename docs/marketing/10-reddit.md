# Reddit

**Status:** not started · **Effort:** high (6 weeks of drip, ~3 evenings of asset-building) · **Payoff:** high but spiky — one r/dataisbeautiful hit outweighs everything else combined · **Hub:** [Marketing plan](./README.md)

## The bet

Reddit is the only free channel where a physics-derived colour catalogue can reach millions of people who have never heard of a geometric albedo. The bet is **not** "post the link in space subs" — that gets removed as blogspam almost everywhere. The bet is that we build **four small static artifacts** (an image, a wallpaper pack, a printable guide, a mosaic), each shaped to one subreddit's culture, and let the site be the thing people find *after* the artifact earned the upvote. Everything hinges on one asset: a single image that shows what survives when you look at 5,764 worlds through Roman's four filters instead of the full spectrum.

## The subreddit map

Subscriber counts pulled from Reddit's own `about.json` on **2026-07-30**. Rules quoted from each sub's `about/rules.json` on the same date. Note: **no subreddit publishes its AutoModerator karma/age thresholds** — they are invisible until you trip them. Assume every large sub silently filters accounts under ~30 days old with near-zero comment karma, and plan the account hygiene below accordingly.

> **Provenance warning (added on review, 2026-07-30).** Reddit now returns
> `403 — you've been blocked by network security` to *every* unauthenticated request, including
> `about.json` and `about/rules.json`, from any user-agent; the public mirrors (redlib/libreddit)
> are all behind bot challenges. That means these quotes could not be independently re-verified,
> and neither can they be refreshed by a script. **Before each post, open the sub's rules page in
> a logged-in browser and screenshot it into `docs/marketing/evidence/`.** Until that is done,
> treat every verbatim quote below as a paraphrase. Cross-checks that *were* possible are marked
> ✅ inline. A rule quote you cannot produce a screenshot of is not a rule you can plan around.

| Sub | Subs | Verdict | Why |
|---|---|---|---|
| r/dataisbeautiful | 21.8M ✅ | **GO — priority 1** | Exactly our shape, *if* the artifact is a chart and not a colour swatch (see rework note) |
| r/space | 27.9M ✅ | **GO — weekend image only** | Images allowed Sat/Sun only; link posts = blogspam |
| r/Amoledbackgrounds | 324k ✅ | **GO — needs the wallpaper pack** | Clear mechanical rules, but small ceiling: median top-100 post ≈380 upvotes |
| r/exoplanets | 15.9k | **GO — start here** | Tiny but the exact audience; forgiving; free corrections |
| r/InternetIsBeautiful | 16.6M ✅ | Maybe — week 5+, conditional | See the downgrade note below: ~1 post/day survives, median top-100 ≈490 |
| r/datasets | 204k ✅ | GO — near-zero risk | On-topic by definition once `06-open-data.md` ships. Low ceiling (median top-100 ≈17) but permanent and citable |
| r/coolguides | 6.1M ✅ | **GO — needs the printable guide** | Best risk/reward on the list: ~3 posts/day, median top-100 ≈7,200 upvotes |
| r/Astrobiology | 35.8k | GO — habitable-zone angle | Small, on-topic, low risk |
| r/generative | 98k | GO — mosaic only | Explicitly allows relevant self-promo |
| r/proceduralgeneration | 125k | GO — mosaic only | Same asset, different framing |
| r/wallpapers | 736k | GO — reuse Amoled pack | Low effort once pack exists |
| r/spaceporn | 4.3M | Maybe — images only, approved hosts | Renders are "simulations", allowed; no website links |
| r/telescopes | 259k | Maybe — Roman/CGI angle | Needs a real top-level commentary |
| r/SideProject | 793k | Maybe — low-quality traffic | Founders talking to founders |
| r/astronomy | 3.1M | **NO-GO** | Rule bans "infographics, apps" outright |
| r/Physics | 3.2M | **NO-GO** | Bans image posts and "zero-content" submissions |
| r/somethingimade | 3.1M | **NO-GO** | Handmade only; digital work and apps excluded |
| r/graphic_design, r/design, r/web_design | 2.9M / 4.5M / 974k | **NO-GO** | Portfolio/critique culture; a link drop reads as spam |
| r/colors | 25k | **Waste of time** | 25k members, low velocity; nice-to-have at best |
| r/Colorpalettes | **7** | **Dead** | Restricted, 7 members. r/colorpalette does not exist |
| r/EarthPorn | 23.6M | **Irrelevant** | Real photographs of Earth. Our images are modelled. Do not |
| r/askastronomy | 173k | **NO-GO for posting** | Q&A sub. Answering questions there is fine — that's karma-building, not promotion |
| r/NASA, r/SpaceXLounge, r/spaceflight | 5.9M / 384k / 312k | Hold for launch | Only relevant when Roman actually flies — see `15-roman-launch.md` |

### Per-sub notes

**r/dataisbeautiful (21.8M) — the whole campaign in one post.**
Rules that bind us, verbatim: *"A post must be or contain a qualifying data visualisation."* · *"[OC] posts must state the data source(s) and tool(s) used in the first top-level comment on their submission."* · *"Directly link to the original source article of the visualization... If you made the visualization yourself, tag it as [OC]."* · *"Post titles must describe the data plainly without using sensationalized headlines. Clickbait posts will be removed."* · *"No reposts of popular posts within 1 month."*
Two scheduling traps: *"Posts regarding Personal Data are permissible only on Mondays (ET)"* and *"Posts involving U.S. politics are allowed only on Thursday (ET)"* — neither applies to us, but both crowd the queue. Post **Tuesday or Wednesday, ~08:00 ET**.
What performs: a *single image*, self-explanatory in three seconds, with an axis and a legend. Interactive sites and gallery links reliably underperform or get pulled. Angle: temperature-ordered colour strip, true-colour vs Roman.
**The removal risk this section understates.** Rule 1 is *"must be or contain a qualifying data visualisation"*, and the most common removal on that sub is "this is data art, not a visualisation." Two flat bands of colour, ordered by temperature, encode exactly one variable (order) — a mod scrolling the queue can read it as decoration. **Do not submit the strips alone.** The submission must *contain* a quantitative chart: put ΔE (the colour distance between the full-spectrum colour and the four-band reconstruction) on a y-axis against equilibrium temperature on the x, and run the two strips as a band underneath, sharing the x-axis. Then the pretty thing rides along on something that qualifies. Two more mechanics the plan omits: **the post needs a flair** (unflaired submissions are auto-removed), and the source/tools comment must go up **immediately** — the OC bot removes posts missing it, it does not wait. Also: DIB posts live or die in the first 60–90 minutes, so block out four hours, don't just pick a timeslot.

**r/space (27.9M) — one shot, one Saturday.**
*"Images, gifs, and gif-like videos... are permitted only on weekends."* · *"No low-effort, meme, or AI generated images are permitted at any time."* · *"No AI generated content — This includes both AI generated images/artwork and text generated by tools such as ChatGPT."* · *"No spam/blogspam/paywalled/pirated content."* · *"If an image is not OC you must give credit to the original photographer."* · *"Please limit yourself to no more than 5 submissions per 24 hour period."*
Read that AI rule carefully: our renders are *computed from physics*, not generated by a diffusion model, and the post must say so in the first sentence or a mod will assume the worst. A **link post to `<SITE_URL>` will be removed as blogspam** — post the image, put the URL in your own top-level comment.

**r/astronomy (3.1M) — do not bother.**
*"Rage comics, memes, infographics, apps, etc... are not allowed."* An interactive colour catalogue is an "app"; a colour strip is an "infographic". Both are named in the rule. Also *"Primary or reputable secondary sources ONLY"* and image submissions must be *"original content and include acquisition and processing information"* — i.e. real astrophotography with exposure data. There is no version of this project that fits. Skip it and spend the evening on r/exoplanets instead.

**r/exoplanets (15.9k) — the rehearsal room.**
*"Posts and comments should rely on peer-reviewed research, reputable sources, or established scientific knowledge."* · *"Cite Sources When Possible — When sharing research, discoveries, or scientific claims, include citations, links to journals, or credible scientific publications."* Small, but the people who will find the actual bugs. Cite Cahoy et al. 2010, PICASO, and the NASA Exoplanet Archive in the post body itself. Expect corrections; take them publicly and gratefully — that thread becomes the credibility receipt you link to elsewhere.

**r/InternetIsBeautiful (16.6M) — downgraded on review: high variance, low expected value.**
The subscriber count is a mirage. ✅ The sub accepts roughly **one post per day**, its median top-100 post of the year earns **~490 upvotes**, and its best post of the year reached **16.4k** — i.e. a 16.6M-member sub that behaves like a 200k one, because almost everything is removed. Treat it as a lottery ticket with a modest prize, not as "the largest single traffic spike of the campaign." It does not deserve to be the thing weeks −3 to 0 are structured around.
*"This sub follows the 90/10 rule for self-promotion. If almost all your recent activity on Reddit is advertising something you made, you will not be allowed to post here. 90% of your recent participation on Reddit should have nothing to do with a site you own or operate."* This is checked against your visible post history. Two other hazards: *"No Aggregations or Collections — Websites that are aggregates for other content are not allowed"* and *"No Articles, Videos or Images... this includes collections (such as galleries)"* — a 5,764-swatch gallery can be read as a collection. **Mitigation: lead with the Roman toggle, not the gallery.** Frame it as a tool that does something ("switch a telescope's filter set on and see the colour change"), not a catalogue. Also: *"submissions are not allowed if their primary content is produced by AI, or if AI is used to drive functionality"* — we're clean, but say it.

**r/coolguides (6.1M) — mechanically easy, if you follow the format.**
*"all posts must be prefixed with 'A cool guide'"* · *"Only direct links to images of type .png, .jpg, and .jpeg are allowed"* · *"Image hosts must either be Reddit or Imgur"* · *"Infographics will be removed — ...If your guide is more of a visual essay than a structured table or list, [it will be removed]."* That last one is the trap: build a **table**, not a poster.

**r/Amoledbackgrounds (324k ✅) — the most rule-shaped sub on the list, and the smallest prize.**
Its public description reads *"Backgrounds for OLED phones, mainly black for screen power saving and contrast. **No AI allowed.**"* ✅ — the AI ban is in the one-line description, not buried in rule 7, which tells you how hard they enforce it. Median top-100 post ≈380 upvotes. Also: these subs expect **one wallpaper per post**, not a pack; a post whose source comment points at a download page on your own domain is the exact shape of the funnel they remove. Post a single image, and offer the rest only if someone asks.
*"Submissions should be at least 50% true black in colour, as in #000000."* · *"Include your submission source in a top-level comment on your post (include one of the keywords `source`, `credit`, or `original` in your comment)."* · *"Reposting is not allowed."* · *"Be ready to provide an uncompressed link if asked."* A planet disc on `#000000` clears the 50% bar trivially. Requires an actual wallpaper pack at real device resolutions — see below and `07-wallpapers.md`.

**r/generative (98k) / r/proceduralgeneration (125k).** r/generative: *"Self-promotion is allowed, but it must be relevant and non-excessive"* and *"do not post AI-generated work here, note that this does not apply to your own algorithms."* Our pipeline is exactly "your own algorithm". r/proceduralgeneration: *"No AI-written posts/comments"* — write the post yourself, in your own voice.

**r/spaceporn (4.3M).** *"Only images are allowed. Videos, interactive images/websites, memes, and articles are not allowed."* Simulations and artist's depictions are explicitly in scope. Approved image hosts only. Decent reach for zero extra work once the wallpapers exist, but the audience converts poorly — it's a scroll-past sub.

**r/telescopes (259k).** *"Direct links should be accompanied by commentary as a top level comment, and should be a source of discussion."* The only honest angle is the /roman target board: "here's what CGI's four bands can and can't recover." Small, but the right people.

## Features worth building for a specific sub

Five artifacts. Every one of them is reusable on the site — nothing here is throwaway marketing collateral.

### 1. The two-strip chart — *"Every known exoplanet, true colour vs Roman's four bands"* — **build this first**
**What:** one static PNG. All 5,764 planets as vertical lines, ordered left→right by equilibrium temperature, drawn in their computed hex.
**Fix the geometry before you build it:** 5,764 one-pixel columns do not fit in a 2400px-wide image. At 2400px each planet gets 0.42px and the renderer averages neighbours into mush — the divergence between the two strips, which is the entire point, is the first thing lost to aliasing. Either render **5,764 px wide** (and accept that Reddit's viewer downsamples it, so ship a cropped detail inset too) or **bin the temperature axis** into ~400 bins and draw the median colour per bin, saying so in the caption. Binning is the honest choice and it survives a phone screen. Two stacked strips in identical order: top = full-spectrum colour, bottom = the four-band Roman reconstruction. Temperature axis underneath; a handful of annotated anchors (Neptune, Jupiter, HD 189733 b, the hottest ultra-hot Jupiter). A caption band stating model assumptions.
**Why it's novel:** nobody has published a picture of *what a filter set costs you*. The eye reads the answer instantly — where the two strips match, Roman recovers the colour; where they diverge (methane-band worlds, most likely), it doesn't. That is the project's thesis rendered as one image.
**Work:** ~1 evening. `planets.json` already holds both colours; it's a PIL/matplotlib script in `pipeline/`.
**Unlocks:** r/dataisbeautiful (priority 1), r/space (as the weekend image), r/visualization, r/datavisualization.
**Reuse:** hero image for `/roman`, the default OG card, and figure 1 of the press kit (`02-press-kit.md`).

### 2. The calibration figure — *"Five planets we can check"* — **build this second, it is your armour**
**What:** a small figure: the five solar-system anchors, each showing (a) the colour computed from measured spectra by our pipeline, (b) the colour sampled from a real photograph, (c) the ΔE between them, as a number.
**Why:** it is the single most credible thing the project owns, and it is the pre-loaded answer to "is this AI slop?" — you don't argue, you link the figure. It also makes r/exoplanets and r/Astrobiology respect the post instead of tolerating it.
**Work:** half an evening; the data exists.
**Unlocks:** r/exoplanets, r/Astrobiology, and every comment thread everywhere.
**Reuse:** the site's "how do we know this works" panel; `13-credit-the-scientists.md`.

### 3. True-black wallpaper pack
**What:** per-planet phone wallpapers: the planet disc render centred on pure `#000000`, name + hex + host star in small mono type, retro-CRT styling intact. Ship exact resolutions — **1080×2400, 1440×3200, 1284×2778** — plus a desktop 3840×2160. Start with 12 hand-picked planets, not 5,764.
**Work:** ~half a day, reusing the OG-card disc shader headlessly.
**Unlocks:** r/Amoledbackgrounds, r/wallpapers, r/spaceporn.
**Reuse:** a `/wallpapers` page on the site — see `07-wallpapers.md`, which this feeds directly.

### 4. *"A cool guide to why exoplanets are the colours they are"*
**What:** one PNG, laid out as a **table** (their rule bans visual-essay infographics). Rows = cause: methane absorption · thick water/ammonia clouds · no clouds at all · sodium/potassium · thermal glow. Columns = swatch | what it does to the reflected spectrum | a real example planet | its hex. Footer line: "modelled, not photographed."
**Work:** ~2 hours as HTML → screenshot.
**Unlocks:** r/coolguides (6.1M, and the artifact is *exactly* what performs there).
**Reuse:** the site's "how to read a swatch" explainer; hands educators a printable — see `14-educators.md`.

### 5. The catalogue mosaic
**What:** all 5,764 planet colours as packed circles — radius = planet radius, position = orbital distance or insolation. One dense, genuinely pretty image where the structure is real data, not decoration.
**Work:** ~1 evening (circle packing is the only new code).
**Unlocks:** r/generative, r/proceduralgeneration.
**Reuse:** an about-page banner; decent Bluesky/Mastodon fodder (`11-bluesky-mastodon.md`).

**Explicitly not worth building:** a "copyable palette image" for r/colors / r/design. r/colors has 25k members and low velocity; the design subs are no-go. The palette export already exists on-site (`05-machine-readable.md`) — don't build an image format to serve a dead sub.

## The sequence

Never two posts on the same day. Never the same text twice — mods and users both notice cross-posted boilerplate, and it's the fastest way to get flagged as a spam account.

**Weeks −3 to 0 — account hygiene, no posting at all.** Use a real account with history; a fresh one will be silently AutoMod-filtered in every large sub here. If the only account is new, spend three weeks *commenting*: answer questions in r/askastronomy and r/exoplanets, help people in r/telescopes. Target ~200+ comment karma and 30+ days of age before week 1.

**Correction on the 9:1 rule.** ✅ Reddit **retired the site-wide 9:1 / 90-10 self-promotion guideline years ago**; there is no longer an official Reddit self-promotion page, and no admin enforces a ratio. What survives is (a) per-sub rules that write it down themselves — r/InternetIsBeautiful's 90/10 is a real, quoted, hand-enforced rule — and (b) mod instinct. So don't count to nine. What a mod actually checks, in this order: *do you have comment history **in this sub** before today* → *does every submission you've ever made point at one domain* → *are you replying to questions in your own thread*. The first is worth more than the other two combined and is not a ratio: **five real comments in the target sub beats 500 karma farmed elsewhere.** Farming generic karma to hit a number produces exactly the account shape that gets flagged.

**What the plan is missing entirely: the three silent failures.** All three are invisible from a logged-in session, which is why people re-post and get banned for it.
1. **Shadowban (account).** Open your profile in a **logged-out private window** at `reddit.com/user/<name>`. Empty or 404 = shadowbanned. Do this before week 1 and after any removal.
2. **Silent AutoMod filter (karma/age gate).** No sub publishes its thresholds. Test cheaply: leave one ordinary comment in the sub's daily/weekly thread, then check that comment **logged out**. If it's invisible to logged-out eyes, your account is filtered there and every post you make will vanish without a modmail.
3. **Domain ban (site-wide or per-sub).** A domain can be blocked and you will never be told; your post simply never appears. Test: comment your bare URL in **r/test**, then view that comment logged out. If it's gone, the domain is on a site-wide list and *nothing* in this plan works until it's appealed. Per-sub, just ask: a two-line modmail — *"I made X, is it in scope here, and is `<domain>` allowed?"* — gets an answer, costs nothing, and pre-registers you as someone who asked first.
4. **Never re-upload the identical image file across subs.** Reddit's spam filter matches image hashes; the same PNG in three subs inside a week is a stronger spam signal than the same title. Re-render at different dimensions for each.

| Week | Sub | Artifact | Notes |
|---|---|---|---|
| 1 | r/exoplanets | Link + calibration figure | Tue eve. Low stakes, harvest corrections |
| 1 | r/Astrobiology | Habitable-zone lens (68 candidates) | Fri, different text entirely |
| 2 | **r/dataisbeautiful** | **Two-strip chart [OC]** | **Tue or Wed 08:00 ET.** The one that matters |
| 3 | r/Amoledbackgrounds | Wallpaper pack | Weekday. Source comment mandatory |
| 3 | r/wallpapers | Same pack, new title | 3+ days later |
| 4 | r/space | Two-strip chart as image | **Saturday only.** Link in a comment, never the post |
| 5 | r/InternetIsBeautiful | The site, framed as the Roman toggle | Needs the 9:1 history to now be true |
| 5 | r/coolguides | "A cool guide..." table | 3 days after IIB |
| 6 | r/generative + r/proceduralgeneration | Mosaic | Split across two days, different text |
| Reserve | r/telescopes, r/spaceporn, r/SideProject | — | Only if weeks 1–6 went clean |

If a post lands hard (front page), **stop for a week**. A cluster of self-promo posts right after a hit is what gets accounts shadowbanned.

## Copy

**r/exoplanets** — title: `Computed the visible colour of 5,764 known exoplanets from albedo models + host-star spectra (PICASO / Cahoy grids, CIE 1931)`
Body: *"Every colour here is modelled, not observed — reflected-light albedo spectra multiplied by the host star's spectrum, convolved with the CIE 1931 2° colour-matching functions, then converted to sRGB. Sources: NASA Exoplanet Archive (pscomppars), PICASO, Cahoy et al. 2010. As a sanity check I ran the same pipeline on five solar-system planets using measured spectra and compared the output to real photographs [figure]. Microlensing planets are flagged model-only, since no light from them has ever been received. Assumptions per planet (cloud state, metallicity, phase angle) are stated on each page: `<SITE_URL>`. Corrections very welcome — particularly on the cloud-deck assumptions."*

**r/dataisbeautiful** — title: `[OC] The colour of 5,764 known exoplanets, ordered by equilibrium temperature — full modelled spectrum vs. only the four Roman Coronagraph bands`
Mandatory first top-level comment: *"**Source:** NASA Exoplanet Archive (pscomppars table), accessed 2026-07-XX. Albedo spectra from PICASO and the Cahoy et al. 2010 model grids. **Tools:** Python — PICASO for the reflected-light spectra, colour-science for CIE 1931 → sRGB, matplotlib/Pillow for the render. Each planet is one 1px column, coloured by its computed sRGB hex. Top strip is the colour from the full 380–780 nm spectrum; bottom strip is the colour reconstructed from only the four Roman Coronagraph filter bands (575, 660, 730, 835 nm). These are modelled colours, not photographs — no exoplanet has ever been photographed in visible colour. Method and per-planet assumptions: `<SITE_URL>?utm_source=reddit&utm_medium=social&utm_campaign=dataisbeautiful`"*

**r/space** (Saturday only) — title: `The modelled visible colour of every known exoplanet, sorted by temperature — and how much of that colour Roman's coronagraph would actually recover`
First comment: *"Not AI-generated. These are physics: geometric albedo spectra (PICASO / Cahoy et al. 2010) times each host star's spectrum, run through the CIE 1931 colour-matching functions. Planet parameters from the NASA Exoplanet Archive. No exoplanet has ever had its visible colour measured directly — HD 189733 b's blue is the closest thing, from Hubble polarimetry. Full method, and the five solar-system planets I used to check the pipeline against real photographs: `<SITE_URL>?utm_source=reddit&utm_medium=social&utm_campaign=space`"*

**r/Amoledbackgrounds** — title: `[1440x3200] Exoplanet colours computed from physics — true black background`
Mandatory source comment: *"**Source:** made these myself. The disc colour for each one is computed from the planet's modelled reflected-light spectrum (PICASO albedo models × the host star's spectrum → CIE 1931 → sRGB), not picked by hand. Background is pure #000000. Other resolutions and the rest of the catalogue: `<SITE_URL>/wallpapers?utm_source=reddit&utm_medium=social&utm_campaign=amoled` — happy to post uncompressed PNGs if anyone wants them."*

**r/InternetIsBeautiful** — title: `A site that computes what colour every known exoplanet would be, and lets you switch between the full spectrum and the four filters the Roman telescope will actually use`
First comment: *"I built this. It isn't a gallery of pictures — the interesting bit is the toggle: flip it and every colour on the page is recomputed from just Roman's four coronagraph bands instead of the full 380–780 nm spectrum, so you can see how much colour identity a real filter set throws away. Nothing here is AI-generated; it's a Python pipeline over NASA Exoplanet Archive parameters and published albedo models. Every colour is labelled as modelled rather than photographed, because none of them have ever been photographed."*

## How we'll know it worked

PostHog is cookieless, so **UTM tags are the only reliable attribution** — Reddit strips referrers on some clients. Tag every link `?utm_source=reddit&utm_medium=social&utm_campaign=<subreddit>`, lowercase, exact sub name. Set up the dashboard before week 1 (`99-tracking.md`).

| Sub | Metric that means it worked |
|---|---|
| r/exoplanets | ≥1 substantive scientific correction in the thread. Traffic is not the point |
| r/dataisbeautiful | ≥2,000 upvotes and ≥3,000 sessions on `utm_campaign=dataisbeautiful`; the real signal is whether the Roman toggle gets used in >30% of those sessions |
| r/space | ≥1,000 sessions and *not being removed* — surviving 24h in a 27.9M sub is the win |
| r/Amoledbackgrounds | ≥300 wallpaper downloads; feeds the `07-wallpapers.md` decision on whether to render all 5,764 |
| r/InternetIsBeautiful | Binary: did it survive the mod queue. If yes, expect the largest single traffic spike of the campaign |
| r/coolguides | ≥500 upvotes; watch whether anyone asks for a printable version (→ `14-educators.md`) |

Site-wide target for the six weeks: **15,000 sessions from `utm_source=reddit`**, and — more important — a median session that includes at least one planet page and one toggle interaction. High-bounce upvote traffic is not worth a ban.

## Risks

- **Blogspam removal (likely, r/space and most science subs).** A link post to your own domain is the single most-removed thing on Reddit. Mitigation: image post + link in your own comment, everywhere it's permitted.
- **The 90/10 rule (r/InternetIsBeautiful, enforced by hand).** If weeks 1–4 are all self-promo posts, week 5 is dead on arrival. The comment-building in weeks −3 to 0 is not optional padding; it's the entry fee.
- **"Is this AI slop?"** — the accusation you will definitely get, because coloured planet discs look like Midjourney output. Do not get defensive and do not write a wall of text. The answer is three moves, in this order: (1) "It's a physics pipeline, not a generative model — here's the source code and the albedo grids it uses." (2) Link the five-planet calibration figure: measured spectra in, real photographs to compare against, ΔE stated. (3) "Every colour on the site is labelled modelled, not photographed, because none of them have ever been photographed." Then stop replying. The figure does the arguing.
- **Mod removal.** Message modmail **once**, politely, with the specific rule you believe you satisfied, and ask what would make it acceptable. Never re-post the same content to the same sub without a mod's go-ahead, and never argue in public comments — public mod-arguing is how sub bans become sitewide ones. If they say no, accept it and move on; there are ten other subs on this list.
- **Shadowban / spam filter.** Posting the same domain to several subs in one day is the trigger. The schedule above exists mostly to avoid this.
- **AI-content rules are tightening everywhere** (r/space, r/InternetIsBeautiful, r/generative, r/proceduralgeneration, r/somethingimade all ban it explicitly as of 2026). Write every post and comment yourself. A post that reads as LLM-generated will be removed even though the underlying work isn't.
- **The schedule is itself the biggest risk.** Ten subreddits, one domain, one account, six weeks is the textbook pattern site-wide spam detection is built to catch — every individual post can be rule-compliant and the *aggregate* still trips it. Nothing else in this document is as dangerous as its own calendar. Halve it.
- **The top comment that kills the thread, and it isn't "is this AI".** It's a working astronomer writing *"the albedo models are unconstrained for all but a handful of these planets, so these colours are essentially free parameters."* That is a fair hit and it will be upvoted above yours. Have the answer written before you post, and make it a concession, not a defence: which planets have observationally constrained albedos, which are grid interpolation, and where the site says so. If the site doesn't currently distinguish those two tiers per planet, **that is a product change to make before posting**, not a comment to write.
- **Rules change.** Re-read the sidebar the morning of each post. This map is a snapshot of 2026-07-30.

## Links

- [Marketing plan](./README.md) — hub
- [07-wallpapers.md](./07-wallpapers.md) — the wallpaper pack r/Amoledbackgrounds requires; this doc is the demand case for it
- [09-show-hn.md](./09-show-hn.md) — same launch window, different culture; don't run both in the same week
- [02-press-kit.md](./02-press-kit.md) — the two-strip chart and calibration figure are press-kit figures 1 and 2
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the citations that make the r/exoplanets and r/Astrobiology posts credible
- [14-educators.md](./14-educators.md) — the r/coolguides table doubles as the classroom printable
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — reuses all five artifacts, no rules to fight
- [99-tracking.md](./99-tracking.md) — UTM scheme and the PostHog dashboard this plan reports against
- [15-roman-launch.md](./15-roman-launch.md) — where r/NASA, r/spaceflight and r/SpaceXLounge become worth posting to
- [01-newsjacking.md](./01-newsjacking.md) — a new exoplanet result is the one time a same-week second Reddit post is defensible
