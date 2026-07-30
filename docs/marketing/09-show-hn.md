# Show HN

**Status:** not started · **Effort:** one evening to prepare, one afternoon live (~6 h) · **Payoff:** high variance — the single biggest traffic event available to this project, or a quiet nothing · **Hub:** [Marketing plan](./README.md)

## The bet

Hacker News is the one channel where "a physicist's colour pipeline for 5,700 exoplanets, and it tells you honestly that it is a model" is exactly the shape of thing that gets upvoted, and where the audience is technical enough to attack the method rather than the pixels. The median Show HN gets under 10 points and dies unseen; the tail case puts 3,000–10,000 curious engineers on the site in an afternoon and leaves permanent inbound links from blogs and .edu pages. The bet is that the *honesty* framing — computed, not photographed — is the differentiator that flips this from "pretty space thing" to "interesting engineering", and that the Roman four-band reconstruction gives the thread a genuine technical argument to have. It costs one evening of preparation and cannot be re-run, so it should be prepared like a launch and not fired off casually.

## What to do

**Pre-launch (one evening, the week before)**

1. **Confirm the account.** Show HN from a zero-karma account created that day gets auto-killed. Use an account with real comment history and 50+ karma. If there isn't one, spend two weeks commenting substantively on unrelated threads first. Do not create a new account for this.
2. **Freeze the site.** No deploys in the 48 h before, and none during the launch except to fix an outage. A half-broken feature discovered mid-thread is worse than a missing one.
3. **Check it survives no-JS and blocked trackers.** A large slice of HN runs uBlock Origin, NoScript, or Firefox strict mode. Load `<SITE_URL>` with JavaScript disabled: the gallery is htmx + Alpine, so confirm the page renders *something* useful (a server-rendered grid, or at minimum a legible message) rather than a blank cockpit. Confirm PostHog being blocked breaks nothing.
4. **Check gzip actually survives the proxy.** `nginx.conf` sets `gzip_proxied any` precisely because Traefik adds `Via`. Verify in production, not locally: `curl -sI -H 'Accept-Encoding: gzip' -H 'Via: 1.1 test' <SITE_URL>/ | grep -i content-encoding`. The planet index is ~2.8 MB raw / ~0.5 MB gzipped and every gallery visitor pulls it — uncompressed at 50 visitors/min that is ~140 Mbit/s of egress instead of ~25.
5. **Sanity-check capacity, then stop worrying.** Static files from `nginx:alpine` behind Traefik. Real front-page traffic peaks around 35–50 unique visitors/minute; that is single-digit requests/second. The only real risks are (a) gzip off, (b) a Dokploy/Traefik rate-limit middleware returning 429s on a burst — check the middleware list, (c) the host disk being full so the container can't restart. No CDN needed.
6. **Verify analytics before you need them.** Confirm `POSTHOG_KEY` is set as a build arg in production and that a test visit lands with `$referrer` populated. Cookieless mode must already be on. Analytics you fix *during* the spike measures nothing.
7. **Pick the three deep links you will paste in comments.** Suggested: HD 189733 b (measured deep blue — the credibility anchor), the `/roman` target board, and the raw dataset download. Have them open in tabs.
8. **Write the first comment in advance** (draft below) and paste it, don't compose it live.

**Launch hour**

9. Submit at `https://news.ycombinator.com/submit` with the bare canonical URL — no UTM, no trailing-slash variant, no query string. HN dedupes on URL and mods dislike tracking params on submissions.
10. **Post the author comment within 60 seconds.** This is the convention and it materially changes how the thread reads.
11. Then leave it alone. Do not refresh obsessively for the first 20 minutes; early rank is noisy.

**First six hours**

12. Answer every substantive comment, in your own voice, within ~15 minutes. Concede the true part of a criticism *first*, then explain. HN rewards this enormously.
13. Keep a scratch file open and log every technical objection. This thread is free peer review from people who may actually work on Roman or PICASO — it is worth more than the traffic.
14. If someone finds a real bug in the physics, say so publicly and fix it after the thread cools. "You're right, that's wrong, I'll fix it" is the single highest-scoring comment type on HN.
15. Around hour 3–4, if the thread is alive, post to Bluesky/Mastodon linking the *thread*, not the site (see [11-bluesky-mastodon.md](./11-bluesky-mastodon.md)). Never ask for votes.

**Do not, under any circumstances**

16. **Do not ask anyone to upvote.** Not friends, not a Slack, not a WhatsApp group. HN's voting-ring detector is good and it silently sinks the post with no appeal. This is the most common way a good launch is destroyed.
17. **Do not edit the title once votes are coming in** — the edit window closes anyway, and mods rewrite titles themselves if needed. Accept their rewrite silently.
18. **Do not argue.** One reply per hostile comment, factual, then stop. A flamewar triggers the automatic flamewar downranker (comment count outrunning score) and drops you off the front page.
19. Do not reply "thanks for the feedback!" to everything — it reads as marketing and adds noise.
20. Do not cross-post to Reddit the same day; save it (see [10-reddit.md](./10-reddit.md)).

## Copy

### Title candidates, ranked

HN's title field is **80 characters**. Count before you submit.

1. **`Show HN: Exoplanet Palette – 5,700 exoplanet colours, computed not photographed`** (79 chars)
   *Why it wins:* it is a flat declarative with a number, a name, and — critically — the honesty caveat baked into the title. That last clause does three jobs at once: it pre-empts the top comment ("these are made up"), it signals the project's actual editorial spine, and it is the surprising bit that makes an engineer click. No adjectives, no "beautiful", no "stunning", nothing a mod would rewrite.
2. **`Show HN: The colour of every known exoplanet, computed from albedo models`** (73)
   Nearly as good and slightly more austere. Loses to #1 only because "computed from albedo models" states the method without stating the *tension*; "computed not photographed" is the hook.
3. **`Show HN: Exoplanet colours from physics, and what Roman's 4 filters would keep`** (78)
   Leads with the signature feature. Best title *if* you think the Roman angle is the draw — but it presumes the reader knows what Roman is, which most don't. Keep in reserve for a later, Roman-launch-timed submission ([15-roman-launch.md](./15-roman-launch.md)).
4. **`Show HN: I computed a colour for all 5,700 known exoplanets`** (58)
   Clean, first-person, entirely acceptable. Ranked lower because it invites "so what" — nothing in it says the result is non-obvious.
5. **`Show HN: What colour is every known exoplanet? (Modelled, not photographed)`** (74)
   Question titles under-perform on HN and read slightly clickbaity. Listed so you can see why not to use it.

Avoid entirely: anything with "beautiful", "stunning", "the internet's", an exclamation mark, or a trailing period.

### The author's first comment (paste immediately after submitting)

> Author here. The short version of how it works:
>
> For each planet I take its parameters from the NASA Exoplanet Archive (radius, mass, equilibrium temperature, semi-major axis, host-star Teff), generate a geometric albedo spectrum across 380–780 nm — the fraction of starlight the atmosphere reflects at each wavelength — and multiply it by the host star's spectrum, which is the illuminant. That reflected spectrum goes through the CIE 1931 2° colour-matching functions to XYZ, then the standard matrix to linear sRGB, gamma encode, clamp. The albedo spectra come from PICASO and from the Cahoy et al. 2010 model grids; the colour maths is the `colour-science` package rather than anything I hand-rolled.
>
> The important caveat, which the site repeats everywhere: these are **modelled** colours, not photographs. Nobody has imaged these planets in visible light. Every planet page states the assumptions that produced its colour — cloud state, metallicity, phase angle — because those assumptions are doing a lot of the work. The five solar-system planets in there are the calibration check: they are built from real measured spectra and sit next to real photographs, so you can see how far the pipeline is off on worlds we actually know.
>
> The feature I actually built this for: the Roman Space Telescope's coronagraph will only see four narrow visible bands. Toggle "as Roman would see it" and you get the colour reconstructed from just those four samples, next to the full-spectrum colour. That difference is the question the whole project is asking.
>
> Happy to answer anything about the pipeline or where it's wrong.

(~250 words. Do not add a call to action, a "would love your feedback", or a link to a newsletter.)

## Prepared answers

**1. "These colours are made up. You have no idea what these planets look like."**
Correct, and the site says so on every page. What I'm computing is: *if* a planet has the atmosphere its mass, radius and temperature imply, this is the colour that physics says it would reflect. That's a model output, not an observation, and it's labelled as one everywhere. The value isn't "here's a photo", it's "here's what the physics predicts, stated precisely enough that a future measurement can contradict it."

**2. "Albedo models for planets with unknown atmospheres are garbage in, garbage out."**
Largely fair. The uncertainty is dominated by composition and clouds, not by the colour maths. That's why the solar-system anchors are in there: five planets computed from *measured* spectra, shown against real photographs, so you can see the size of the error on cases where we know the answer. Where the inputs are weak the output is weak, and I'd rather show the model plainly than dress it up as a rendering.

**3. "You can't know the cloud state, so the colour is arbitrary."**
The cloud state is an explicit assumption, printed on the page, not a hidden fudge. Clouds are the single biggest lever — a thick cloud deck pushes almost anything toward bright off-white, a cloud-free hot Jupiter goes dark and sodium eats the yellow. Two different cloud assumptions genuinely give two different colours; I picked one convention, documented it, and the phase/model controls let you see how sensitive the result is.

**4. "Why sRGB? Half of these must be out of gamut."**
Some are, and they're clamped — which is a lossy choice I made deliberately because the output is a palette people paste into a design tool, not a colorimetric record. The underlying XYZ and the downsampled spectrum (5 nm steps) are in the dataset, so if you want to render in Display P3 or Rec. 2020 the numbers are there and the clamp is yours to redo.

**5. "You normalise luminance, so the brightness is fake."**
Yes, and it has to be. Most of these worlds reflect a few percent of a star that is itself far away; rendered at true relative luminance the entire gallery is black rectangles. I normalise Y to a fixed value (0.6) for the base swatch so the *hue and chroma* — the part that carries information — is visible. The true geometric albedo is shown numerically on the planet page, so the brightness you're not seeing is still stated.

**6. "You're using blackbodies for the host stars. Real stars have absorption lines, and that changes the colour."**
It does, at the few-percent level for the integrated colour, and more if a strong feature lands in a narrow band. Blackbody-from-Teff is the v1 illuminant and it's an acknowledged approximation; PHOENIX/Kurucz model atmospheres are the upgrade path. For M dwarfs in particular the difference is not negligible and I'd expect that to be the first thing to move when I swap them in.

**7. "Microlensing planets have never been observed at all. Why do they have a swatch?"**
They're flagged as model-only, explicitly, because no light from them is ever received — the detection is a lensing lightcurve of the *star*, not the planet. Their swatches are pure inference from mass and orbit. I could have excluded them; I'd rather include them and mark them honestly, because "here is a thing we know exists and can say almost nothing about" is itself worth showing.

**8. "Isn't this just PICASO with a hex code stapled on?"**
PICASO does the radiative transfer, and I say so loudly — that's Batalha et al.'s work and the Cahoy grids underneath it, not mine. What I built is the pipeline around it: pulling and cleaning ~5,700 archive records including the null-`pl_eqt` fallback, running the spectra at scale, the CIE conversion and brightness convention, the four-band Roman reconstruction, and a site that explains each result in plain English. The physics is theirs; the "make it legible to a designer" part is mine.

**9. "Four bands can't reconstruct a spectrum. The Roman view is meaningless."**
It can't reconstruct the spectrum, and it isn't trying to — it's asking how much *colour identity* survives four samples, which is a different and answerable question. I integrate the full reflected spectrum through the four CGI bandpasses (575 nm/10%, 660 nm/6%, 730 nm/6%, 835 nm/15%, as top-hats for v1), interpolate between band centres, and run the same CIE step. Sometimes the answer is "almost all of it" and sometimes it's "the methane signature vanishes entirely" — that contrast is the point of the feature.

**10. "What phase angle? Full phase is unphysical for a coronagraph — you'd never observe at zero separation."**
Right, and there's a phase-angle slider for exactly that. The default is 20°, chosen so the illuminated fraction shown in the render matches the label rather than being a full disc you could never see. Quadrature-ish phases are what direct imaging actually gets, and the colour does shift with phase — the slider is there so you can check that yourself rather than take my default on faith.

**11. "How is this different from a NASA artist's impression?"**
An artist's impression is a person choosing colours to look plausible. This is a spectrum, a documented illuminant, and a standard colorimetric transform, with the assumptions printed and the numbers downloadable. It can be wrong — but it can be wrong *in a checkable way*, which is the whole difference.

**12. "Where's the data? Can I use this?"**
Whole dataset is downloadable, spectra downsampled to 5 nm, plus per-planet palettes as hex, CSS variables and .ase. Details in [06-open-data.md](./06-open-data.md) / [05-machine-readable.md](./05-machine-readable.md). (Have this link ready — it converts a drive-by upvote into a citation.)

## Timing

- **Portugal is WEST (UTC+1) in summer, WET (UTC+0) in winter.** Every time below is given in both.
- **Primary slot: Tuesday or Wednesday, 13:00 UTC** = **14:00 Lisbon (WEST)** / 13:00 Lisbon (WET) = 09:00 US Eastern. This is the maximum-audience window: US East Coast starting the day, West Coast waking, Europe still at work. `/newest` competition is heaviest here, so a weak title dies fast and a strong one compounds fast.
- **Secondary slot, and the realistic one for someone with a day job: Sunday, 12:00 UTC** = **13:00 Lisbon (WEST)**. Analysis of ~157k Show HN posts (Myriade, on the HN BigQuery dataset) puts weekend "breakout" rates — reaching 30+ points — roughly 20–30% *higher* than weekdays, because submission volume drops more than readership does. Absolute ceiling is lower; odds of being seen at all are better.
- **Pick the slot you can actually sit in front of for six hours.** Being present in the thread matters more than the hour. A Tuesday launch you have to abandon at 15:00 for a meeting is worse than a Sunday one you can babysit.
- **Never** Friday afternoon or Saturday morning European time. Never during a major tech news event that will own the front page.
- **Resubmission.** HN's own stated norm: if a post got no significant attention, "a small number of reposts is ok." So — if it dies with under ~10 points and a couple of comments, waiting several weeks and resubmitting once, ideally with a different title from the ranked list, is entirely within the rules. If it got real traction (50+ points), do **not** resubmit; the next submission must be a genuinely new artefact (the open dataset, the Roman launch tie-in). You may also email hn@ycombinator.com about the second-chance pool, but dang's stated preference is that pool suggestions come from readers rather than authors — so ask, briefly, once, and accept a no.

## How we'll know it worked

- **Primary metric:** *unique visitors on launch day with referring domain `news.ycombinator.com`* in PostHog. Front page for an hour is roughly 3,000–4,000 visitors; a strong day is 8,000–15,000; a top-slot day can exceed that.
- **Quality metric, which matters more:** *share of HN-referred sessions that view ≥2 planet pages*. A gallery that people scroll and leave is a screensaver; a gallery people navigate is a tool. Target ≥35%.
- **Durable metric:** number of distinct referring domains in the 14 days *after* launch (blogs, aggregators, .edu). One HN thread typically seeds 10–30 of these, and they outlive the spike.
- **UTM:** do **not** put UTM params on the submitted URL — it looks like marketing and HN readers notice. Identify the main wave by referrer. Tag only the links you paste *inside* comments: `?utm_source=hn&utm_medium=comment&utm_campaign=showhn-2026`, so you can tell "clicked the story" from "read the thread and followed the dataset link". Full scheme in [99-tracking.md](./99-tracking.md).
- **Success:** ≥100 points, ≥40 comments, at least one comment from someone who works on exoplanet atmospheres or Roman, and no factual claim on the site left standing as wrong. **Failure:** under 10 points after two hours — which is the *median* outcome and says almost nothing about the project, only that it wasn't seen.

## Risks

- **Vote solicitation is fatal and irreversible.** The most likely way this launch fails is sharing the link in a group chat with "upvote please". Assume the detector works.
- **A wrong number in the thread is worse than no thread.** The project's entire position is honesty; being caught overstating what the model knows would cost more than the traffic is worth. Hence the prepared answers — improvise the tone, never the facts.
- **One shot, genuinely.** Unlike Reddit or Bluesky, a burned HN submission on a strong hook is hard to re-run without a new artefact. If preparation isn't done, postpone; there is no deadline.
- **The tail risk in the other direction:** it does well and the traffic arrives with nothing to catch it. There is no mailing list and building one for this isn't worth it — instead make sure the repo link, the dataset, and an RSS/Atom feed are visible, so interest converts into a star or a bookmark rather than evaporating.
- **Low-value temptations to refuse:** paying for any "HN boost" service (all are voting rings), posting a second Show HN for a minor feature (HN excludes version updates that aren't major overhauls), and rewriting the site in response to the loudest commenter.

## Links

- [Marketing plan](./README.md) — hub
- [99-tracking.md](./99-tracking.md) — the UTM scheme and the PostHog dashboard to have ready before launch
- [06-open-data.md](./06-open-data.md) — the dataset link to paste in the thread; HN converts to citations better than any other channel
- [05-machine-readable.md](./05-machine-readable.md) — API/format questions will come up in the thread
- [10-reddit.md](./10-reddit.md) — the deliberately *separate*, later push; do not run same-day
- [11-bluesky-mastodon.md](./11-bluesky-mastodon.md) — where to amplify the thread mid-launch
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — PICASO and Cahoy attribution; the thread will ask, and getting this right is what earns the astronomers' goodwill
- [02-press-kit.md](./02-press-kit.md) — journalists read HN; have the kit up before you submit
- [15-roman-launch.md](./15-roman-launch.md) — the one legitimate reason for a second HN submission later
