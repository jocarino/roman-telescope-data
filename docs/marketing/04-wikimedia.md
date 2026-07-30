# Wikimedia Commons — the honest verdict

**Status:** **parked** (the mass campaign) · **small version: do it** · **Effort:** one evening · **Payoff:** low as traffic, real as reach · **Hub:** [Marketing plan](./README.md)

You asked how worth this actually is. Short answer: **the campaign is worth less than it looks;
the small version is worth more than this doc originally said, and it is unblocked today.**
An earlier draft of this page parked everything behind a Zenodo DOI. That was a policy
misreading — corrected below, with the actual guideline pages.

## Why it looked good

Exoplanet articles on Wikipedia often have no image, or use a NASA artist's impression. Those
articles get steady traffic forever. An image placed there is permanent, algorithm-proof
referral, and uploading is free. On paper it's the best-value idea in the whole plan.

## Why the mass version isn't

**1. Original research is the right objection, but only for the per-planet swatches.** Commons
has *no* no-original-research rule at all — the only gate is
[Commons:Project scope](https://commons.wikimedia.org/wiki/Commons:Project_scope): "realistically
useful for an educational purpose". And on Wikipedia,
[WP:NOR § Original images](https://en.wikipedia.org/wiki/Wikipedia:No_original_research#Original_images)
(WP:OI) says: *"Original images created by a Wikimedian are not considered original research, so
long as they, or their captions, do not illustrate or introduce unpublished ideas or arguments."*
So the block is not "we made it" — it is *the claim the image makes*. A swatch for a planet
nobody has published a colour for is an unpublished argument, and is blocked permanently by this
route. An illustration of a **published** result (HD 189733 b's measured blue; the Sudarsky
classes) or a **method diagram** is not, and is admissible today.

**2. Placing our own images is not forbidden — it is a disclosure obligation.**
[WP:COI § Supplying photographs and media files](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest#Supplying_photographs_and_media_files)
*encourages* COI editors to upload media, and says the addition to an article "may be an
uncontroversial edit that editors with a COI can make directly… If the addition of an image is
challenged by another editor, it is controversial." COI is a guideline; the policy —
[WP:PAID](https://en.wikipedia.org/wiki/Wikipedia:Paid-contribution_disclosure) — doesn't apply
to an unpaid hobby project. What *is* a real problem is scale: doing it across hundreds of
articles is [WP:SELFCITE](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest#Citing_yourself)
/ WP:REFSPAM territory, and reads as a promotion campaign. So: declare, propose, don't bulk-add.

**3. There is no traffic here at all — by policy, permanently.** Not merely "small". A caption
can't carry an external link ([WP:ELPOINTS](https://en.wikipedia.org/wiki/Wikipedia:External_links#Important_points_to_remember):
"with rare exceptions, external links should not be used in the body of an article") and the
image can't carry a watermark or credit line
([WP:IUP](https://en.wikipedia.org/wiki/Wikipedia:Image_use_policy)). Attribution lives on the
file description page and nowhere else. Treat this as reach and credibility, never as referral.

**4. The addressable set is a few hundred articles, not 5,700.**
[WP:NASTRO](https://en.wikipedia.org/wiki/Wikipedia:Notability_(astronomical_objects)) says
individual exoplanets are not automatically notable — most exist only as rows in list articles.
`Category:Exoplanet stubs` is ~411 pages. Mass upload has nowhere to go even if it were allowed.

**5. Mass uploads risk deletion, not bureaucracy.** No bot flag is needed at these volumes
(ordinary accounts run ~380 uploads/72 min; the convention is a proposal subpage at
[Commons:Batch uploading](https://commons.wikimedia.org/wiki/Commons:Batch_uploading)). The real
hazard is thousands of near-identical generated discs being nominated as out-of-scope
"self-created artwork without obvious educational use".

**Net:** the *campaign* stays parked — [09-show-hn.md](./09-show-hn.md),
[13-credit-the-scientists.md](./13-credit-the-scientists.md) and
[03-seo-planet-pages.md](./03-seo-planet-pages.md) all beat it comfortably. The *small version*
below does not need to wait for anything.

## What would flip the mass version

**Not a DOI.** [WP:RS § Preprints](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources#Preprints)
names Zenodo alongside arXiv and bioRxiv: "these materials are seldom reliable sources". A DOI is
a resolver handle, not an editorial process, and a self-deposited dataset is a textbook
[self-published source](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources#Self-published_sources).
Do [06-open-data.md](./06-open-data.md) for its own reasons — citability, the timestamped Roman
predictions — but it unblocks nothing here.

The only real gate is **independent published coverage of the colours**: a science outlet, an AAS
Nova write-up, a scientist's blog, or best of all a peer-reviewed paper. See
[13-credit-the-scientists.md](./13-credit-the-scientists.md) and
[15-roman-launch.md](./15-roman-launch.md). Even then, whether a modelled colour belongs in a
given article is an editorial judgement, not a right.

## The small version — do this, it's unblocked now

One evening, zero policy exposure:

1. **Three or four files, not thousands**, under **CC BY 4.0** (matching
   [06-open-data.md](./06-open-data.md); share-alike only adds friction for the educators in
   [14-educators.md](./14-educators.md)): the method diagram (albedo × stellar spectrum → CIE →
   sRGB); a five-panel [Sudarsky class](https://en.wikipedia.org/wiki/Sudarsky%27s_gas_giant_classification)
   illustration; an HD 189733 b swatch flagged as consistent with the published measurement;
   optionally the catalogue hue-distribution plot. SVG where possible. No watermark, no URL in
   the pixels.
2. **File descriptions written like a methods section** — assumptions (cloud state, metallicity,
   phase angle, luminance normalisation), the sources, and *"modelled, not photographed"*.
3. **Add depicts (P180) statements and captions.** [Commons discovery runs on structured
   data](https://commons.wikimedia.org/wiki/Commons:Depicts) via MediaSearch, not categories.
4. **Declare and propose, don't place.** {{connected contributor}} on the talk page, then a post
   at **[Wikipedia talk:WikiProject Astronomical objects](https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Astronomical_objects)**
   — that is the right venue for exoplanet articles, not WikiProject Astronomy. Disclose the COI
   in the first line, name WP:OI against your own interest, offer the two admissible files, and
   let uninvolved editors decide. Draft wording in
   [reviews/04-wikimedia-review.md](./reviews/04-wikimedia-review.md).
5. **Never add anything to an External links section.** WP:ELNO #11 covers personal sites.

Best single target: **Sudarsky's gas giant classification** — an article about modelled exoplanet
colours from published theory, currently illustrated with renders from the *Celestia* hobbyist
simulator. A physics-derived version sourced to Sudarsky et al. 2000/2003 is a straight upgrade.

**Wikidata: don't.** A P465 colour statement sourced to our own site is the same self-published
problem with less editorial friction to catch it — more COI hazard, not less.

## How we'll know it worked

For the small version: whether anyone else uses the files. Once a file is used on any Wikimedia
project it is automatically in scope (COM:INUSE) and effectively permanent — that single event is
the whole measure. For the campaign: article placements that *someone else* made. Don't
instrument Commons file-page views; there is no traffic to measure (see 3).

## Risks

- Being seen as a self-promoter in a community with long memories, at a stage where our
  credibility is the whole asset. Mitigated almost entirely by declaring first and proposing
  rather than placing.
- A mass upload being nominated for deletion as out-of-scope — the reason the campaign stays
  parked.
- Sinking evenings into process rather than the channels that actually move.

## Links

- [README.md](./README.md) — the hub
- [reviews/04-wikimedia-review.md](./reviews/04-wikimedia-review.md) — the policy review this page was corrected against, with draft talk-page wording
- [06-open-data.md](./06-open-data.md) — worth doing, but it does **not** unblock this (WP:PREPRINT names Zenodo)
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the third-party coverage that is the actual gate
- [14-educators.md](./14-educators.md) — the CC-licensed images help here regardless
- [03-seo-planet-pages.md](./03-seo-planet-pages.md) — a better use of the same evenings
