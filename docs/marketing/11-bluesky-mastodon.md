# Bluesky & Mastodon

**Status:** not started · **Effort:** medium (one evening to set up, ~20 min/week after) · **Payoff:** high — this is where working astronomers actually are · **Hub:** [Marketing plan](./README.md)

## The bet

Working exoplanet scientists, planetary scientists and space journalists moved to Bluesky and stayed; a smaller, older, more accessibility-conscious slice sits on Mastodon. Both reward a person who shows their work and punish a brand that broadcasts. Our unfair advantage is that we can produce a *genuinely new image* every single day — 5,700 planets, each with a physically-derived colour nobody has published before — which is exactly the raw material these platforms starve for. The bet is that a daily planet swatch with one honest sentence of physics earns follows from the researchers whose papers we're consuming, and that a handful of those follows is worth more than 10,000 anonymous impressions.

## Account decision

**Recommendation: personal account as the primary voice on both platforms. Add a separate project *bot* account on Bluesky only, and not until week 7.**

The reasoning is not vibes — it is visible in the follower data. Verified 2026-07-30 via the public AT Protocol API:

| Account | Posts | Followers | What it is |
|---|---|---|---|
| `@astrophep-bot.bsky.social` | 8,267 | **75** | arXiv astro-ph.EP firehose |
| `@exocourier.bsky.social` | 6,654 | **90** | exoplanet news bot |
| `@theplanetaryguy.com` (Paul Byrne) | 3,464 | **18,230** | one planetary scientist posting as himself |

Pure-output bot accounts on Bluesky do not grow, no matter how good the output. Two exoplanet bots have posted ~15,000 times between them for a combined 165 followers. A single human posting a third as much has 18,000. Reach on Bluesky comes from replies and reposts by humans, and humans repost humans.

There is a second, harder reason. Bluesky's astronomy distribution runs through the **Astrosky feed network** (below), and its signup is *per-account* and gated on the account being "a scientist, science organization, or hobbyist astronomer." That is a judgement about a person. A personal account that also replies about lunch reads as a hobbyist astronomer; a faceless `@exoplanetpalette` posting 5,700 scheduled images reads as a content farm, and one moderator decision removes the entire distribution channel.

So:

- **Personal account, both platforms.** Bio names the project and links `<SITE_URL>`. This does the threads, the replies, the "I found something weird in the data tonight" posts. It is where ~80% of the value is.
- **Mixing audiences is fine and is the point.** The occasional non-astronomy post is what marks you as a human. The only real cost is if your personal account has an existing incompatible identity (heavy politics, employer-sensitive). If so, make a *new* personal account under your own name — still a person, just a fresh one — rather than a brand.
- **Project bot account on Bluesky, week 7+, clearly labelled** (`🤖 automated · run by @you`). It carries the daily planet queue so your personal timeline isn't 365 near-identical images. You boost it manually ~2× a week with commentary. Do not expect it to grow; it is a *utility*, not a channel.
- **No bot account on Mastodon.** Anti-automation norms are stronger there and the natural astronomy home is gone (below). One human account, lower volume.

## Bluesky

**Discovery mechanics (2026).** The Following feed is strictly chronological — no algorithmic suppression, and, unlike X, **no penalty on posts containing links**. You can put the URL directly in the post. Reach comes from three places: your followers, reposts, and *custom feeds*. Follower count matters less than early replies; a post with 8 real replies outperforms one with 40 passive likes. There is no viral lottery — growth is linear and compounding, which suits a daily format.

**The Astrosky Ecosystem is the whole ballgame.** Run by Emily Hunt (`@emily.space`, 22,455 followers, astronomy postdoc at Vienna), it operates the astronomy feed network at [astrosky.eco](https://astrosky.eco) / astronomy.blue. Verified live 2026-07-30:

- **Astronomy** — `bsky.app/profile/emily.space/feed/astro` — **9,007 likes**. The main one.
- **Exoplanets** — `bsky.app/profile/emily.space/feed/exoplanets` — 208 likes. Small, but *exactly* our audience, and **posts here also flow into the main Astronomy feed**.
- Also Extragalactic (273), Stellar (167), Radio (109), Astronomy Education (86), History of Astronomy (82).

**How to get in — this is the single highest-value action in this doc.** Post `@bot.astronomy.blue signup` from your account. The bot (`@bot.astronomy.blue`, 13,066 posts, 1,805 followers, "Managed by @emily.space") replies within a couple of minutes — but **it is not one-and-done**: you then have to accept the rules, state your motivation, and **a human moderator verifies the signup**. Budget for a real (small) application, and do it *after* you have some posting history, not on day one from an empty account. One signup covers every feed in the network; there is no per-feed application. Eligibility per the rules repo: any *"professional/amateur/student in astronomy/astrophysics/astrobiology/planetary science/astronomy education—or you must represent an astronomy-related organization."* **Amateurs are explicitly welcome** — you qualify. Over a thousand accounts and orgs are signed up, ESA among them; the network self-reports ~1 million feed views per week.

Once signed up, inclusion is triggered per-post by content:
- 🔭 emoji, `#astronomy`, or `#astro` → main Astronomy feed
- `#exoplanet` or `#exoplanets` → Exoplanets feed *and* the main feed

**The rules, retrieved in full from [github.com/the-astrosky-ecosystem/rules](https://github.com/the-astrosky-ecosystem/rules) (2026-07-30).** Three of the five bear directly on this plan:

- **Rule 3 — "no spam, including repetitive or overly promotional material that clutters the feeds… AI usage should be minimized, and AI fakes or low-quality generative creations should be avoided."** Read that twice. A daily stream of *computer-generated coloured discs* is, at a glance, indistinguishable from AI slop to a scrolling moderator. Our images are rendered from physics, not a diffusion model — but the burden is on us to make that legible **in the image itself** (the `MODELLED` stamp, the hex, ideally a visible spectrum trace) and in the first clause of the caption. This is the biggest un-named risk in the whole channel.
- **Rule 4 — "Attribute content that is not your own… link to the original creator's content."** The albedo grids are Mark Marley's and Kerri Cahoy's work. Crediting them is not just good manners here, it is a *feed rule*. See [13-credit-the-scientists.md](./13-credit-the-scientists.md); that doc is a prerequisite for this one, not a companion to it.
- **Rule 5 — "limit your promotional posts to no more than once per day on the main Astronomy feed. Promotional posts should not be the majority of your contributions to the feeds."** A daily swatch carrying a link to our own site *is* a promotional post. Once a day is exactly at the cap, and the "not the majority" clause means the plan below is out of compliance unless most of what we tag into the feeds is about **other people's work**. Concretely: tag ~2 planet posts a week into the main Astronomy feed; the rest go out untagged or with `#exoplanet` only.

Moderation contact is `@moderation.astronomy.blue`; ask *before* posting anything you are unsure about — the rules explicitly invite that, and one pre-emptive question is cheaper than one strike.

**Starter packs — verified live 2026-07-30, and worth far less than the guides claim:**
- *Planetary Scientists on Bluesky!* — `bsky.app/starter-pack/asrivkin.bsky.social/3l3emzqrclr2g` (Andy Rivkin, 7,007 followers, active today). **5 all-time joins.**
- *Astronomy on Bluesky Starter Pack* — `bsky.app/starter-pack/emily.space/3kvvsi4qacz2p`. **35 all-time joins.**
- *Astrophotographers on Bluesky* — `bsky.app/starter-pack/astronomywriter.bsky.social/3lazfdoadk32j` — **0 all-time joins**; creator last posted 2025-09-03. Same owner also has two *Astronomers & Space Scientists on Bluesky* packs, both 0 joins.
- An *Exoplanetary Astronomers* pack is indexed on blueskydirectory.com but I could not resolve it to a live AT-URI — treat as unverified.

**So: use packs as a follow list on day one, and drop "get added to a pack" as a goal.** Across the four biggest astronomy packs, the all-time total is 40 joins. Being *in* one delivers a rounding error; using one to bulk-follow 80 real astronomers on day one is the actual value, and costs nothing but a click. If you do ask anyway, ask after 6–8 weeks with one polite reply linking your best thread — but do not count it as a success metric.

**Should you build your own feed?** Not in the first 90 days, and probably not ever. An "Exoplanets" feed already exists and is run by the person with the distribution — competing with it is strictly worse than being *in* it. Feeds are free to build (SkyFeed, or Graze for no-code), so revisit only if you later want something genuinely absent, e.g. a feed of *reflected-light / direct-imaging* posts as Roman approaches launch. Even then, offer it to `@emily.space` as an addition to her network first.

**Alt text is not optional here.** The astro and disability communities on Bluesky overlap heavily and *will* notice. Turn on Settings → Accessibility → **Require alt text** so you cannot forget. There is an `@alt-text.bsky.social` retrieval bot ("Get Alt Text", 7,051 followers, 53,671 posts — verified 2026-07-30, i.e. it is invoked tens of thousands of times) and an ALT4Me convention for requesting human-written alt text — being on the receiving end of that is embarrassing and entirely avoidable. Limit is 2,000 characters; ours will use ~250. Template below.

**Hashtags.** Bluesky hashtags are functional (they drive the Astrosky feeds), not decorative. Use **2, maximum 3**, at the end: `#exoplanet` plus `#astronomy`. Add 🔭 as belt-and-braces. Avoid `#space` (noisy, non-scientific), `#science` (nothing), and long tag stacks (reads as spam).

## Mastodon

**⚠️ astrodon.social is gone.** Every guide still recommends it as *the* astronomy instance. As of 2026-07-30 the domain has MX records (iCloud mail) but **no A record** — DNS resolution fails, `curl` cannot connect, and the instance API is dead. Do not attempt to sign up there, and be sceptical of any other astronomy-Mastodon advice written before 2026.

**Where to actually be.** Verified monthly-active users, 2026-07-30:

| Instance | Active/month | Registration |
|---|---|---|
| `mastodon.social` | 264,894 | open, no approval |
| `fediscience.org` | 821 | open, **approval required** |
| `sciences.social` | 494 | open, approval required |
| `mstdn.science` | 425 | open, approval required |
| `scicomm.xyz` | 183 | **closed** |
| `spacey.space` | 74 | open, approval required |

**Recommendation: `mastodon.social`.** With astrodon dead there is no astronomy-native home worth the friction, the science instances are tiny (a few hundred people) and gated behind manual approval that will cost you days, and Mastodon discovery is hashtag-driven anyway — so your instance barely affects who sees you. Take the instant signup. If you later want the community, `fediscience.org` is the strongest of the science instances at 821 monthly actives.

**Should you be there at all?** Yes, but *cheaply*. Expect roughly a tenth of Bluesky's engagement for a fifth of the effort. Justification: the fediverse audience skews toward exactly the people who care about open data, reproducibility and accessibility — which is this project's whole personality — and several of them run newsletters and blogs. Treat it as cross-posting your best 2–3 posts a week, not the daily firehose.

**No algorithm means hashtags do 100% of the work.** Mastodon users *follow hashtags* directly, so a tagged post reaches people who follow zero of your accounts. Use 3–5, capitalised for screen readers (`#ExoPlanet` not `#exoplanet` — CamelCase is a genuine accessibility convention here, not a style choice):

`#Astronomy` `#Exoplanet` `#Astrophysics` `#Space` `#DataViz` `#SciComm` `#Astrodon`

`#Astrodon` survives as a cross-instance community tag even though the instance that spawned it is gone — still worth including.

**Anti-self-promotion norms are real and stricter than Bluesky's.** The rules are cultural, not written: (1) never post the same link twice in a week; (2) reply to other people at least as often as you post; (3) if you automate, **label the account as a bot** in profile settings and post at **unlisted** visibility so you don't flood the local/federated timelines — this was astrodon's explicit written policy and remains the fediverse norm; (4) no engagement-bait phrasing. A single "check out my site!" post to a cold account will get you silently blocked by exactly the people you want.

**CW (content warning) conventions.** Astronomy content essentially never needs one — CWs are for politics, medical detail, food, eye contact in photos. Do *not* CW your planet images; over-CWing reads as ignorant of the norm just as under-CWing does. The one real case: if you ever post a flashing/animated phase-slider GIF, CW it `eyestrain` or `flashing`. Alt text is mandatory (1,500 char limit) and enforced socially as hard as on Bluesky.

## The daily post format

**The image.** One square 1200×1200 PNG: the planet's rendered disc on the site's CRT-dark background, the hex code, the planet name, and — critically — a small `MODELLED` or `MEASURED` stamp. This is the whole editorial position rendered as a pixel. Reuse the per-planet OG card generator; it already ports the `planet-render.js` shader.

**Twice a week**, post the *Roman comparison* instead: two discs side by side, "full spectrum" vs "as Roman would see it". That's the signature feature and it's the one image nobody else on either platform can produce.

> ⛔ **Gate: do not post a single Roman comparison until the band-model correction in [15-roman-launch.md](./15-roman-launch.md) has shipped in the data.** The flight configuration is **three bands (575 nm/10%, 730 nm/15%, 825 nm/10%)**, not the four this doc originally assumed, and only the 575 nm band is guaranteed by the tech demo. Publishing "as Roman would see it" against a wrong band model, to an audience that contains the CGI team, is the one unrecoverable error available to this channel. Both the README and 15 say the same thing; it is repeated here because this is where the mistake would actually be published.

**Character budget.** Bluesky 300 graphemes; Mastodon 500. Write to Bluesky's 300 and let Mastodon breathe. Allocation:

- Planet name + hook: ~60
- One sentence of physics (the *why*): ~110
- Honesty clause (modelled / measured / model-only): ~40
- URL: ~45
- Hashtags: ~30

**Linking.** No link penalty on Bluesky, so put the URL in the post. One catch: **a post cannot have both an image and a link card**, and the image is the product — so attach the image and let the URL sit as plain text in the body. Deep-link to the planet page, never the homepage: `<SITE_URL>/planet/hd-189733-b?utm_source=bluesky&utm_medium=social&utm_campaign=potd`.

**Alt text template** (fill the four slots; ~250 chars):

> A rendered disc of {planet}, coloured {plain-colour-name} ({hex}), on a dark background. {One clause on the visible feature — e.g. "The disc is uniformly lit with no banding."} The colour is computed from a model albedo spectrum, not photographed.

Never write "image of a planet". Name the colour in words — the whole point is that a blind reader gets the finding, and the finding *is* the colour.

**Frequency.** Once a day is the ceiling on Bluesky and is already ambitious; 5 days a week is safer and leaves room for hand-written posts. On Mastodon, 2–3 a week, unlisted if automated. Two automated posts in a day is the point at which a shared feed starts to feel occupied by you.

## 10 drafted posts

Voice: flat, specific, slightly dry. The physics does the work; never oversell. Each is under 300 characters including the URL.

**1 — HD 189733 b** (the anchor: we have a *measurement* to check against)
> HD 189733 b is deep blue, and we know because Hubble measured it — not because an artist decided. Silicate cloud droplets scatter blue; sodium eats what's left past 450 nm. One of the few exoplanet colours that isn't a model.
> `<SITE_URL>/planet/hd-189733-b` 🔭 #exoplanet #astronomy

**2 — TrES-2 b** (the extreme) — ⚠️ *corrected 2026-07-30; the original draft stated two things that are false.*
> TrES-2 b is the darkest planet we know of: Kepler measured a geometric albedo of about 2.5%, and most of even that is the planet glowing, not reflecting. Our swatch looks normal because every swatch here is brightness-normalised — the real one is nearly black. The site says so.
> `<SITE_URL>/planet/tres-2-b` 🔭 #exoplanet

*Two corrections baked in.* (a) The widely-quoted "less than 1%" is the press-release figure; the published Kepler-band measurement is Ag ≈ 0.025, and the sub-1% number is the *reflected* residual after subtracting thermal emission — cite whichever you use, don't blur them, and do not state the "0.04%" figure from the original draft without a paper in hand. (b) The original claimed "our pipeline renders it as a disc you can barely distinguish from the background." **It does not.** `pipeline/config.py` sets `BASE_SWATCH_LUMINANCE_Y = 0.60`; every base swatch is normalised to the same luminance by design. Posting that sentence would have been the site being caught contradicting its own code — on the honesty account. Turn it into the confession instead, as above: the normalisation *is* the interesting caveat.

**3 — Kepler-7 b** (the counter-extreme, same week as #2)
> The opposite of yesterday: Kepler-7 b bounces back 38% of its starlight. It was the first exoplanet ever given a cloud map — the clouds sit on one side, so it's brighter on the west. Modelled here as uniform, which is a lie we label.
> `<SITE_URL>/planet/kepler-7-b` 🔭 #exoplanet #astronomy

**4 — WASP-12 b** (narrative)
> WASP-12 b is being eaten. It orbits in 26 hours, it's stretched into an egg, and its geometric albedo is under 0.064 — it reflects almost nothing and glows instead, at ~2,600 K. A dying planet renders as a dark ember.
> `<SITE_URL>/planet/wasp-12-b` 🔭 #exoplanet #astronomy

**5 — the Roman comparison post** (signature; use the two-disc image) — ⚠️ *corrected 2026-07-30; the original draft was wrong twice and is the post most likely to have burned this account.*
> Left: 47 UMa b's colour from its full modelled spectrum. Right: the same planet rebuilt from only the bands Roman's coronagraph actually flies. Most of the identity survives. Sometimes it doesn't — that's the whole question this site asks. Both are models; Roman hasn't launched.
> `<SITE_URL>/planet/47-uma-b` 🔭 #exoplanet

*Two corrections.* (a) **"four bands" is wrong** — the flight configuration is three (575/10%, 730/15%, 825/10%), per the Primer table cited in [15-roman-launch.md](./15-roman-launch.md). (b) **GJ 1214 b is not a Roman target and never could be.** It is a small planet at 0.014 AU from an M dwarf 14.6 pc away — orders of magnitude inside the coronagraph's inner working angle. Using it as the exemplar of "as Roman would see it" is the kind of error that gets one screenshot-quoted by someone with 20,000 followers. Use a target the repo itself already flags: `pipeline/catalog.py` sets `_CGI_TARGETS = {"47 UMa b", "47 UMa c", "ups And d"}`, and those are the repeatedly-named CGI candidates. Take the exemplar from that set, always.

**6 — 55 Cancri e** (naked-eye hook)
> 55 Cancri e orbits a star you can see without a telescope. The planet is 2,000 K, probably part-molten, and close enough to its star that a year lasts 18 hours. The colour here is modelled — nobody has ever seen this thing in visible light.
> `<SITE_URL>/planet/55-cnc-e` 🔭 #exoplanet #astronomy

**7 — the calibration post** (the credibility flex; pin this one)
> Before trusting any of the 5,700 modelled colours here, check the five we can verify. Jupiter, Saturn, Uranus, Neptune and Earth go through the identical pipeline using *measured* spectra. If they come out wrong, everything else is wrong too.
> `<SITE_URL>/about/calibration` 🔭 #astronomy

**8 — TRAPPIST-1 e** (the honest deflation)
> TRAPPIST-1 e is the one everyone wants to be blue. We don't know its atmosphere, so we don't know its colour, and the swatch you'll see is one model among many — labelled as such. Refusing to guess prettily is the point.
> `<SITE_URL>/planet/trappist-1-e` 🔭 #exoplanet #astronomy

**9 — HD 209458 b** (history)
> HD 209458 b was the first exoplanet ever caught crossing its star, and the first with a detected atmosphere. Twenty-six years of it being the test case for every technique we have — including the albedo models this site runs on.
> `<SITE_URL>/planet/hd-209458-b` 🔭 #exoplanet #astronomy

**10 — a microlensing planet** (the hardest honesty)
> We have never received a single photon from OGLE-2005-BLG-390L b. It was found by the way its gravity bent another star's light. So its swatch is model-only, flagged model-only, and always will be. Some colours are arguments, not observations.
> `<SITE_URL>/planet/ogle-2005-blg-390l-b` 🔭 #exoplanet #astronomy

Posts 2+3 and 7+10 are deliberately paired — contrast and self-criticism both travel further than a single fact.

## Automation

**The line both communities draw is authorship, not scheduling.** Nobody minds that a post went out at 09:00 via cron. They mind text that was clearly assembled by a template. `@astrophep-bot` and `@exocourier` are tolerated *because they're honest utilities* — and their 75 and 90 followers show what tolerance is worth.

**Recommended: auto-draft, manual send.** A Python script generates the image, the alt text and a *draft* caption for the next 7 planets and writes them to a file. You spend 15 minutes on Sunday rewriting the seven sentences in your own voice and approving the queue. The physics sentence is the entire value of the post — the moment it's templated, the account is dead. This also means every caption is legally and scientifically yours, which matters when you're making claims about other people's data.

**Tooling, all free:**
- **Bluesky:** [`atproto`](https://github.com/MarshalX/atproto) (MarshalX, the mature Python SDK). `client.send_post(text, embed=...)`. Auth with an **app password**, never your real one. No built-in scheduling — use `cron`, or a GitHub Actions scheduled workflow so you don't need a machine on. The [ATProto Python Bot Starter Kit](https://github.com/bluesky-hack/bot) has a ready `cron-bot.py`.
- **Mastodon:** `Mastodon.py`. Create an app under Preferences → Development, scope `write:statuses` + `write:media`. `status_post(..., visibility='unlisted', media_ids=[...])`, and set alt text via `media_post(description=...)`.
- **Both:** one script, two adapters, ~120 lines. It belongs in `pipeline/` next to the OG-card generator, since it reuses the renderer.

**Rules for the automation:** hard-cap one post per day; kill-switch file the cron checks; never auto-reply to anything, ever; never auto-follow; log post IDs so you can measure. If the queue empties, post nothing rather than repeating.

## Who to engage

Genuine engagement means replying with something only you could say — "your paper's Fig. 4 is what our albedo model is interpolating, here's what it looks like as a colour" — not dropping links. Budget 10 minutes a day for replies; it will outperform the posting.

**Verified live on Bluesky, 2026-07-30** (follower count, last post):

- `@philplait.bsky.social` — Phil Plait, Bad Astronomy. 84,169, posting today. *(Note: `@badastronomer.bsky.social` is a squatter with 48 followers — don't tag it.)*
- `@astrokatie.com` — Katie Mack, cosmologist. 323,201, today. Huge; engage sparingly and only with substance.
- `@elakdawalla.bsky.social` — Emily Lakdawalla, planetary science writer. 26,530, today. Deeply into planetary imaging and colour — arguably the single best-matched person on the platform.
- `@theplanetaryguy.com` — Paul Byrne, planetary scientist. 18,230, today.
- `@chrislintott.bsky.social` — Chris Lintott, Oxford / Zooniverse / Sky at Night. 15,597, today.
- `@voosen.me` — Paul Voosen, *Science* magazine journalist. 15,321, 2026-07-27.
- `@coreyspowell.bsky.social` — Corey S. Powell, science journalist. 9,801, today.
- `@astrobites.bsky.social` — grad-student paper summaries. 10,760, active. Wrote the definitive guide to astro-Bluesky; plausible venue for a guest post.
- `@emily.space` — Emily Hunt. 22,455, today. **Runs the feeds.** Engage genuinely and early; do not ask her for anything in the first month.
- `@asrivkin.bsky.social` — Andy Rivkin, JHU APL. 7,007, today. Owns the Planetary Scientists starter pack.
- `@eso.org` (8,780) · `@esa.int` (101,779) · `@natastron.nature.com` (Nature Astronomy, 6,016) · `@ojastro.bsky.social` (Open Journal of Astrophysics, 1,183) · `@psi.edu` (Planetary Science Institute, 1,639) · `@aanda-journal.bsky.social` (A&A, 193) — all active this week.
- `@asclnet.bsky.social` — Astrophysics Source Code Library, 2,715. **Submit the pipeline to the ASCL.** It's a real indexed registry, it's free, and it gets the code cited. Last post 2026-06-21.

**The people whose work this site is literally built on — verified 2026-07-30, and the highest-value names in this doc.** These were missing from the first draft and they matter more than any of the big accounts above:

- `@markmarley.bsky.social` — **Mark Marley**, 1,692 followers, 1,262 posts, bio "Substellar science since the 80s." He is a co-author of the Cahoy et al. albedo grids and of the model lineage PICASO descends from. Our pipeline interpolates his work. Telling him that, once, with a picture, is the single best outreach action available to this project — and Astrosky Rule 4 makes attribution mandatory anyway. Do it after [13-credit-the-scientists.md](./13-credit-the-scientists.md) ships, not before.
- `@aussiastronomer.bsky.social` — **Dr. Jessie Christiansen**, 18,743 followers, 6,484 posts, active. Caltech/IPAC; **Chief Scientist of the NASA Exoplanet Science Institute** — i.e. she runs the archive every planet in `planets.json` came from. Enormously well matched, and posts constantly.
- `@offallingstars.bsky.social` — **Sarah E Moran**, 1,471 followers. Exoplanet clouds and hazes; incoming Asst. Prof. at UMD. Clouds are the single biggest lever on albedo in our model — she is the person most able to tell us we're wrong, which is exactly who to want.
- `@astrorickman.bsky.social` — **Dr. Emily Rickman**, ESA/STScI, direct imaging of exoplanets and brown dwarfs. Small account (1,023) but directly on the reflected-light beat.
- `@exocast.bsky.social` — **Exocast**, the exoplanet podcast (Hannah Wakeford, Andrew Rushby, Hugh Osborn), 326 followers. Low-follower account, high-value venue: a podcast segment is a much better ask than a repost.
- `@nancyromansci.bsky.social` — **"Roman for Scientists"**, 720 followers, run by the Roman Science Centers. The official channel for the mission we are hitching to. Follow now; do not pitch.

**Institutions — the first draft's "unverified" list is now resolved:**

- `@stsci.edu` — **Space Telescope Science Institute, 74,036 followers**, active, and its bio names Roman explicitly ("Science Operations Center for Webb, Hubble, and the upcoming Roman"). Real, large, and directly relevant. The first draft said this could not be confirmed; it can.
- `@planetarysociety.bsky.social` — **The Planetary Society, 4,643 followers**. Real, if low-volume (54 posts).
- `@aasnova.org` — **the real AAS Nova, 4,334 followers, 502 posts.** ⚠️ The first draft dismissed `@aasnova.bsky.social` as "parked, 0 posts" — true, but that account's own bio redirects to `@aasnova.org`. Nearly lost a prime venue to a placeholder handle. AAS Nova is also an RSS source in [01-newsjacking.md](./01-newsjacking.md).
- **NASA and NASA Exoplanets still have no native Bluesky account.** The only hits are `@nasawebb.extwitter.link` / `@nasaexoplanets.extwitter.link`, which are third-party Twitter *bridges*, not NASA. Do not tag them and do not treat a bridge post as an official statement.

**Verified dormant or fake — do not waste a mention:** `@drbecky.bsky.social` (12,259 followers but silent since 2026-03-12), `@nasawebb.bsky.social` (57 followers, 18 posts — not the real NASA account), `@badastronomer.bsky.social` (48 followers, display name "Ron Mexico" — a squatter, not Phil Plait), `@exoplanetmodels.bsky.social` (NASA EMAC, last posted 2025-09-05), `@a4e.org` (last 2025-04-22), `@astronomywriter.bsky.social` (last 2025-09-03).

⚠️ **Correction:** `@planetarynews.bsky.social` was listed as dormant/fake. It is neither — it is the **Planetary Exploration Newsletter**, a real weekly newsletter for planetary scientists hosted by the Planetary Science Institute, and it posted on 2026-07-27. It is merely *small* (37 followers). Small is not fake, and PEN is a plausible distribution route to exactly the professional audience this doc wants.

**Mastodon:** `@esoastronomy@mastodon.social` (ESO, 6,189 followers, active 2026-07-28) is the main live institutional astronomy account. ⚠️ `@astronomy@mastodon.social` is **abandoned** — 1 follower, last post 2022-05-11. `@astronews@mastodon.social` (151) is only lightly active. The fediverse astronomy scene is thin and hashtag-mediated; find people by following `#Astronomy` rather than hunting accounts.

**Also worth a genuine approach:** see [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the researchers whose albedo grids we interpolate are on these platforms, and telling someone "your 2010 model grid is what makes this site work" is both true and the best outreach available.

## The 90-day ramp

**Weeks 1–2 — build a history, promote nothing.** Create/clean the personal accounts, bio links `<SITE_URL>`, enable Require-alt-text on Bluesky. Read the Astrosky rules repo *first*, then post `@bot.astronomy.blue signup` — a human moderator reads the application, so apply in week 2 with ten real posts behind you, not on day one from an empty profile. Follow ~80 accounts from the two live starter packs. Then **post 10 times about other people's work and zero times about your own** — reply to papers, ask real questions. An account with no history that opens with a product link is indistinguishable from spam, and the astro feeds are moderated by humans who have seen it a thousand times.

**Weeks 3–6 — start the daily, hand-written.** No automation yet. One planet per weekday, written by hand, using the drafted voice above. This is where you learn which sentences land — you cannot template that before you know it. Cross-post the best 2–3 a week to Mastodon. Post the calibration post (#7) around week 4 and pin it; it is the credibility artifact. Introduce the Roman two-disc comparison in week 5. Keep replying daily.

**Weeks 7–12 — automate the boring half, spend the credits.** Stand up the auto-draft/manual-send script and the labelled bot account. Around week 8, with ~40 posts of history, spend the one good ask you have on the people whose work the site runs on — `@markmarley.bsky.social` and `@aussiastronomer.bsky.social` — not on starter-pack inclusion, which is worth ~40 joins across the whole ecosystem. Submit the pipeline to the ASCL. Reach out to `@astrobites.bsky.social` about a write-up. Run one thread-format experiment: a 5-post thread on "why most exoplanet art is a lie" is the most shareable thing this project can say, and it's true.

## How we'll know it worked

**Primary metric: 150 referred sessions from Bluesky + Mastodon in the first 90 days, with median session depth ≥ 2 pages.** Depth is the honest half — 500 bounces would mean the images travelled and the site didn't.

Tag every link:

```
?utm_source=bluesky&utm_medium=social&utm_campaign=potd
?utm_source=mastodon&utm_medium=social&utm_campaign=potd
```

Use `utm_campaign=roman` for the two-disc comparison posts specifically, so we can test whether the signature feature actually out-travels a plain swatch. PostHog picks these up cookielessly with no extra config — see [99-tracking.md](./99-tracking.md).

**Secondary, checked at day 90:** followers who are identifiable astronomers (count by hand, target 25 — this is the real number); ≥3 reposts by accounts with >5,000 followers; one inbound from a researcher whose work we cite. ~~inclusion in ≥1 starter pack~~ — **dropped as a metric**: the four biggest astronomy packs have 40 all-time joins between them, so inclusion measures nothing.

**Kill criteria:** if after 6 weeks of daily hand-written posts the Bluesky account is under 100 followers *and* has produced under 30 referred sessions, the format is wrong — stop the daily and shift the effort to [10-reddit.md](./10-reddit.md) or [09-show-hn.md](./09-show-hn.md), which are burstier and cheaper.

## Risks

- **Astrosky feed removal.** Losing the Astronomy feed removes most of the reach. Mitigation: obey the rate limits, keep captions human, keep the bot account separate from the personal one so a bot strike doesn't take down the human.
- **Scientific error at scale.** A daily post is a daily chance to state something wrong about someone's specialty, in front of that specialty. Mitigation: every claim traceable to a paper; correct fast and visibly; prefer "modelled" phrasing that cannot be falsified by a new measurement.
- **The "pretty picture that's actually made up" objection.** The single most likely hostile reply is *"these aren't real colours."* This is correct, and it's why the calibration post and the MODELLED stamp exist. Have a two-sentence answer ready and never get defensive — see [02-press-kit.md](./02-press-kit.md).
- **Burnout.** A daily post is a real obligation for one person with evenings only. The week 7 automation exists specifically so the streak survives a bad month. Post nothing rather than post filler.
- **Mastodon may not be worth it.** Genuine possibility given astrodon's death and the thin instances. Capped at ~20 min/week; if day-90 referred sessions from Mastodon are under 15, drop it and keep only cross-posting.
- **Personal-account bleed.** Mixing audiences means astronomers see your non-astronomy posts. Mostly a feature. If it ever isn't, Bluesky's per-post controls and Mastodon's unlisted visibility both let you keep things off the public feeds.

## Links

- [Marketing plan](./README.md) — hub
- [01-newsjacking.md](./01-newsjacking.md) — social is the delivery mechanism for newsjacking; a Roman or JWST result becomes a same-day post
- [02-press-kit.md](./02-press-kit.md) — the "these aren't real colours" rebuttal and the modelled-vs-measured language should be identical in both
- [07-wallpapers.md](./07-wallpapers.md) — the daily render and the wallpaper assets are the same pipeline; social is where wallpapers get discovered
- [08-short-video.md](./08-short-video.md) — the phase-angle slider as video; Bluesky supports video and the astro feeds carry it
- [09-show-hn.md](./09-show-hn.md) — a posting history on Bluesky gives the HN launch somewhere to send people
- [10-reddit.md](./10-reddit.md) — the fallback channel if the daily format underperforms
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the researchers to engage are the ones whose models we use
- [15-roman-launch.md](./15-roman-launch.md) — the two-disc Roman comparison post is the asset that matters most at launch
- [99-tracking.md](./99-tracking.md) — UTM scheme and PostHog setup
