# Review — 10 Reddit

*Reviewed by a moderator of a large science subreddit — ten years in the removal queue, no love for distribution channels.*

## Verdict

**substantially rework** — the sub-by-sub research is unusually good, but the plan it wraps around that research (ten subs, one domain, one account, six weeks) is the exact pattern I remove people for, and its flagship artifact would probably die under r/dataisbeautiful's Rule 1.

## What's right

- The core instinct — *build the artifact, let the site be what people find afterwards* — is correct and rare. Most people in my queue never get there.
- The calibration figure (5 solar-system planets, modelled vs photographed, ΔE stated) is the single best idea in the document. It is armour, it is honest, and it is a *post* in its own right.
- The NO-GO calls (r/astronomy, r/Physics, r/EarthPorn, r/colors) are right and the reasoning is right. Nice to see a plan that says "skip it."

## Gaps

**1. It plans for rules and not for silence.** Every removal in this doc is imagined as a visible one. The three that actually happen are invisible: a shadowbanned account, an AutoMod karma/age gate, and a domain-level block. You can post ten times, see your posts in your own profile, and be talking to nobody. There is no detection step anywhere in the plan. I added one to the doc: logged-out profile check, a canary comment in the sub's daily thread checked logged-out, and a bare-URL canary in r/test to catch a site-wide domain ban. Do all three *before* week 1, because a domain ban makes every other line of this plan worthless and takes weeks to appeal.

**2. The 9:1 rule is folklore as stated.** Reddit retired the site-wide 9:1/90-10 self-promotion guideline years ago; there is no official Reddit self-promotion page and no admin enforces a ratio. What survives is per-sub rules that write it down (r/InternetIsBeautiful's 90/10 is real and hand-enforced) and mod instinct. And mod instinct is not a ratio. When I open an account I check, in order: *comments in my sub before today?* → *does every submission point at one domain?* → *is OP answering questions in their own thread?* Five real comments in my sub beat 500 karma farmed in r/askastronomy. The doc's "target 200+ comment karma" advice optimises for the wrong number and produces the farmed-then-dropped shape that gets flagged.

**3. The schedule is the ban risk.** Ten subreddits, one domain, one account, six weeks. Every post can pass its own sub's rules and the *aggregate* still reads as a campaign — because it is one. If I saw this account in modmail I'd look at its submission history and see nothing but one domain, and that's the end of the conversation. Nothing else in this document is as dangerous as its own calendar.

**4. r/dataisbeautiful would probably remove the two-strip chart.** Rule 1 is "must be or contain a qualifying data visualisation," and "this is data art, not a visualisation" is the most common removal there. Two flat colour bands ordered by temperature encode exactly one variable. It's beautiful; it isn't a chart. Also missing: DIB posts need a **flair** (unflaired = auto-removed), and the source/tools comment must go up **immediately** — the bot doesn't wait. And the plan picks a timeslot without booking the four hours after it; DIB posts are decided in 60–90 minutes.

**5. The chart as specified can't be rendered.** 5,764 one-pixel columns do not fit in a 2400px-wide PNG. At 0.42px per planet the renderer averages neighbours and the divergence between the strips — the entire thesis — is the first casualty. Bin the temperature axis (~400 bins, median colour, say so in the caption) or go 5,764px wide with a detail inset.

**6. It prepares for the wrong hostile comment.** "Is this AI slop?" is handled well. The comment that actually kills the thread is an astronomer writing *"the albedo models are unconstrained for all but a handful of these planets, so these colours are free parameters."* That's a fair hit, it lands above your reply, and no calibration figure answers it — the solar-system anchors have measured spectra, the 5,764 don't. The answer has to be a concession with a receipt: which planets have observationally constrained albedos vs. grid interpolation. If the site doesn't tier those two per planet today, that's a build task before posting, not a comment to draft.

**7. Wallpaper subs want one image, not a pack.** r/Amoledbackgrounds and r/wallpapers culture is one wallpaper per post. A post whose mandatory source comment points at a download page on your own domain is the funnel shape those subs remove. Post one image; offer the rest when asked. Also drop the name+hex overlay from the shared version — that's a watermark, and watermarks read as branding.

**8. No abort condition.** "If a post lands hard, stop for a week" is there; "if two posts are removed, stop the campaign and reassess" is not. Two removals in different subs almost always means the account or the domain is the problem, not the posts.

## Wrong or unverified

- **"Rules quoted from each sub's `about/rules.json` on 2026-07-30."** I could not reproduce this and neither can you. Reddit now returns `403 — you've been blocked by network security` to every unauthenticated request from any user-agent, including `about.json`, `about/rules.json`, `old.reddit.com`, and reader proxies; every public redlib/libreddit mirror I tried is behind a bot challenge. So the verbatim quotes in this doc cannot be checked by anything except a logged-in human with a browser. For a project whose entire editorial position is *honesty about provenance*, an unverifiable citation block is the wrong thing to have. **Screenshot each rules page into `docs/marketing/evidence/` before its post.** Added as a provenance warning at the top of the doc.
- **Subscriber counts: broadly accurate ✅.** Independently confirmed r/space 27.9M, r/dataisbeautiful ~22M (doc says 21.8M), r/coolguides 6.1M, r/InternetIsBeautiful 16.6M, r/datasets 204k. **r/Amoledbackgrounds is 324k, not 346k** — corrected.
- **r/InternetIsBeautiful is over-rated in the doc.** ✅ ~1 post per day survives, median top-100 post of the year ≈490 upvotes, best post of the year 16.4k. A 16.6M sub behaving like a 200k one, because almost everything is removed. It is not "the largest single traffic spike of the campaign," and structuring weeks −3 to 0 around its 90/10 rule is spending three weeks to buy a lottery ticket with a small prize. Downgraded to Maybe in the table.
- **r/coolguides is under-rated.** ✅ 6.1M, ~3 posts/day, median top-100 ≈7,200 upvotes. Best risk/reward on the list by a distance, and the cheapest artifact (2 hours). It should be first, not week 5.
- **DIB timing "Tue or Wed 08:00 ET" — unverified.** Third-party stats put the sub's peak activity nearer 22:00 UTC. 08:00–09:00 ET is the conventional advice for catching the US morning rise and I'd keep it, but it's convention, not measurement. Don't present it as a finding.
- **r/somethingimade "handmade only", r/coolguides' "A cool guide" title prefix, r/Amoledbackgrounds' 50%-black threshold, r/space's weekend-image rule** — all plausible, none independently confirmable given the 403 wall. The r/Amoledbackgrounds AI ban ✅ *is* confirmed and sits in the sub's one-line description, not in a numbered rule — which tells you how hard they enforce it.

## Better approaches

Ranked by what I'd actually approve.

1. **Do nothing on Reddit for 90 days.** Comment only, in five places: **r/exoplanets** and **r/askastronomy** (answer questions — this is where the domain expertise is free to give), **r/Astronomy** (comment forever, never post; the sub is closed to you and its readers overlap everything else), **r/telescopes** (the CGI/optics crowd), and **r/dataisbeautiful** (comment on other people's OC — DIB mods notice which OC contributors show up in other people's threads, and it's the only "karma" that changes how I read an account). Ship the calibration figure and the credits page in that window. This is the option nobody takes and it is the one that works.
2. **Two posts, not ten.** r/exoplanets first (low stakes, harvest corrections, that thread becomes the receipt you cite everywhere else), then r/coolguides — cheapest artifact, largest realistic payoff, no self-promo dimension at all if the URL is nowhere in the image. Everything else moves to "only if someone asks."
3. **Rebuild the DIB artifact as a chart.** ΔE between full-spectrum colour and four-band reconstruction on the y-axis, equilibrium temperature on the x, the two colour strips as a band underneath sharing that axis. Now the submission *contains* a qualifying visualisation and the beautiful part rides along. Title, in DIB's plain register: `[OC] Modelled visible colour of 5,764 known exoplanets, and how much of it survives the Roman telescope's four filters` — describes the data, no adjective, no "I built". Not: *"the colour of every world we know"*, which is the version that gets the Rule 5 clickbait removal.
4. **Modmail first, for the two that matter.** Two lines to r/dataisbeautiful and r/space: *"I made a physics-derived colour catalogue of known exoplanets; is a chart of it in scope, and is `<domain>` allowed?"* Mods answer this. It costs nothing, it pre-registers you as someone who asked, and it surfaces a domain block before it costs you a post. Almost nobody does it and I remember the ones who do.
5. **Let someone else post it.** The highest-EV Reddit outcome for a project like this is a submission with *no relationship to your account*. Seed via Bluesky, HN, and the design newsletters (`11`, `09`, `12`); a third-party submission arrives with none of the self-promo signal, and I approve those without a second look. It's also the only path into r/astronomy that exists. Reddit should be an *output* of the other channels, not a channel.
6. **Cut, don't defer:** r/InternetIsBeautiful, r/wallpapers, r/spaceporn, r/SideProject, r/generative, r/proceduralgeneration. Six subs, six small prizes, and collectively they're what turns the account into a marketing account. Add **r/datasets** (204k) when `06-open-data.md` ships — tiny reach, near-zero risk, and it's the one place a link to your own data is the actual topic of the sub.

## The one thing I'd change

Delete the six-week schedule. Replace it with 90 days of commenting and **two** posts — r/exoplanets and r/coolguides. Every individual post in the current plan can be rule-compliant and the account still gets flagged, because ten submissions pointing at one domain in six weeks *is* the definition of the thing I remove. The plan's own calendar is its biggest risk, and it's the only risk in the document that isn't listed.

## What I edited

In `10-reddit.md`, preserving structure, status line and links:

- Added a **provenance warning** under the subreddit map: Reddit 403s all unauthenticated rule fetches, mirrors are challenge-walled, so quotes must be screenshotted from a logged-in browser into `docs/marketing/evidence/`; marked independently confirmed facts ✅ inline.
- Corrected **r/Amoledbackgrounds to 324k**, added its confirmed "No AI allowed" description line, its ~380 median, and the one-image-not-a-pack norm.
- **Downgraded r/InternetIsBeautiful** to Maybe with the ~1 post/day, ~490 median, 16.4k-best numbers.
- Upgraded the **r/coolguides** row (best risk/reward, ~7,200 median) and added a **r/datasets** row.
- Added to the r/dataisbeautiful note: the Rule 1 "data art" removal risk and the ΔE-chart fix, the flair requirement, the immediate source-comment requirement, and the four-hour availability window.
- **Corrected the 9:1 rule** in account hygiene: retired site-wide, real only where a sub writes it down; replaced with what a mod actually checks, and added the three silent-failure detection tests (shadowban, AutoMod gate, domain ban) plus the image-hash warning.
- Fixed the **two-strip chart geometry** (5,764 columns can't render at 2400px; bin or go wide).
- Added two risks: **the schedule itself**, and **the unconstrained-albedo comment** that is more dangerous than "is this AI".
