# Review — 04 Wikimedia Commons

*Reviewed by a long-standing en.wp administrator and Commons contributor, WikiProject Astronomy regular.*

## Verdict

**`parked` is right for the article-placement campaign and wrong for everything else** — the doc reaches a defensible conclusion through four misread policies, and gates the whole thing behind a Zenodo DOI that will never unblock anything on Wikipedia.

## Where the policy reasoning is wrong

**1. "Wikipedia will treat our colours as original research" — wrong project, and wrong rule.**

Commons has no no-original-research policy. The only gate is [Commons:Project scope](https://commons.wikimedia.org/wiki/Commons:Project_scope) (COM:SCOPE): a file must be "realistically useful for an educational purpose", where educational means "providing knowledge; instructional or informative". Self-created diagrams are hosted there by the million. Nothing about these colours is inadmissible *on Commons*, today, DOI or no DOI.

On Wikipedia, [WP:NOR § Original images](https://en.wikipedia.org/wiki/Wikipedia:No_original_research#Original_images) (WP:OI, WP:IMAGEOR) says nearly the opposite of what the doc asserts: *"Original images created by a Wikimedian are not considered original research, so long as they, or their captions, do not illustrate or introduce unpublished ideas or arguments."*

So the objection is not "you made it". It is narrow — *the claim the image makes* — and that distinction decides which images are admissible **now**:

- A swatch for a planet nobody has published a colour for: an unpublished argument. Blocked, and permanently by this route.
- An illustration of a **published** colour result — HD 189733 b's deep blue (Evans et al. 2013) — illustrates a source rather than arguing. Admissible now.
- A **method diagram** (albedo × stellar spectrum → CIE 1931 → sRGB) illustrates published physics. Admissible now.

The doc's blanket "an editor removing our image would be applying the policy correctly" is true for 5,690 planets and false for the handful that matter.

**2. "Adding your own work to articles is a conflict of interest" — backwards.**

[WP:COI § Supplying photographs and media files](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest#Supplying_photographs_and_media_files): *"Editors with a COI are encouraged to upload high-quality media files… In some cases, the addition of media files to an article may be an uncontroversial edit that editors with a COI can make directly, but editors should exercise discretion and rely on talk pages when images may be controversial or promotional. If the addition of an image is challenged by another editor, it is controversial."*

[WP:COI](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest) is a *guideline*, not a policy. It asks for disclosure ({{connected contributor}}), discretion, and immediate deference if challenged — not abstention. The *policy* here is [WP:PAID](https://en.wikipedia.org/wiki/Wikipedia:Paid-contribution_disclosure), and it does not apply: this is unpaid. The doc names neither mechanism, so it treats a manageable disclosure obligation as a prohibition.

Where the doc is right, it cites the wrong rule. Doing this across hundreds of articles *is* a problem — but the rule is [WP:SELFCITE](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest#Citing_yourself) ("adding numerous references to work published by yourself… is considered to be a form of spamming") and [WP:REFSPAM](https://en.wikipedia.org/wiki/Wikipedia:Spam#Citation_spamming), not COI at large.

**3. "Publish the dataset with a DOI" — the central error, and the flip sequence rests on it.**

[WP:RS § Preprints](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources#Preprints) (WP:PREPRINT) names Zenodo explicitly, alongside arXiv, medRxiv and bioRxiv: *"These materials are seldom reliable sources."* A DOI is a resolver handle, not an editorial process. A self-deposited dataset is [WP:SPS](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources#Self-published_sources) — "self-published sources are largely not acceptable" — and the expert exception requires someone "whose work in the relevant field has previously been published by reliable, independent publications", which a hobby project does not satisfy by construction. **Step 1 of the doc's sequence buys nothing on Wikipedia.** (Still worth doing for the reasons in [06-open-data.md](../06-open-data.md) — citability, timestamped pre-registered predictions. Just not this one.) Step 2 — independent coverage, or a peer-reviewed paper — was always the step doing the work.

**4. "The traffic return is worse than assumed" — right, and understated for the wrong reason.**

It is not merely that the file page is a click away. Two policies shut the door completely: [WP:ELPOINTS / WP:NOELBODY](https://en.wikipedia.org/wiki/Wikipedia:External_links#Important_points_to_remember) — "with rare exceptions, external links should not be used in the body of an article" — kills the caption link; and [WP:IUP](https://en.wikipedia.org/wiki/Wikipedia:Image_use_policy) — "free images should not be watermarked… have any credits or titles in the image itself" — kills the baked-in URL. There is **no in-article link surface, by policy, ever.** This cannot be a traffic play. Say that flatly rather than "very small".

**5. "Mass uploads mean a bot flag" — the bureaucracy is not the risk; deletion is.**

No bot flag is needed at these volumes; ordinary accounts are rate-limited (~380 uploads / 72 min) and the convention is a proposal subpage at [Commons:Batch uploading](https://commons.wikimedia.org/wiki/Commons:Batch_uploading). The real hazard is COM:SCOPE: thousands of near-identical procedurally generated discs invite a mass deletion request under "not realistically useful for an educational purpose" and "[self-created artwork without obvious educational use](https://commons.wikimedia.org/wiki/Commons:Project_scope/Summary)". A deletion risk, not a weekend of process.

## What it missed

- **The addressable set is not 5,700.** [WP:NASTRO](https://en.wikipedia.org/wiki/Wikipedia:Notability_(astronomical_objects)) says individual exoplanets are not automatically notable; its worked example, HAT-P-40 b, has no article. Most live as rows in `Category:Lists of exoplanets`; `Category:Exoplanet stubs` holds ~411 pages. Low hundreds of image-capable articles, not thousands — which kills mass upload on its own.
- **The best target is not a planet article.** [Sudarsky's gas giant classification](https://en.wikipedia.org/wiki/Sudarsky%27s_gas_giant_classification) is an article *about modelled exoplanet colours from published theory*, currently illustrated with renders from the Celestia hobbyist simulator. A physics-derived five-class illustration sourced to Sudarsky et al. 2000/2003 is a straight upgrade and is not OR. Same logic for **Geometric albedo** and **HD 189733 b**. Three admissible placements the doc never considered.
- **Wikidata: don't.** [Wikidata:Verifiability](https://www.wikidata.org/wiki/Wikidata:Verifiability) requires references; P465 (sRGB colour hex triplet) on an exoplanet item sourced to your own site is the same SPS problem with *less* editorial friction to catch it — more of a COI hazard, not less. The only clean contribution there is non-colour housekeeping (missing archive identifiers, discovery refs), and it isn't worth an evening.
- **Commons discovery is structured data now, not categories.** MediaSearch ranks on [depicts (P180)](https://commons.wikimedia.org/wiki/Commons:Depicts) statements and captions — 27M+ files carry them. The discovery work is depicts + multilingual captions, not category placement.
- **COM:INUSE is the asymmetry.** A file used on any WMF project is automatically in scope and effectively deletion-proof. One accepted placement settles hosting permanently.
- **Free imagery mostly does fill the gap — except in one place.** Commons `Category:Exoplanets` has ~189 root files and 298 by-name subcategories over a large PD-NASA / CC BY 4.0 ESO–ESA corpus. The famous planets are covered. What exists nowhere is an image of *reflected-light colour derived from physics rather than an artist's choice*. That gap is real, and it is one image wide.
- **Wrong venue.** For exoplanet articles the forum is [Wikipedia talk:WikiProject Astronomical objects](https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Astronomical_objects), not WikiProject Astronomy.
- **Licence inconsistency.** 06 picks CC BY 4.0 for data, 04 picks CC BY-SA for images. Both are Commons-acceptable, but share-alike adds friction for exactly the educators and bloggers the doc wants reusing them. Use CC BY 4.0.

## The policy-compliant version

All of this is doable **this month**, with no DOI and no coverage.

1. **Upload three or four files, not thousands.** (a) the method diagram; (b) a five-panel Sudarsky class illustration; (c) an HD 189733 b swatch labelled as consistent with the published measurement; (d) optionally the catalogue hue-distribution plot. SVG where possible, CC BY 4.0, no watermark, no URL in the pixels.
2. **Write the file descriptions like a methods section.** Inputs, model assumptions (cloud state, metallicity, phase angle), the CIE step, the luminance convention, and the sentence *"modelled, not photographed"*. Link the source and the papers in the description text — that is attribution, and it is expected there.
3. **Add depicts (P180) statements and captions** in English plus one or two other languages. That is the entire discovery mechanism.
4. **Declare, then propose.** {{connected contributor}} on the talk page of any article you mention, then post the message below. Do not add images yourself on the first pass.
5. **If nobody objects after a week**, adding *one* image to *one* article — Sudarsky, the strongest case — sits inside WP:COI's "uncontroversial edit" allowance; use {{edit COI}} if you'd rather not touch it. If anyone reverts, it is controversial by definition: leave it, thank them, move on. One revert handled gracefully costs nothing; arguing costs your reputation.
6. **Never touch the External links section.** WP:ELNO #11 covers personal sites, and it is the fastest way to be read as a spammer.

Draft for **Wikipedia talk:WikiProject Astronomical objects** (also usable at `Talk:Sudarsky's gas giant classification`):

> **== Offering physics-derived reflected-light colour illustrations (COI disclosure) ==**
>
> Disclosure up front: I built and run the site these come from, so I'm raising it here rather than adding anything myself.
>
> I've uploaded a few CC BY 4.0 files to Commons that compute a planet's visible colour from a geometric-albedo spectrum times a host-star illuminant, integrated against the CIE 1931 2° colour-matching functions. The method and its assumptions (cloud state, metallicity, phase angle, luminance normalisation) are written out on each file description page. These are **modelled, not observed**, and labelled that way.
>
> Two I think may be genuinely useful here:
> * A five-class illustration for [[Sudarsky's gas giant classification]], derived from the Sudarsky et al. (2000, 2003) models the article already cites. It is currently illustrated with Celestia renders, which are artistic rather than computed.
> * A method diagram for [[Geometric albedo]] showing spectrum → colour.
>
> I'm aware a per-planet colour with no published source would be [[WP:OI|unpublished analysis]], so I'm *not* proposing anything of that kind, and no bulk addition. I'd rather someone uninvolved judge whether these two are an improvement. Happy to re-render, re-label or supply SVG at any size — and equally happy to be told no. Links: [file 1], [file 2]. ~~~~

That post gets a reply: it discloses, cites the right policy against its own interest, asks a narrow question, and offers an out.

## Wrong or unverified

- **Wrong:** "a Zenodo DOI makes the colours a citable published source" — WP:PREPRINT names Zenodo.
- **Wrong:** "placing your own images into articles is what the COI guidance asks you not to do" — WP:COI encourages the uploads and permits uncontroversial additions.
- **Wrong:** "core content policies exclude unpublished analysis [therefore images]" — as a blanket claim about images, contradicted by WP:OI.
- **Wrong:** "uploading thousands means a bot flag" — no flag at that scale; the risk is a scope DR.
- **Wrong venue:** "WikiProject Astronomy talk page" → WikiProject Astronomical objects.
- **Overstated:** "hundreds of exoplanet articles have no image" — exoplanet *articles* number in the low hundreds total (WP:NASTRO), and the well-known ones are already illustrated.
- **Unverified:** Commons file-page view/click-through rates. Neither of us has data; the doc's directional claim matches my experience but is asserted, not measured.
- **Unverified:** exact en.wp exoplanet article count — the API rate-limited me. ~411 stubs is solid; the total is an estimate.

## Better approaches, ranked

1. **The four-file version above.** One evening, zero policy exposure, permanent hosting, one plausible placement in a genuinely under-illustrated article. Do this.
2. **Do nothing until a third party writes about the project.** Entirely respectable — every argument for waiting survives my corrections; only the stated reason changes. If evenings are scarce, this beats a half-done version 1.
3. **Fix the Sudarsky article's prose instead of its images.** Classes II and IV have no colour description despite the cited papers containing them. Sourced text, no image, no self-reference: pure contribution, and the only route that ever converts a hobbyist into the kind of author WP:SPS would later accept.
4. **Skip Wikimedia; spend the evening on 06 and 13.** The doc's own conclusion, still fine.
5. **Do not do:** Wikidata colour statements, mass Commons upload, any External-links addition.

## The one thing I'd change

Delete "publish the dataset with a DOI" as the unblocking step. It is the load-bearing claim of the doc and it is false, and it currently makes 06-open-data.md look like a prerequisite for something it cannot unblock. Replace it with the honest gate — **independent published coverage of the colours, or nothing** — and note that the small Commons version needs neither and can happen today.

## What I edited

`docs/marketing/04-wikimedia.md` — rewrote reasons 1–4 against the actual policy text with citations; corrected the COI claim; replaced the DOI flip-condition; corrected the WikiProject venue; changed CC BY-SA to CC BY 4.0 for consistency with 06; promoted "the small version" from optional aside to the recommended play and specified its four files; added the WP:NASTRO addressable-set correction and the no-in-article-link-surface point. **Status** line and **Links** section preserved, with links added.

`docs/marketing/README.md` was **not** edited — its board row still reads `parked`, which remains correct for the campaign. If you want the split verdict reflected there, it is a one-line change to the Note column.

`docs/marketing/06-open-data.md` was **not** edited, but it needs a follow-up: it claims the DOI is "the gate on 04-wikimedia.md" (line 14) and that a citation "unlocks 04-wikimedia.md" (line 85). Both are now contradicted by 04. Its own case for Zenodo stands on the pre-registered-predictions argument and does not need the Wikipedia claim.
