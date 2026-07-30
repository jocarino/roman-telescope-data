# Review — 11 Bluesky & Mastodon

*Reviewed by a working planetary scientist who posts on these platforms, from the audience side. Verified against the AT Protocol public API, the Astrosky rules repo, live instance APIs, and this repo's own source, 2026-07-30.*

## Verdict

**Structurally the best channel doc here, and one drafted post away from a self-inflicted wound.** The account strategy, the honesty framing and the feed mechanics are right; the Roman post is factually wrong about Roman, and the TrES-2 b post is factually wrong about this project's own renderer.

## What's right

- **"Personal account, not a bot", argued from data rather than vibes.** The 8,267-post / 75-follower `@astrophep-bot` figure checks out exactly, as does Paul Byrne at 18,230. That table is the most persuasive paragraph in the marketing plan and it is correct.
- **Astrosky identified as the distribution.** The feed like-counts are exact (Astronomy 9,007; Exoplanets 208; Extragalactic 273; Stellar 167; Radio 109), the signup command is verbatim right, and "post into the existing Exoplanets feed rather than build your own" is the correct call. Most outsiders take a year to work that out.
- **Astrodon's death is real and correctly called.** No A record, `curl` returns 000, API dead; MX still on iCloud. Every Mastodon-astronomy guide online is stale on this. Instance registration flags check out too (fediscience/sciences.social/mstdn.science/spacey all approval-gated, scicomm.xyz closed).

## Gaps

- **Rule 3 of the Astrosky rules is not mentioned and it is the biggest risk in the channel.** The rules say: *"AI usage should be minimized, and AI fakes or low-quality generative creations should be avoided."* You are about to post a daily stream of computer-generated coloured discs into a feed moderated by people who spend their volunteer hours deleting AI slop. Your images are physics. Nobody scrolling can tell. **The image has to argue for itself** — the `MODELLED` stamp is not enough; put the spectrum trace on the card. A shader-rendered sphere with a hex code and no visible provenance is, at thumbnail size, exactly what the rule exists to remove.
- **Rule 5 breaks the posting plan.** *"No more than once per day on the main Astronomy feed. Promotional posts should not be the majority of your contributions."* A daily swatch with your own link is a promotional post. Five a week, all tagged `#astronomy`, is promo as the overwhelming majority of your feed contributions. This is a compliance failure, not a grey area. Fix: tag ~2 into the main feed weekly, rest untagged or `#exoplanet` only, and make the majority of your tagged posts about other people's results.
- **Signup is not "That's it."** A moderator verifies it, and you have to state your motivation. The doc's own advice (build history first) is right but it's filed under week 1–2 alongside the signup — do the signup in week 2, not day one.
- **Rule 4 makes [13-credit-the-scientists.md](../13-credit-the-scientists.md) a blocker, not a sibling.** *"Attribute content that is not your own."* You are publishing derivatives of Marley/Cahoy albedo grids daily. The credits page must exist before the first tagged post. The hub already flags 13 as blocking; this doc should inherit that, not link to it.
- **No answer for "what happens when someone smart replies that you're wrong."** The Risks section covers the *hostile* reply ("these aren't real colours"). The harder case is the correct, friendly, specific one — a cloud modeller saying your metallicity assumption is off for that planet. There should be a written norm: reply within a day, thank them by name, fix the data, and post the fix. That single behaviour is what converts scientists from followers into advocates, and it's free.
- **The four biggest people for this project were missing.** See below.

## Wrong or unverified

Everything I could check in the handle list checked out — `@philplait.bsky.social` 84,174, `@astrokatie.com` 323,200, `@elakdawalla.bsky.social` 26,531, `@theplanetaryguy.com` 18,230, `@chrislintott.bsky.social` 15,600, `@voosen.me` 15,320, `@coreyspowell.bsky.social` 9,801, `@astrobites.bsky.social` 10,760, `@emily.space` 22,456, `@asrivkin.bsky.social` 7,007, `@asclnet.bsky.social` 2,715, `@alt-text.bsky.social` 7,051. Dormancy dates all confirmed to the day. The `@badastronomer.bsky.social` squatter is real (display name "Ron Mexico", 48 followers, 1 post). Good work — that is a better hit rate than most published guides.

The exceptions:

1. **`@planetarynews.bsky.social` is filed under "dormant or fake". It is neither.** It is the *Planetary Exploration Newsletter*, hosted by the Planetary Science Institute, and it posted 2026-07-27. It is small (37 followers), which is not the same thing. Calling a real scientific newsletter fake in a doc you might quote from is a bad look. **Corrected in the doc.**
2. **AAS Nova was nearly lost to a placeholder.** `@aasnova.bsky.social` is indeed parked at 0 posts — but its bio points to **`@aasnova.org`, 4,334 followers, 502 posts, live.** AAS Nova is already an RSS source in [01-newsjacking.md](../01-newsjacking.md); dismissing it here would have broken that doc's Bluesky leg. **Corrected.**
3. **STScI and The Planetary Society are listed as unconfirmable. Both exist.** `@stsci.edu` — **74,036 followers**, bio explicitly names Roman. `@planetarysociety.bsky.social` — 4,643. **Corrected.** NASA and NASA Exoplanets genuinely have no native account; the only hits are `@*.extwitter.link` third-party bridges. The doc's caution there was right.
4. **Starter packs are near-worthless and the doc treats them as a goal.** All-time joins: Rivkin's Planetary Scientists **5**, Emily Hunt's Astronomy **35**, Astrophotographers **0**, and the same owner's two other astronomy packs **0** each. Forty joins across the entire astronomy pack ecosystem. Using packs as a day-one follow list is great; *getting into one* is not a day-90 success metric. **Corrected, and dropped from the metrics.**
5. **"Two exoplanet bots have posted ~15,000 times for a combined 165 followers"** — arithmetic is right (75 + 90), and `@exocourier` is honestly labelled 🤖 in its own bio, which supports the doc's argument better than the doc realises.

**Missing, and these are the four names that matter most:**

- **`@markmarley.bsky.social`** — Mark Marley, 1,692 followers, *"Substellar science since the 80s."* He co-authored the albedo model lineage this entire site interpolates. His absence from a list containing six science journalists is the clearest sign the list was built by follower count rather than by relevance.
- **`@aussiastronomer.bsky.social`** — Dr. Jessie Christiansen, 18,743 followers, 6,484 posts, **Chief Scientist of the NASA Exoplanet Science Institute**. She runs the archive `planets.json` is built from. Bigger than most of the doc's list and infinitely better matched.
- **`@offallingstars.bsky.social`** — Sarah E Moran, exoplanet clouds and hazes. Clouds are the dominant lever on geometric albedo in your model. She is the person best placed to tell you you're wrong, which is who you want.
- **`@exocast.bsky.social`** — the exoplanet podcast. 326 followers, but a podcast segment beats any repost in this doc.

Also worth adding: `@nancyromansci.bsky.social` (Roman for Scientists, run by the Roman Science Centers) and `@astrorickman.bsky.social` (Emily Rickman, ESA/STScI direct imaging). All added to the doc.

## The posts, reviewed

They read like a person about 70% of the time — the voice is genuinely good, flat and specific, and there is no marketing verb anywhere. But **all ten end with the identical string `🔭 #exoplanet #astronomy`**, and on a strictly chronological feed ten identical trailers in ten days is the single most bot-like signal available. Vary it. Drop `#astronomy` on the days you aren't spending your main-feed slot (see Rule 5).

The honesty caveat *has* become a tic. Five of ten end on a modelled-vs-measured line, and three of those land the same rhetorical shape — *"which is a lie we label"*, *"Refusing to guess prettily is the point"*, *"Some colours are arguments, not observations"*. Individually each is good. Consecutively they are a catchphrase, and a catchphrase is the thing people learn to scroll past. Ration it: the caveat belongs in the *image* every time and in the *text* about half the time.

**Would repost:** #7 (calibration), #10 (microlensing), #4 (WASP-12 b). #7 is the best thing in this doc — "check the five we can verify before trusting the 5,700 we can't" is an argument almost nobody in scicomm makes, and pinning it is right. #4 is clean and its numbers hold up (P = 1.09 d = 26 h; Ag < 0.064 from the HST upper limit; ~2,600 K dayside; tidal distortion and mass loss all real).

**Fine:** #1 and #9. #1's *"silicate cloud droplets"* is the one physics wobble — at those temperatures the condensates are solid grains, not droplets, and the blue is a Rayleigh slope; a specialist will notice "droplets". *"Sodium eats what's left past 450 nm"* is loose but defensible. #9's "twenty-six years" depends on counting from the 2000 paper rather than the November 1999 detection; say "a quarter-century" and stop having the argument.

**Weak:** #3 opens *"The opposite of yesterday"* — a serialisation cue that assumes a reader saw yesterday's post, which on a chronological feed almost nobody did. That's a content-calendar tell in a doc that's otherwise good at avoiding them. Its 38% is also high; the published Kepler geometric albedo for Kepler-7 b is ~0.32–0.35. #6 says *"nobody has ever seen this thing in visible light"* — 55 Cnc e has optical photometry (MOST, and later TESS). Wrong, in a post whose whole selling point is being right, about a planet a hundred people follow closely.

**The two worst, rewritten** (both are already corrected in the source doc):

**#2 — TrES-2 b.** Original: *"reflects less than 1%… Best-fit models say 0.04%… our pipeline renders it as a disc you can barely distinguish from the background. Correctly."* The last sentence is false about your own code: `pipeline/config.py` sets `BASE_SWATCH_LUMINANCE_Y = 0.60` and every base swatch is normalised to the same luminance. You would have been caught contradicting your own repo, on the honesty account, by anyone who clicked. The "0.04%" figure I could not source at all. Rewrite:

> TrES-2 b is the darkest planet we know of: Kepler measured a geometric albedo of about 2.5%, and most of even that is the planet glowing, not reflecting. Our swatch looks normal because every swatch here is brightness-normalised — the real one is nearly black. The site says so.

That version turns the render convention from a liability into the post. It is also the only exoplanet-colour account on either platform that would ever admit its own images are lit.

**#5 — the Roman comparison.** Original: *"the four bands Roman's coronagraph can see"*, illustrated with **GJ 1214 b**. Both halves are wrong. The flight configuration is **three** bands (575/10%, 730/15%, 825/10%) — your own [15-roman-launch.md](../15-roman-launch.md) says so, and the hub lists the band-model correction as blocking. And GJ 1214 b is a small planet 0.014 AU from an M dwarf at 14.6 pc; it sits orders of magnitude inside CGI's inner working angle and will never be a coronagraph target. Choosing it as *the* exemplar of "as Roman would see it", in the signature post, in front of the CGI community, four weeks before launch, is the one error in this plan that does not recover. Rewrite:

> Left: 47 UMa b's colour from its full modelled spectrum. Right: the same planet rebuilt from only the bands Roman's coronagraph actually flies. Most of the identity survives. Sometimes it doesn't — that's the whole question this site asks. Both are models; Roman hasn't launched.

`pipeline/catalog.py` already contains `_CGI_TARGETS = {"47 UMa b", "47 UMa c", "ups And d"}`. Take the exemplar from that set, always. And post no Roman comparison at all until the band fix ships.

## Alt text for colour

The doc's template is better than most and still not the answer. *"Coloured {plain-colour-name} ({hex})"* passes a colour *word* to someone who may never have seen colour, which is a label, not information. A colour project owes better, and this one is uniquely equipped to give it, because it knows *why* the colour is that colour.

Four rules:

1. **Name the colour from a system, not from vibes.** Use ISCC-NBS centroid names — "moderate greenish blue", "dark grayish yellow". They are compositional (lightness + saturation + hue), so a reader who has never seen colour still extracts three ordered facts from one phrase. xkcd survey names are friendlier and fine as a second clause; never hand-write a name per planet, because inconsistency across 5,700 posts is worse than a slightly clinical name.
2. **Give lightness separately and honestly, because lightness is the part many readers can perceive.** Colour-blind and low-vision readers see luminance. Say "very dark, barely above the background" or "pale, close to white" — and **say when the swatch has been brightness-normalised**. Your renders are pinned to Y = 0.60. A sighted person cannot tell that TrES-2 b is nearly black from your image. Alt text is the one place you can tell them. No other colour project has this problem and none of them would admit it.
3. **Give the physical cause, not a simile alone.** "Reflects blue and green, absorbs almost everything past 600 nm, because methane" is a real fact about a real object, and it is fully available to a blind reader. That single clause is more information than any colour name, and you already have it in the spectrum. One familiar-object anchor is still worth adding as a third leg — "the blue of a clear midday sky" — because comparison carries what abstraction doesn't.
4. **On the two-disc Roman images, describe the difference, not the two colours.** The image's whole content is a comparison, and a comparison survives translation perfectly: "the right disc is slightly greyer and about as bright" *is* the finding. Most alt text fails here by describing each panel independently and leaving the reader to do the subtraction they cannot do.

Mechanics: hex goes **last** and written as "hex 4A6EA9" (screen readers mangle a leading `#`). Don't repeat the post body — the reader gets both. Limits are 2,000 on Bluesky, 1,500 on Mastodon; you'll use ~350. Generate it from the same record that generates the image so it can never drift, and turn on Require alt text.

A worked example:

> A rendered disc of 47 UMa b on a near-black background. The colour is a light greyish yellow — the warm off-white of unbleached paper — hex E8DFC4. The planet reflects fairly evenly across the visible range with a slight dip in the blue, which is what water and ammonia clouds over a hydrogen atmosphere do. Brightness in this image is normalised; the real planet is much dimmer. The colour is computed from a model albedo spectrum, not photographed.

## Better approaches

Ranked by return per evening.

1. **Own the format nobody has: the correction post.** Nobody in astronomy scicomm posts *"I was wrong, here's the diff."* You can, weekly, because your outputs are versioned data and your errors are visible as colour changes. "This planet's mass was revised in a paper last week; here's what that did to its colour" is a genuinely new format, it is intrinsically honest, it needs no new asset, and it makes every scientist who sees it trust the other 5,699 swatches. It also converts the project's biggest liability — that the numbers move — into the reason to follow. **This is the format to own.**
2. **Make the daily post about a paper, not about a planet.** Same image, different framing: read one arXiv astro-ph.EP abstract a day, and post the colour of the planet *that paper is about*, tagging the finding. This costs the same twenty minutes, it satisfies Astrosky Rule 5 (most contributions are about others' work), it makes the account a service to the field rather than a shop window, and it is the single behaviour most likely to get you reposted by the authors. It also merges this doc with [01-newsjacking.md](../01-newsjacking.md) into one habit instead of two.
3. **Ship the "why most exoplanet art is a lie" thread early, not in week 12.** The doc has it as a week-7–12 experiment. It's the most shareable true thing this project can say and it should be the second week's post, because it establishes the editorial position before the daily stream makes people categorise you as a swatch bot. Five posts, one image each, ending on the calibration post.
4. **Replace "Mastodon presence" with "Mastodon crossposting, unattended."** The doc already suspects this. The instances are 500–800 monthly actives, astrodon is dead, and the honest expected value is a handful of sessions. Cross-post automatically at unlisted visibility, follow `#Astronomy`, spend zero attention, revisit at day 90.
5. **Do not build the bot account in week 7.** It is the one recommendation I'd cut entirely. It splits your posting history in half at exactly the moment history is starting to compound, it earns ~80 followers on the doc's own evidence, and the stated reason — protecting your timeline from 365 similar images — is solved by posting five a week instead of seven. Keep one account.
6. **Colour, not astronomy, is the underexploited hashtag.** The astronomy feeds are the right primary channel, but the design and colour community on Bluesky has zero astronomy content and would repost this on sight. That's a different post with different words (per the hub's house rules) — but it's free reach the doc doesn't mention at all.

## The one thing I'd change

**Stop being an exoplanet-picture account and become the account that shows its working.** Every genuinely strong item here — the calibration post, the microlensing post, the modelled/measured stamp, the correction format above — comes from the same instinct, and every weak one comes from reaching for a pretty planet and a fact. Pick the instinct. The physics-derived swatch is not the product; the *audited* swatch is, and nobody else on either platform is offering it.

Concretely, and before anything else: **fix post #5 and don't publish a Roman comparison until the band model is right.** An account built on honesty that gets Roman's own bandpasses wrong, in launch month, does not get a second impression.

## What I edited

In `11-bluesky-mastodon.md` (structure, `**Status:**` and `## Links` preserved):

- Replaced the "I could not retrieve the rules" paragraph with the **actual Astrosky rules**, retrieved in full, quoting Rules 3, 4 and 5, and flagging the AI-slop-resemblance risk and the Rule 5 compliance failure.
- Corrected the signup description: moderator verification, motivation statement, one signup covers all feeds; moved the signup to week 2 in the ramp. Added the ~1M weekly feed views figure and the `@moderation.astronomy.blue` contact.
- Added **all-time join counts** to the starter packs (5 / 35 / 0 / 0 / 0), rewrote the recommendation to "follow list, not a goal", and removed pack inclusion from the day-90 metrics; redirected the week-8 ask to Marley and Christiansen.
- Added a hard **gate on Roman comparison posts** until the band-model fix ships, with the correct three-band flight configuration.
- **Rewrote drafted post #2** (removed the false claim about the site's own renderer; noted the unsourced 0.04% figure) and **#5** (three bands not four; 47 UMa b not GJ 1214 b), each with the reasoning inline.
- Added the missing high-value accounts: Mark Marley, Jessie Christiansen, Sarah Moran, Emily Rickman, Exocast, Roman for Scientists.
- Resolved the "unverified institutions" list: `@stsci.edu`, `@planetarysociety.bsky.social`, `@aasnova.org` all confirmed live; NASA confirmed as bridge-only.
- Moved `@planetarynews.bsky.social` out of "dormant or fake" with a correction note; added the `@badastronomer.bsky.social` squatter to that list.
- Added verified stats for `@alt-text.bsky.social`.
