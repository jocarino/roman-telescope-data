# Review — 13 Credit the scientists

*Reviewed by a research-software citation and ethics specialist — software-citation principles, CC licensing, and academic cold-contact practice.*

## Verdict

**Revise.** The audit is unusually honest and mostly correct — better than most formal ones I see — but it misses one redistributed dataset entirely, understates two licence breaches, gets one "gap" backwards, and its one *unverified* row turns out to hide a factual error in the site's signature feature that dwarfs every attribution question in the document.

## Audit of the audit

I re-derived the table from the code before comparing. Line references in the doc were checked one by one and are accurate.

**Right, and verified:**

- NASA Exoplanet Archive acknowledgement genuinely absent. `grep -ri "California Institute of Technology"` over the whole repo returns **zero** hits; so do "Christiansen" and "Akeson". Confirmed.
- Karkoschka and Payne are behind a toggle that is collapsed by default — `how.html:9-14` defines `maths_open()` as `x-data="{ m: false }"`. Confirmed literally.
- `data/cahoy_grid/` holds 305 files with **no** README, licence note or manifest of provenance. The only Cahoy reference in the repo is the docstring at `cahoy_ingest.py:11`. Confirmed.
- The `/roman` provenance block (`roman.html:198-205`) really is the best attribution in the codebase — title, authors, journal, link, and a verbatim quoted count. It is a fair model.
- Images (`pipeline/observations.py`) and maps (`web/textures.py`) carry `credit` / `license` / `source_url` on every record and render them in the lightbox. Exemplary is the right word.
- Thorngren 2016 is genuinely invisible: one docstring line, `pipeline/spectrum/parametric.py:20`. Kopparapu is named on site but with no venue. Both confirmed.
- No `LICENSE`, no `CITATION.cff`, no data-sources section. Confirmed.

**Wrong:**

- **"Not on the four planet pages it powers"** (Karkoschka row) is false. `macros.html:1042` maps `karkoschka1998` → "measured full-disk spectrophotometry (Karkoschka 1998, ESO)" and `payne2026` → "the measured solar-system reference spectrum (Payne et al. 2026)" in the data card of every anchor page. Author and year are on-page; venue and link are not. Corrected in the doc.
- **"no version recorded"** for PICASO is false in the repo: `docs/picaso-runbook.md:55` records **PICASO 4.0.1** and opacity DB Zenodo 14861730. True only of the *emitted data*. The doc's guess of "v3.3" in the citations list was wrong and is now removed.
- **Silkscreen: "OFL doesn't strictly require it"** is wrong. OFL 1.1 condition 2 is explicit: fonts may be bundled with software "provided that each copy contains the above copyright notice and this license". `web/static/fonts/*.woff2` are served with no notice and the repo does not contain the OFL text at all — only a link to it.
- **Payne's lead author is Allison Payne**, not "Amber Payne" as the contact table had it. Verified from Zenodo 17470005 (Payne project leader; Villanueva supervisor; Kofman, Fauchez, Faggi, Mandell, Roberge, Alei).

**Missed entirely:**

- **CDS catalogue VI/42 — IAU constellation boundaries.** `pipeline/data/constellation_boundaries.dat` is a *verbatim redistributed copy* fetched from `cdsarc.cds.unistra.fr`, and it powers the "Where in the sky" panel on ~5,700 pages. Credited in the file header and `pipeline/sky.py:3-4` — nowhere a visitor can see. CDS has a published acknowledgement request and asks that original authors be explicitly cited. This is the same class of omission as the Archive one and the audit did not see it.
- **Roman (1987), *PASP* 99, 695** and **Meeus, *Astronomical Algorithms*** — the algorithms behind the sky panel, docstring-only.
- **The project's own output licence.** Not stated anywhere: no `LICENSE`, nothing in `README.md`, nothing on the site. Meanwhile [02-press-kit](../02-press-kit.md) recommends CC BY 4.0 on the renders, [04-wikimedia](../04-wikimedia.md) plans a Commons upload under CC BY-SA, [05-machine-readable](../05-machine-readable.md) says to "state the CC BY licence" in `llms.txt`, and [06-open-data](../06-open-data.md) commits to CC BY 4.0 on the dataset. Four downstream items are blocked on a line that does not exist. An audit that flags what we owe upstream but not what we grant downstream is half an audit.
- **Alpine.js is worse than "needs a notice"**: the vendored bundle contains no copyright header whatsoever (grep finds only the string `alpinejs`). The notice was stripped, not merely omitted from a credits page.
- **The dark-hole geometry** (150–450 mas, 1e-7 contrast) in `data/roman-targets.json` is uncited, same as the bandpasses.
- **NASA NSSDC planetary fact sheets** are linked on anchor pages (`macros.html:1051`) — an existing credit the table didn't list. Public domain, no obligation, but the table claimed to be complete.
- Dependency licences (numpy, scipy, pydantic, jinja2, pillow) are unexamined. All permissive; no redistribution of code; no action needed — but say so rather than leave it silent.
- `README.md` and `CLAUDE.md` both still claim the site uses **htmx**. It does not — there is no htmx anywhere in `web/`. Minor, but it is the kind of thing a scientist who opens the repo notices.

## Obligations, verified

Actual obligations (a term of a licence, or a stated requirement of the provider):

1. **NASA Exoplanet Archive** — [acknowledgement page](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html), verbatim: *"This research has made use of the NASA Exoplanet Archive, which is operated by the California Institute of Technology, under contract with the National Aeronautics and Space Administration under the Exoplanet Exploration Program."* Preferred citation **Christiansen et al. (2025)**, *PSJ*, doi:10.3847/PSJ/ade3c2, superseding Akeson et al. 2013. The doc quoted this correctly. Strictly a *request*, not a licence term — but it is the single most conspicuous omission to the audience being emailed.
2. **Payne et al. — CC BY 4.0**, confirmed on [Zenodo 17470005](https://zenodo.org/records/17470005) as "Creative Commons Attribution 4.0 International". [§3(a)(1)](https://creativecommons.org/licenses/by/4.0/legalcode.en) requires retaining *"identification of the creator(s)"*, *"a copyright notice"*, *"a notice that refers to this Public License"*, *"a notice that refers to the disclaimer of warranties"*, and *"a URI or hyperlink to the Licensed Material to the extent reasonably practicable"*. A **binding licence term**. The site gives name and licence label only.
3. **Alpine.js — MIT**: *"The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."* Copyright line: *"Copyright © 2019-2025 Caleb Porzio and contributors"*. **Binding**, and currently breached.
4. **Silkscreen — SIL OFL 1.1**, condition 2: *"Original or Modified Versions of the Font Software may be bundled, redistributed and/or sold with any software, provided that each copy contains the above copyright notice and this license."* **Binding**, currently breached.
5. **Solar System Scope maps — CC BY 4.0.** Already credited on-page (`web/textures.py`, `macros.html:243`). Compliant, and it also means CC-BY-licensed renders downstream must carry that credit forward.

Courtesies (strongly expected, not enforceable):

6. **PICASO** — its [What to Cite](https://natashabatalha.github.io/picaso/credit.html) page asks, for reflected light: *"Batalha, Natasha E., et al. 'Exoplanet reflected-light spectroscopy with PICASO.' The Astrophysical Journal 878.1 (2019): 70."* No Zenodo DOI or licence is stated on that page.
7. **`colour-science`** — BSD-3-Clause, *"Copyright 2013 Colour Developers – colour-developers@colour-science.org"*; cite via Zenodo **10.5281/zenodo.17837391**. We import rather than redistribute, so no notice obligation.
8. **CDS / VizieR** — requested wording: *"This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France (DOI : 10.26093/cds/vizier). The original description of the VizieR service was published in 2000, A&AS 143, 23"*, plus *"the original authors and publication references including the publisher have to be explicitely cited"*.
9. **Cahoy 2010** and **Karkoschka 1998** — public/model data, no licence hook. Pure courtesy, and the whole point of the project.

## Gaps

- No `LICENSE`, no `CITATION.cff`, no output licence — see above. This is the load-bearing gap.
- The doc plans `data/credits.json` but doesn't say who owns keeping it true. Attribution files rot. Tie it to a test: assert every `provenance` / `spectrum_source` value emitted by the pipeline has a matching entry, so a new engine cannot ship uncredited.
- No "how to cite this site" — asymmetric. You are about to ask ten scientists to care about citation while offering them no way to cite you back.
- The CC BY chain is unexamined: Payne (CC BY) → our spectra → our hexes → a CC BY dataset. Attribution has to travel with it. Say so in `06-open-data`.
- Nothing addresses the AI-scraping angle that `05-machine-readable` invites, where an attribution-required dataset is exactly what gets stripped.

## Wrong or unverified

The most serious finding in this review is not an attribution problem.

**The Roman bandpasses are wrong.** `pipeline/config.py:74-80` ships 575 nm/10%, 660 nm/6%, 730 nm/6%, 835 nm/15%. The published CGI bands are **575 nm/10%** (Band 1), **660 nm/17%** (Band 2), **730 nm/17%** (Band 3), and **825 nm/11%** (Band 4) — corroborated across [Roman @ IPAC](https://roman.ipac.caltech.edu/page/cgi), the [CGI reference information (Jan 2025)](https://roman.gsfc.nasa.gov/science/docs/Roman-CGI-Reference-Info-January2025.pdf) and the instrument literature (band 4F: 825 nm centre, 94 nm FWHM; 3F: 730 nm, 122 nm FWHM; 1F: 575 nm, 58 nm FWHM). The spectroscopic mode is quoted as R≃50 over 15–17% bandpasses, never 6%.

So: one band centre off by 10 nm, and two bandwidths off by roughly 3×. Every "as Roman would see it" swatch on the site is reconstructed from the wrong filter set, and the whole editorial claim of the feature — *how much colour identity survives Roman's filters* — is quantitatively wrong in the direction that makes the loss look worse than it is. The doc flagged this row *"Unverified"* and scheduled the check for Week 1. That was the right instinct and the wrong priority: it belongs before the credits page, not after.

Also unverified and worth not asserting: whether the committed Cahoy CSVs match the current IPAC distribution; whether the `.npz` files were produced by 4.0.1 or an earlier build (the runbook is prose, not provenance).

## Better approaches

Ranked, most to least valuable.

1. **Fix the bandpasses, then build the credits page.** Reversing the doc's order. Credit that decorates a wrong number is worse than no credit: it tells the instrument team you cited them *and* misrepresented their instrument. This is one afternoon in `config.py` plus a re-emit.
2. **Ship the two licence notices and a `LICENSE` in the same commit as the fix.** `OFL.txt` beside the woff2, the Alpine MIT header restored, a licence for your own code and a separate explicit line for the data and renders. Ten minutes, clears three breaches, and unblocks four other marketing items.
3. **Make the credits page a `CITATION.cff` and a machine-readable `credits.json` first, HTML second.** Scientists check `CITATION.cff`; it is the file that signals you know the norms. Rendering the same data as a page is then free, and `05-machine-readable` gets its source of truth for nothing.
4. **Replace the first email with a GitHub issue.** For `colour-science` and PICASO, open an issue titled "Showing colour-science computing sRGB for 5,700 exoplanets — sanity check on one convention?" It is public, permanent, indexed, costs the maintainer nothing to ignore, and if they answer, the exchange becomes a citable artefact. Mansencal in particular responds in the open. Email a maintainer only after an issue goes unanswered.
5. **Post before you write.** Bluesky's astronomy community is where Fortney, Batalha and Christiansen actually are. A post that tags nobody and says "the phase slider on this site is Cahoy et al. 2010's grid doing all the work" gets found by the authors without an inbox ask, and a public "that's neat" is worth more than a private reply. Then the email has a hook: *"you may have seen this."*
6. **Use the Archive helpdesk exactly as the doc says** — that row is right and should not change.
7. **DPS/AAS over cold email for the model authors.** A poster or a lightning talk puts you in a room with Marley and Fortney with no address-guessing. Slower, far higher conversion.
8. **Emails last**, and fewer of them. Three, not thirteen.

**On the drafts as written:** (b) is the strongest — specific, technically checkable, asks one answerable question, and the `illuminant=None` detail proves you read the library. I would reply to it. (a) is good but "I'd genuinely like to know if I've misused it anywhere" spans two questions; cut to the phase interpolation alone. (c) is the one that gets deleted — a communications lead receives fifty "please feature my project" emails a week and "if it's useful for launch-window outreach, please use it" is that email with better manners. Rewrite it as an offer of a specific asset on a specific date, or send it to Vanessa Bailey as a technical correction request instead, where the bandpass question makes it genuinely useful to the recipient.

## The one thing I'd change

Move the Roman bandpass fix out of the audit and to the top of the plan, before the credits page and before any email. The document's own editorial standard is honesty about model versus measurement; a signature feature built on the wrong filter set fails that standard more badly than any missing citation in the table, and it is the one error the people you most want to email are certain to catch.

## What I edited

In `13-credit-the-scientists.md`, preserving structure, `**Status:**` and `## Links`:

- Rewrote the CGI bandpass row from "unverified" to a verified factual error, with the correct band centres and widths.
- Added four audit rows: CDS catalogue VI/42 (missed entirely), the uncited dark-hole geometry, and the NSSDC fact-sheet link (an existing credit the table omitted).
- Corrected the Karkoschka/Payne "not on the planet pages" claim — they are, via `macros.html:1042`.
- Corrected the PICASO version claim (4.0.1, recorded in the runbook; removed the wrong v3.3 guess) and pointed item 2 at PICASO's own What-to-Cite page.
- Strengthened the Alpine row to a verified MIT breach with the exact copyright line, and corrected the Silkscreen row — OFL 1.1 condition 2 does require the notice.
- Added the CC BY 4.0 §3(a)(1) requirements verbatim and CDS/VizieR as citation item 8.
- Fixed "Amber Payne" → **Allison Payne** and recorded the verified author list.
- Added the missing output-licence gap to the repo-licensing row, naming the four docs blocked on it.
- Updated the risk bullet from one breach to three, and added a "Week 0" step for the bandpass fix.
