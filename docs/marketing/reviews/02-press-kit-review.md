# Review — 02 Press kit

*Reviewed by a science press officer — twenty years of observatory and agency releases, and of watching good paragraphs get replaced by a rewrite.*

## Verdict

**Good instincts, unusable as briefed** — it knows images and honesty decide the story, but it ships no specifications, no named human, and no contact plan, which are the three things a journalist emails to ask for.

## What's right

- **"A writer has ninety minutes to file"** is the correct model of the reader, and almost no press kit written by a maker starts there.
- **Build-time figures from `planets.json`.** Correct, and the risk it names (a stale number destroying an honesty positioning) is the real one.
- **Naming the honesty paragraph as the highest-value item.** Right diagnosis. Wrong prescription — see below.

## What a journalist will email to ask for

Everything here is a real email I have received, and every one of them costs a day the writer does not have.

- **A person.** "Built by one person" is the hook and the doc never names him. A desk cannot print "one person"; it prints a name, a job, a town and a face. Needed: full name as it should appear in print plus the accent-free fallback (`João`/`Joao`), a one-line bio, and a 1200 px square headshot under the same licence. Supply it or they crop your LinkedIn photo badly. State plainly that there is no astronomy affiliation — a desk that finds this out at the fact-check stage kills the piece; a desk told up front runs "a software engineer in Portugal, in his own time", which is a better line anyway.
- **Second sources.** Every science desk needs one voice that isn't you before it runs a claim. Name three: the albedo-paper authors, the PICASO maintainers, the CPP contacts in [15](../15-roman-launch.md). This is the most professional thing you can put on the page and it costs nothing.
- **Actual image specs.** "2400px+" is not a spec. Missing: format per asset (PNG-24 for UI, JPEG q90 for renders, both under 5 MB), a 3000 px master plus a 1200 px web copy, no browser chrome, defined 16:9/1:1/3:2 crops with dead margin, and one `press.zip`. Above all **an embedded sRGB profile on every file** — a colour project whose press images get colour-shifted by a CMS has failed at its own subject, and untagged PNGs are re-interpreted downstream routinely.
- **IPTC/XMP metadata.** Write `Creator`, `Credit`, `Description`, `CopyrightNotice`, `WebStatement` into every file with `exiftool`. Journalism image standards assume the caption and credit live in the IPTC fields; more importantly it is the only way the credit and the words "not a photograph" survive the file being detached from your page.
- **Captions.** The doc promises "a caption written for them" and supplies none. Supply the string, per image, ~25 words.
- **A credit line, in two forms.** Online with a link; print without one, because print cannot carry attribution in a hyperlink. Plus explicit pre-authorisation for crops and colour-space conversion, which is the CC BY clause picture desks stall on.
- **Motion.** Absent entirely, and [12](../12-design-newsletters.md) treats it as a hard requirement. Needed: the 8–12 s phase clip as MP4 *and* GIF under 5 MB; a **broadcast-safe 1920×1080 H.264 cut with no music, no on-screen text and no logo** (anything with a soundtrack is unusable to a video desk and they will not ask twice); a 1080×1920 vertical.
- **Availability.** Timezone (WEST/UTC+1), languages (Portuguese *and* English — Portuguese-language desks are an uncontested audience nobody in this plan has noticed), notice needed for a recorded call, and whether you will do live. An unanswered request is worse than a stated no.
- **Launch night.** Roman lifts at 07:26 EDT on 30 Aug; US desks file past midnight Lisbon time. One line on the page — *"29 Aug–2 Sep, mark the subject URGENT and it reaches my phone"* — plus the filter actually set. In that week being a single person with a phone beats an institution with a duty officer.
- **Known limitations.** Blackbody illuminants, cloud assumptions, no phase-curve validation. A fact-checker is going to establish these anyway; publishing them converts five emails into zero.
- **A footer email.** There is currently no footer, no About page and no address anywhere on the site. Today there is no way to reach him at all.

## Making the caveat survive the rewrite

The doc's plan is to write a better caveat paragraph. It will still be cut, and by someone who never read the press kit.

Understand the mechanism before the fix. Caveats die because they sit in their own paragraph and pieces are trimmed from the bottom; because they are negatives and negatives are the cheapest words to lose; because nothing else in the piece depends on them; and because the person cutting them is a sub-editor on deadline working from the headline, the picture and the caption. **Write for that person, not for the writer you emailed.** So: assume the paragraph dies, and put the honesty in six places it cannot be cut from. All six, one evening.

1. **Inside the noun.** Never "the colours (which are modelled)". Always **"computed colour"** — in every caption, filename, alt text, blurb and email. A modifier inside a noun phrase cannot be removed without rewriting every sentence containing it, and no sub does that on deadline. This is precisely why *"artist's impression"* has survived forty years: it is not a disclaimer, it is the name of the thing. You are competing with that phrase and you need one of your own. Choose it once and never vary it.
2. **In the caption.** Captions are almost never cut — the space is already allocated — and they are assembled last from whatever the supplier wrote. That makes a 25-word caption the caveat's real home: *"Computed colour of HD 189733 b, derived from its modelled reflected-light spectrum and its star's light. Not a photograph — no exoplanet has ever been photographed in visible colour."*
3. **Burned into the image.** `COMPUTED COLOUR · NOT A PHOTOGRAPH`, small, in the safe margin, in the site's own type. This is the only version that survives cropping, screenshotting, being lifted off Bluesky, or running with no caption at all. Observatories watermark artist's impressions for exactly this reason. It is the difference between honesty asserted and honesty physically attached to the file.
4. **Inside the one quotable sentence.** Journalists lift whole sentences. Give them exactly one, and put the caveat in its subject: *"Nobody has ever photographed the colour of a planet around another star. So I computed all 5,700 of them, and the site tells you where the model ends."* Cutting the caveat now costs them the quote.
5. **As a number, not a hedge.** *"Five of these 5,700 worlds have ever been photographed, and all five are in our own solar system."* Editors cut hedges and keep statistics: a number reads as reporting, a hedge reads as legal. That sentence reaches the standfirst; a hedge never does. Same move on Roman — *"one guaranteed measurement per planet."*
6. **Make the honesty the story, so cutting it costs the editor the piece.** This is the structural fix and everything above is insurance. "Pretty planet colours (with caveat)" is a picture story with a hedge attached, and it will be cut to the picture — correctly, by the editor's logic. The available framing is one nobody else is running: **almost every exoplanet image you have ever seen is an artist's guess; this is what we actually know; and Roman, launching this month to look at these planets, will return one number per planet, not a picture.** Now the caveat is the premise, the antagonist is the artist's impression, and there is real tension. [15](../15-roman-launch.md)'s information-budget argument and the pre-registered, self-graded predictions are the same move: honesty *demonstrated*, not asserted. A project that publicly scores its own wrong predictions cannot have its honesty edited out, because the honesty is what is being reported.

Two mechanical extras that punch above their weight. A **"please write this, not that"** box — four lines, two columns; subs are not trying to be wrong, they are trying to be fast, and this is the cheapest item on the page. And **offer to check the caption**: *"send me your caption and I'll check it within the hour — no approval, no changes to your copy, just the physics."* Costs them nothing, protects them, accepted far more often than you'd expect. Never ask to see the article.

Last: delete the words "caveat" and "disclaimer" from the page. Head the section **"How to describe these images"**. One is a condition imposed on the writer, the other is a service done for them, and they get filed accordingly — the first with the legal boilerplate, which is the part of a press kit nobody reads.

## Wrong or unverified

- **"The four Roman bands"** (Facts and figures, and the 150-word copy) is contradicted by this plan's own [15](../15-roman-launch.md): the Jan 2025 CPP Primer lists Band 1 575/10%, Band 3 730/15%, Band 4 825/10%, no 660 nm band, and **only Band 1 HLC imaging is formally required**. A press page that gets Roman's instrument wrong, on a project whose pitch is accuracy, is the worst error available here — it gets reprinted, and it gets caught by the exact CGI people you most want as allies. **Fixed in the doc.** The band-model correction is blocking for `/press`, not only for `/roman`.
- **"Recommend CC BY 4.0 on the renders… reserve all rights on nothing."** CC BY 4.0 is the right call and is verified as the sector norm — ESO, ESA/Webb and ALMA all release press imagery under it, so science desks already have a workflow. But the blanket grant is a licence he does not hold: `pipeline/observations.py` shows planet pages carry ESA/Webb frames credited *"NASA, ESA, CSA, STScI, W. Balmer (JHU), L. Pueyo & M. Perrin (STScI)"* and five NASA public-domain photographs (NASA/JPL, NASA/JPL-Caltech, NASA/JPL/Space Science Institute, Apollo 17 crew). Fix: per-asset licence table, and build the hero, the true↔Roman comparison and the Band-1 still from rendered swatches only so the flagship images are unencumbered. Also state that CC BY 4.0 is **irrevocable and permits commercial reuse forever** — that is the point, but it should be a decision, not a surprise.
- **Unverified but load-bearing:** the "no tracking beyond cookieless analytics" claim. PostHog is build-key-gated, so it's plausibly true — but a privacy-minded writer will open the network tab. Name the vendor and the setting.
- **"~5,700"** floats against 5,764 in the release notes. The doc already prescribes the fix; make sure the *copy blocks* are generated too, not just the bullets.

## Better approaches

1. **`/about` first, `/press` second — two thin pages, same evening.** `/about` is the human page (name, face, bio, email, "using these images"); `/press` is the asset page, titled in plain language, that you paste into pitch emails. This fixes the pretentiousness objection properly: a corporate `/press` page argues *against* the "one person, evenings" pitch that [12](../12-design-newsletters.md) is entirely built on, while a NASA comms officer genuinely does need a stable asset URL. Split the audiences rather than compromising one page between them.
2. **Ship the metadata and the burned-in label before you ship a single pitch.** sRGB profiles, IPTC fields, the corner label. This is two hours of `exiftool` and a render tweak, and it is the only part of the honesty strategy that works when you are not in the room.
3. **A footer email on every page, today, before any of the above.** The site currently offers no way to contact its author. Everything else in this doc is optimisation on top of an unreachable project.
4. **Write the captions and the credit line before the images exist.** They constrain what the images need to show, and they are the artefacts that actually travel.
5. **Do not build a media centre.** No logo lockup, no brand guidelines, no third person, no "pleased to announce". For half this plan's audiences the amateurism is the asset.

## The one thing I'd change

Stop treating honesty as a paragraph to be preserved and start treating it as the noun, the caption, the pixel and the premise — **"computed colour", burned into the image and carried in the IPTC fields** — because the person who deletes your caveat is not the person you emailed, and they will never read your press kit.

## What I edited

In `02-press-kit.md`, preserving structure, the `**Status:**` line and `## Links`:

- **Corrected "the four Roman bands"** in Facts and figures, and rewrote that clause in the 150-word copy block, with a blocking note pointing at the Primer table in [15](../15-roman-launch.md).
- **Added a full specifications table** to the images section: sRGB embedded, formats, 3000 px master + 1200 px copy, crops with dead margin, IPTC/XMP fields, alt text, `press.zip`. Added the Band-1-only still to the asset list.
- **Added a motion-assets block** (MP4+GIF, broadcast-safe 1080p with no music or text, vertical cut).
- **Rewrote item 3** from "the honesty paragraph" to "How to describe these images", pointing at a new **`## Making it survive the rewrite`** section carrying the six-place argument, the write-this-not-that box, and the caption-check offer.
- **Rewrote item 5 (licence)**: third-party imagery cannot be blanket-licensed, per-asset table, keep flagship images unencumbered, both credit-line forms, pre-authorised crops/conversions, irrevocability stated.
- **Rewrote item 6 into "Contact — and the human"**: name and accent fallback, bio, no-affiliation statement, headshot spec, timezone, languages, availability, the launch-night URGENT line, footer email.
- **Added items 7 and 8**: story menu + known limitations, and second sources.
- **Added the `/about` vs `/press` split** to "What the page contains", and an asset reconciliation note to "How it gets used" covering what [12](../12-design-newsletters.md) and [15](../15-roman-launch.md) actually specify.
- **Added four risks**: wrong Roman instrument, licensing images you don't own, looking like a press office, the unreachable moment.
