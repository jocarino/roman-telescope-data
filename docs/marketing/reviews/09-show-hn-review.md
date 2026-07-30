# Review — 09 Show HN

*Reviewed by: fifteen-year HN reader, several Show HNs on the front page and several that sank without trace. Adversarial on purpose.*

## Verdict

**revise** — the tactics and the voice are unusually good for a first launch, but the doc tells you to walk into the thread stating an instrument configuration your own sibling doc proves is wrong, and it has no plan for the twelve hours after you fall asleep.

## What's right

- The title work is genuinely strong. "computed not photographed" is the whole project in three words and it pre-empts the top comment. Ranked #1 is correct and I'd not change it.
- "Concede the true part first, then explain" and "improvise the tone, never the facts" are the two rules that actually decide HN threads. Most launch plans miss both.
- Correctly refuses the fatal move (vote solicitation) and correctly refuses same-day Reddit cross-posting.

## Gaps

**1. The Roman band config is wrong on the site, and this doc puts it in your mouth.**
`pipeline/config.py` ships 575/10%, 660/6%, 730/6%, 835/15%. `15-roman-launch.md` documents, from the Jan 2025 CPP flight Primer, that Band 2 at 660 nm **is not in the flight configuration**, Band 3 is 15% not 6%, Band 4 is 825/10% not 835/15%, and that **only Band 1 with the hybrid Lyot is formally supported**. The doc's author-comment and prepared answer #9 both recited the stale numbers. On a site whose entire pitch is honesty, being corrected on your own headline feature by someone who works on CGI is not a bad comment — it is the comment the thread remembers. Worse: the correct fact is a *better* story ("Roman's guaranteed output is one photometric point per planet"). You were shipping the weaker and wrong version. Fixed in the doc; the code fix is still yours.

**2. No prerequisite list, and the prerequisites are real.**
The hub calls `13-credit-the-scientists.md` *blocking and overdue* with an unmet CC BY obligation. There is no `credits.html` and no `press.html` in `web/templates/`. HN is precisely the audience that checks attribution on someone else's model grids. A licence failure discovered mid-thread doesn't cost you upvotes, it costs you the astronomers — the exact people doc 13 is trying to win. The doc mentioned neither. Added as blocking prerequisites A0–A3.

**3. The prepared answers do not survive a colour-science pedant.** Specifically:

- **The white point is missing entirely.** This is the *first* question a colorimetrist asks and it wasn't in the list. Do you chromatically adapt to the host star, or hold D65? A neutrally-reflecting planet around an M dwarf is grey under the first and deep orange under the second. There is no right answer, but "I hadn't thought about it" is a fatal answer, and the follow-up — "is your Roman leg adapted identically to your full-spectrum leg?" — invalidates the signature comparison if it's no. Added as answer 13.
- **Answer #4 (gamut) concedes something untrue.** "Some are out of gamut" — almost none are. A broadband reflectance times a broadband illuminant is inherently low-purity; those chromaticities sit comfortably inside sRGB. What you actually clip is overshoot manufactured by your own luminance normalisation. Conceding a non-existent gamut problem tells a pedant you don't know what a gamut is, which then discredits answers 5 and 6 by association. Rewritten.
- **Answer #6 (blackbodies) invents a number and then contradicts it.** "Few-percent level" is unmeasured, and the same paragraph admits M dwarfs are worse — which is true and much worse than a few percent, because TiO/VO bands gut the visible SED. Since M dwarfs are a large share of the catalogue, the "few percent" claim is wrong for the modal planet in your dataset. Rewritten to concede properly and to suggest measuring two ΔE00 values before launch day.
- **"Geometric albedo" + a phase slider is a terminology error** someone will catch. Geometric albedo is defined at zero phase; at 20° you have a flux ratio. Added as answer 14.
- **The unaskable question was missing: how many of the 5,700 are actually measured?** Most exoplanets have no measured radius, many no mass. `pipeline/catalog.py` already tags Teq provenance `measured`/`computed`/`assumed`, so the counts are one query away. Walking in without that number is the single most likely way to lose the thread on the merits. Added as answer 15.

**4. No plan for the success failure mode.** "Sit in front of it for six hours" does not cover a thread that runs 24. Submitted 13:00 UTC, the US afternoon wave lands after midnight in Lisbon. The doc had nothing for hours 6–24. Added a section: post the timezone comment *before* sleeping, triage oldest-first on waking, pre-decide the only two things worth waking for.

**5. The failure mode is handled, but by the wrong lever.** For a sub-10-point death the doc reaches for resubmission. Resubmission is a months-later move (see below). The same-week levers it doesn't mention: the post keeps living on `/show` and `/shownew`, which people genuinely browse; a good thread can be seeded by a *reader* mailing hn@ for the second-chance pool; and a dead Show HN is not deleted — deleting it is the one thing that forecloses everything.

**6. Nothing decides HN against the calendar.** Roman launches 30 Aug 2026, four weeks out. This doc is "one shot, cannot be re-run" and the hub schedules it in Phase 1 behind three other docs. Whether the shot is fired *before* launch (own the "here's what it will see" frame first), *during* launch week (contested, you lose the front page to NASA), or held for the 2027 tech demo is the single highest-leverage decision in the whole plan — and neither this doc nor the hub actually makes it. It's deferred to doc 15 as "keep title #3 in reserve", which is not a decision.

## Wrong or unverified

- **80-character title limit — confirmed.** Long-standing and enforced. But two of the five counts were off by one: #4 is 59 not 58, #5 is 75 not 74. Corrected. A doc that says "count before you submit" and then miscounts is a bad look.
- **"Zero-karma account created that day gets auto-killed" / "use 50+ karma" — overstated folk wisdom.** There is no published karma threshold for submitting, and Show HN has none. What is real: new/very-low-karma accounts' submissions frequently land dead via anti-abuse and need *vouching* by 31+ karma users, which for an unseen post never happens. Same practical advice, honest basis. Corrected.
- **Show HN rules — confirmed verbatim.** "Show HN is for something you've made that other people can play with"; "Please don't ask friends to upvote or comment. That's not ok on HN."; version bumps don't qualify. The doc represents all of these accurately.
- **Resubmission norm — the quote is right, the timescale is wrong.** FAQ: *"If a story has not had significant attention in the **last year or so**, a small number of reposts is ok."* The doc said "several weeks". Also missing the mechanic that makes waiting mandatory: **resubmitting a URL HN still holds counts as an upvote on the existing post**, so an early retry silently does nothing. Corrected.
- **Second-chance pool — confirmed and the doc's nuance is right.** Suggestions go to hn@ycombinator.com; it's fine if it's your own, but they prefer reader-sourced. Pool entries get randomised front-page placement. Accurately stated.
- **Myriade timing data — confirmed exactly.** 157k+ Show HN posts since 2009, breakout = 30 points, Sunday 11.75% vs weekdays 9.45–9.90%, peak 12:00 UTC at 12.2%, golden window 11:00–16:00 UTC. But the doc then ranks Tue/Wed **primary** and Sunday **secondary** — the opposite of the only evidence it cites. The weekday case rests on "higher absolute ceiling", which is asserted, not measured. Flagged in-doc, with the two caveats the Myriade piece invites (17-year average; rate-over-posts, not a controlled comparison).
- **Flamewar/"overheated discussion" detector — confirmed.** Kicks in above ~20 comments when comments outrun points; dang and Scott are emailed and do reverse it. The doc's advice is right.
- **Author edit window — the doc said "closes anyway" without a number.** It's roughly two hours; mods can retitle indefinitely. Made concrete.
- **Could not verify:** the traffic figures (3,000–4,000 visitors/hour on the front page; 8,000–15,000 for a strong day) and the "35–50 unique visitors/minute" capacity estimate. These are plausible and widely repeated but I found no primary source. They're only used for capacity planning, where being wrong is cheap — but don't quote them to anyone.

## Better approaches

**1. Fire it as the Roman pre-launch authority, roughly 7–14 days before 30 Aug — with the corrected band config.** Ranked first because it converts a generic "pretty physics site" into a *timely* one, which is the difference between 40 points and 400. The hook writes itself and it's true: *"Roman launches in two weeks. Its guaranteed coronagraph output is one 10%-wide photometric point per planet. Here's exactly what one number buys you."* That is a genuinely surprising, checkable, adversarial claim — the shape HN rewards — and it is the frame nobody else has. Two weeks out, you own the question before every outlet asks it; launch week itself you'd be competing with NASA's own coverage and lose. This requires A0–A3 done in four weeks, which is tight but is the same work the hub already calls blocking.

**2. Keep the current plan, but swap primary and secondary slots to Sunday 12:00 UTC.** Ranked second because it's free. The doc's own evidence supports Sunday; the weekday ceiling argument is unmeasured; and for a solo author in Portugal with a day job, Sunday is the only slot where full-day presence is realistic — and presence beats the hour, as the doc itself correctly says. The internal contradiction should be resolved in the data's favour, not against it.

**3. Split the shot: dataset first as a regular submission, site later as Show HN.** Ranked third — lower ceiling, much lower variance. A plain link to the open dataset ([06](../06-open-data.md)) is not a Show HN and doesn't burn the Show HN. If it lands, you've built karma, inbound links and a citation base; if it dies, nothing is spent. Then the Show HN follows weeks later with "you may have seen the dataset". The cost is that the dataset alone is a weaker hook than the site.

**4. Don't submit it yourself at all.** Ranked last, but worth naming: an organically-submitted link posted by a reader, with you showing up in the comments as the author, outperforms a Show HN roughly as often as not, has no one-shot cost, and can be repeated. The problem is you can't manufacture it without it being vote manipulation. Mentioned only so it's a considered rejection rather than an oversight.

## The one thing I'd change

**Fix `pipeline/config.py` to the flight band configuration and rebuild before you go anywhere near the submit form.** Everything else in this doc is optimisation around a launch that, as currently specified, opens with the author confidently stating a superseded instrument config as the basis of the headline feature. It is the one error that attacks the project's only real differentiator — and the corrected version ("one guaranteed number per planet, everything else best-effort") is a strictly better story than the wrong one.

## What I edited

Direct edits to `docs/marketing/09-show-hn.md` (structure, `**Status:**` line and `## Links` preserved):

1. Added a **Blocking prerequisites** section (A0 band config, A1 credits/licence, A2 press + SEO, A3 something to catch traffic) before "What to do".
2. Rewrote item 1 (account) to drop the unsupported "50+ karma / auto-killed" claim for the verified auto-kill-plus-vouching mechanic.
3. Corrected the author's first comment: removed the stale four-band recital, replaced with the Band 1 formally-supported framing.
4. Rewrote prepared answer **9** to the Primer configuration (575/10%, 730/15%, 825/10%; only Band 1 supported) with an explicit note that 660 nm is not in the flight config.
5. Rewrote prepared answer **4** (gamut) — the colours are mostly *in* gamut; the clipping comes from luminance normalisation.
6. Rewrote prepared answer **6** (blackbodies) — removed the unmeasured "few percent", made the M-dwarf concession properly.
7. Added prepared answers **13** (white point / chromatic adaptation), **14** (geometric albedo vs phase), **15** (how many planets are actually measured).
8. Added an **Hours 6–24: the part where you are asleep** section.
9. Timing: added the verified Myriade figures and flagged the primary/secondary contradiction against the doc's own evidence.
10. Resubmission: corrected "several weeks" to the FAQ's "last year or so" and added the resubmit-counts-as-an-upvote mechanic.
11. Item 17: made the ~2-hour author edit window concrete.
12. Corrected title character counts (#4 58→59, #5 74→75) and noted the counts were re-verified programmatically.
