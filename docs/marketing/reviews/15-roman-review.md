# Review — 15 The Roman launch play

*Reviewed by an exoplanet astronomer who has worked direct-imaging/coronagraph science and read the CGI Primer, the tech-demo paper and the calibration plan properly.*

## Verdict

**Ship it, after one factual repair and one framing repair** — the band correction is substantially right and the strategy is sound, but the doc says Band 2 "is not in the flight configuration at all" (the hardware *is* installed) and lists a brown dwarf as a reflected-light colour target, either of which would cost you the audience you are writing to.

## The band-config correction — is it right?

**Yes, on every number that matters.** I pulled the text of the Jan 2025 CPP Primer directly. The mode table is reproduced in the doc verbatim and correctly:

| Band | λ₀ | BW | Mode | Mask | Support | Verdict |
|---|---|---|---|---|---|---|
| 1 | 575 nm | 10% | Narrow FoV Imaging | Hybrid Lyot | Required (Imaging) / Best Effort (Polarimetry) | ✅ verbatim |
| 1 | 575 nm | 10% | Wide FoV Imaging | Shaped Pupil | Best Effort | ✅ verbatim |
| 3 | 730 nm | 15% | Slit + R~50 Prism Spectroscopy | Shaped Pupil | Best Effort | ✅ verbatim |
| 4 | 825 nm | 10% | Wide FoV Imaging | Shaped Pupil | Best Effort | ✅ verbatim |

Source: [Roman Coronagraph Primer, CPP, 8 Jan 2025](https://roman.ipac.caltech.edu/docs/RomanCoronagraphPrimer_Current.pdf), p.5.

The pivotal sentence is quoted accurately, word for word:

> "The only formal performance requirement for the Coronagraph Instrument is to be able to image a point source with a flux ratio of at least 10⁻⁷ at a separation of 6−9 λ/D from a star as faint as V = 5 in a 10% bandpass centered < 600 nm (Band 1). Thus, in order to reach this requirement, only observations in Band 1 with the hybrid Lyot coronagraph are formally supported; all other modes listed in the table below will be supported on a 'best effort' basis."

Item by item against `pipeline/config.py`:

- **`cgi-575` @ 10% — correct, keep.** Matches the Primer and every other source.
- **`cgi-660` @ 6% — remove from the supported set, but the doc's *reason* is wrong.** The doc says 660 nm "is not in the flight configuration at all." It is. The CGI colour filter wheel (CFAM) physically carries `λ1 = 575 nm, 10%; λ2 = 660 nm, 15%; λ3 = 730 nm, 15%; λ4 = 825 nm, 10%`, and the spectrometer holds a second Amici prism for it ([Zellem et al. 2022, CGI Observation Calibration Plan](https://arxiv.org/pdf/2202.05923)). The correct statement is Bailey et al.'s: *"Band 2 spectroscopy hardware will be installed, but will not be tested on the ground; hence, it is not an officially supported observing mode"* ([Bailey et al. 2021, Table 1 note](https://arxiv.org/pdf/2103.01980)). Same code change, defensible sentence. **Fixed in the doc.**
- **`cgi-730` @ 6% — width is wrong, correct it.** It is 15% (Primer). Also note the doc's implication that 6% came from a superseded spec: I could not find "6%" in any primary CGI source. It appears to be an error of ours, not an outdated citation. Say that plainly; it is the more honest disclosure.
- **`cgi-835` @ 15% — wrong on both centre and width; it is 825 nm at 10%.** "835 nm" appears in no primary source I could find. Straight error.
- **"only Band 1 HLC is formally supported" — correct and verbatim.**

**One thing the doc did not catch: the sources disagree on bandwidth by ~2%.** The Primer says Band 3 = 15%, Band 4 = 10%. Bailey et al. 2021 Table 1 gives FWHM 122 nm at 730 nm (16.7%) and 94 nm at 825 nm (11.4%); Zellem et al. 2022 says 17% and 12%. That is nominal filter spec vs as-built FWHM. It is worth far less than 1 ΔE for your purposes — but cite which you used, because a referee-minded reader will check. Added to the doc.

**Net: apply the correction.** Final supported band set for the Roman view: 575/10%, 730/15%, 825/10%. Three bands, not four.

## Where the framing overclaims or undersells

**"Roman's guaranteed output is a single brightness measurement per planet" — a colleague would object, and they would be right twice over.**

*Too generous, in one direction.* The L1 requirement guarantees no per-planet output whatsoever. It is one demonstration, on one "astrophysical point source" between 6 and 9 λ/D — which need not be a planet at all; a known companion used as a test source satisfies it. "Per planet" smuggles in a promise the requirement does not make.

*Too harsh, in the other.* "Best effort" is a programmatic term meaning *not formally required*. It is not a probability estimate. The instrument completed instrument-level testing in Bands 1, 3 and 4; the CPP runs standing working groups on Observation Planning, Polarimetry, and the DRP; and the Primer itself anticipates "optical spectra of up to two of these exoplanets." Writing best-effort as "probably won't happen" is the mirror image of the hype you are correcting, and the people who spent a decade on those modes will read it as a sneer. That costs you the exact relationship the doc's own contact section is trying to build.

**The biggest undersell: polarimetry is absent from the entire document.** Bands 1 and 4 are polarimetry-compatible; there is a dedicated CPP Polarimetry working group and a literature (Anche et al. 2023, 2024). Polarimetry constrains cloud presence and particle size — *directly* the physics that drives your palettes. "Roman may not tell you the colour, but it can tell you whether there are clouds, which is what sets the colour" is a stronger and more surprising story than the one you are currently telling, and nobody in the popular press is telling it.

The rewritten framing I put in the doc keeps the punch and survives review: one formal requirement, one band, one band is not a colour, everything that makes a colour is built-and-planned-and-optional.

**Correct and well-judged:** the "no proprietary period" point (verbatim in the Primer, and genuinely your best strategic asset); the refusal to compete on launch day; and the fallback section, which is the most intellectually honest part of the document.

## Gaps

- **Polarimetry**, as above. Largest single omission.
- **Self-luminous targets are a whole category your model cannot address.** The tech demo explicitly includes "self-luminous and reflected-light planet imaging." β Pic b, HR 8799 e and 51 Eri b appear repeatedly in CGI planning; for those, visible flux is not reflected starlight. If CGI's first planet image is a self-luminous one, your prediction set is silent — plan for that being the *likely* outcome, not the edge case.
- **The contrast→albedo inversion is degenerate, and `docs/roman-measured-data.md` step 2 currently hand-waves it.** CGI publishes a flux ratio. Recovering albedo needs `A·Φ(α) = contrast/(Rp/a)²`, and for RV-discovered targets like 47 UMa b there *is no measured Rp* — only M·sin i. Unknown inclination also means unknown true phase angle at epoch. That runbook will produce a confidently wrong number the day it is used. (Out of scope for my edits; flagging it as the highest-value follow-up in the codebase.)
- **The ΔE2000 headline is not measurable.** CGI can never give you the full-spectrum "true colour" to difference against. Only the reconstructed colour is observable. The doc now says so.
- **No mention of the Roman Research Nexus / ROSES participation routes**, which are the legitimate ways an outsider gets near CGI data.
- **Nothing on what the CPP actually wants from outsiders.** The Primer says the CPP's goals are "tools, target databases, and data reduction software." A physics-derived colour predictor is arguably a *tool*. That is the framing most likely to get a reply — stronger than "correction disclosure."

## Wrong or unverified

- ❌ **"Band 2 at 660 nm is not in the flight configuration at all."** Wrong. Installed, untested, unsupported. Fixed.
- ❌ **"HIP 71618 B" in the prediction target list.** The paper is real ([arXiv:2512.02126](https://arxiv.org/abs/2512.02126)) and does say "suitable for the Roman Coronagraph Technology Demonstration" — but the object is a **~60–65 M_Jup substellar companion, M5–M8, ~2700 K, at ~11 AU**. It is a brown dwarf radiating thermally. A reflected-light albedo colour for it is a category error and would be the most quotable mistake this project could make. Removed.
- ⚠️ **"47 UMa b/c used as *the* target in the Roman Exoplanet Imaging Data Challenge."** Misleading. The Challenge (2019–2021, concluded) simulated *"a fictitious exoplanetary system around the nearby solar-type star 47 UMa."* The star was the setting; the planets were invented. It does not establish the real 47 UMa b/c as a tech-demo target. Corrected, and Girard's role put in the past tense.
- ⚠️ **"Community planning documents assumed a window roughly Jan–Jul 2027 based on an October 2026 launch."** Unverified — I could not source either the window or the assumed launch month. Wolff et al. 2024 says only "expected to launch in late 2026"; the Primer says "Launch: No later than May 2027." Replaced with the one thing that *is* published: 2,200 hours / 3 months, within the first 18 months, no start date.
- ⚠️ **"V ≤ 5" as a hard cut.** The Primer adds "though several magnitudes fainter may be possible." Using it as a wall will under-populate your target set. Corrected.
- ✅ **Verified:** launch 30 Aug 2026, 07:26 EDT, Falcon Heavy, LC-39A ([NASA countdown page](https://science.nasa.gov/mission/roman-space-telescope/roman-launch-countdown/)); ~90-day commissioning → science ops early 2027 ([Planetary Society](https://www.planetary.org/articles/the-nancy-grace-roman-space-telescope-launch-what-to-expect)); "2,200 hours (90 days) within the first 18 months"; "No proprietary period"; V ≤ 5 / <2 mas; `plandb.sioslab.com`; Sanghi et al. 2026 ε Eri b ([arXiv:2602.23423](https://arxiv.org/abs/2602.23423)) — real, and its "metal enrichment and/or water ice clouds" claim is genuinely albedo-testable.
- ✅ **All five CPP contacts verified verbatim in the Primer** (Bailey & Millar-Blanchaer `cpp-co-chairs@jpl.nasa.gov`; Greenbaum `azg@ipac.caltech.edu`; Girard `jgirard@stsci.edu`; Wolff `sgwolff@arizona.edu` — the Primer misspells the surname "Wolf"). Andreoli (Roman Communications Lead) and Balzer (Roman Science Writer) confirmed as current GSFC Roman media contacts.
- ❔ **Unknown, and the doc should keep saying so:** the tech-demo target list. None is published or selected. Also unknown: mode commissioning order, and whether spectroscopy gets used on a planet at all.

## The predictions play — rigorous version

**Do it. It is a good idea, and it is the only thing in this plan that cannot be replicated by someone with a bigger audience.** But the current spec would produce a stunt, because it predicts a *swatch* and CGI measures a *flux ratio*. What I would accept as a pre-registration:

1. **Scope statement, first line.** "Reflected-light mature giant planets only. This model does not apply to self-luminous companions or substellar objects." Without it, the first CGI result — plausibly β Pic b — makes you look like you predicted something you didn't.
2. **Predict the observable.** Primary quantity: **geometric albedo in each flight band (575/10%, 730/15%, 825/10%) at a stated phase angle, with an explicit uncertainty interval.** Not a hex. The hex is a derived presentation layer.
3. **Publish contrast as a curve, not a number.** `contrast = A·Φ(α)·(Rp/a)²` with Rp unknown for RV targets. Give predicted contrast *as a function of assumed radius*, with the assumed radius flagged as a separate labelled input. This is the difference between a scientist nodding and a scientist closing the tab.
4. **Pre-register a naive baseline you claim to beat** — a grey Lambertian sphere at fixed albedo, say. **This is the single most important item.** "Our model was within 30%" is meaningless without knowing that guessing grey was within 40%. No baseline, no falsifiability, no science.
5. **Pre-register the decision rules**, in advance and in writing: what counts as a target match (including alias handling — `HD 95128 b` = `47 UMa b`); which phase angle you adopt if the paper quotes one; what you do if only one band is measured; and the explicit pass/fail criterion ("success = measured band albedo within our stated 1σ interval").
6. **State the untestable part.** The full-spectrum colour and therefore the ΔE2000 can never be measured. Only the reconstructed colour can. Say it above the fold, not in a footnote.
7. **Freeze everything.** Zenodo DOI over code version + input data + prediction table, not just the web page. The git tag is nice; the DOI is what makes it citable. The doc's read on arXiv endorsement is correct — don't block on it.

Do that and it is a defensible pre-registration. Skip 4 and it is a horoscope with a DOI.

## Better approaches

Ranked by value to the project per evening.

1. **Ship the band correction with a public, dated changelog.** Highest value, half an evening, blocks everything else. "We found our own error against the CPP Primer" is the single most credibility-positive thing on the roadmap.
2. **Reframe the pitch around the information budget, not the deficit.** "One band is not a colour — here is what the second and third buy you" beats "Roman only gives you one number." Same facts, and the second version makes CGI people your allies instead of your subjects.
3. **Add polarimetry to the explainer.** Genuinely novel in public writing, directly connected to your physics, and it turns an "and it can't do much" story into an "and here's the surprising thing it *can* do" story.
4. **Reposition the outreach as a tool offer, not a correction disclosure.** The CPP's published remit is tools and target databases. "I built a reflected-light colour predictor over the CPP target list; would it be useful, and is my band model right?" outperforms a mea culpa, and still discloses the error.
5. **Pre-register the *method* and the pipeline, weighted above the target list.** Since no target list exists, the durable asset is "any target CGI picks, computed in an hour, against a frozen model." That survives every target-selection outcome.
6. **Fix the contrast→albedo path in `docs/roman-measured-data.md` before it is ever used.** Currently the fastest route to a confidently wrong headline number.
7. *(Lower)* The `/roman/status` page and the "Band 1 only" toggle. Both good; neither is load-bearing.

## The one thing I'd change

**Predict band albedos with uncertainties and a pre-registered baseline, not hex codes.** The hex is what makes the site lovely and it is the right thing to *show* — but it is not what Roman measures, and a prediction set denominated in swatches cannot be scored against a flux ratio. Keep the swatch as the presentation; make the albedo the claim. That one change turns the most pitchable thing this project will ever publish from a nice gesture into something a CGI team member could actually cite.

## What I edited

In `docs/marketing/15-roman-launch.md` — structure, `**Status:**` line and `## Links` section untouched:

- **"The bet"**: qualified the three-bandpass claim with "only one of which is a formal requirement".
- **Timeline table**: replaced the unverified Jan–Jul 2027 / October-2026-launch row with the verbatim published statement (2,200 h / 3 months / within first 18 months), plus the note that the Primer itself still says "Launch: No later than May 2027", so all planning docs predate the real date.
- **Band-correction section**: corrected the Band 2 claim to "not a supported observing mode" with the CFAM filter-wheel contents and the Bailey et al. ground-testing quote; noted 835 nm and 6% trace to no primary source; added the nominal-vs-as-built bandwidth spread across Primer / Bailey 2021 / Zellem 2022; added the verbatim L1 requirement and the observation that it does not promise a planet; rewrote the headline framing; added the explicit warning against reading "best effort" as "unlikely".
- **Predictions section**: stated that no target list is published; softened V ≤ 5 per the Primer's own caveat; **removed HIP 71618 B** with an explanation of why (brown dwarf); added the reflected-light-only scope requirement and named the self-luminous targets it excludes; restructured "what to predict" to lead with band albedos, then the radius-dependent contrast curve, then colours; flagged the ΔE2000 as model-vs-model and unmeasurable; added the pre-registered naive baseline.
- **Email draft**: corrected so it no longer asserts 660 nm is absent from the instrument.
- **Contacts**: Girard's Data Challenge role to past tense with the "fictitious system around 47 UMa" clarification; noted the Primer's "Wolf"/"Wolff" spelling.

No code touched. `pipeline/config.py` is the author's to change: drop `cgi-660`, set `cgi-730` to 15%, replace `cgi-835` @ 15% with `cgi-825` @ 10%.
