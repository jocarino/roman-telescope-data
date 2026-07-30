# Credit the scientists (then email them)

**Status:** not started · **Effort:** M (1 build weekend + 1 evening of email) · **Payoff:** highest in the plan, and the only item with a legal/ethical obligation attached · **Hub:** [Marketing plan](./README.md)

## The bet

Every colour on this site is somebody's life's work run through a colour-matching matrix. One
scientist posting "someone turned our albedo grid into a design palette" reaches more of the
right people than a month of Reddit, because it arrives with their credibility attached and it
lands in front of the mission teams, the conference organisers and the educators at once. But we
cannot send that email yet: the site names its sources in prose and buries the two real citations
behind a collapsed toggle, and it is missing acknowledgements we actually owe. Build the credits
page first, then the email writes itself — "here is where you're credited, tell me if I got it
wrong" is a message a busy scientist answers.

## Attribution audit

Read from the code on 2026-07-30. "On site" = a visitor can see it without reading the repo.

| Input | What it actually does here | On site today? | Where | Gap |
|---|---|---|---|---|
| **NASA Exoplanet Archive** (`pscomppars` via TAP) | Every planet and star number for ~5,700 planets | Partial | Named + linked in `web/templates/gallery.html:47`, `how.html:393`, glossary term `nasa-exoplanet-archive` | **No required acknowledgement sentence anywhere in the repo** (grep for "California Institute of Technology" → zero hits). No Christiansen et al. 2025 citation. |
| **Cahoy, Marley & Fortney 2010** albedo grid | A spectrum engine (`pipeline/spectrum/cahoy_grid.py`), the phase-angle colour/dimming model (`pipeline/spectrum/phase.py`), and the reference points in Model Space (`pipeline/modelspace.py`) | Named only | `how.html:107`, glossary `cahoy-grid`, `macros.html:391` | No journal, no DOI, no link. Full ref exists **only in a Python docstring** (`pipeline/spectrum/cahoy_ingest.py:11`). The grid is redistributed in `data/cahoy_grid/` (760+ CSVs) with no licence note. |
| **PICASO** (Batalha et al.) | Spectrum engine for selected targets; 7 precomputed spectra committed in `data/picaso_spectra/`, a `provenance` value users can see | Named only | `how.html:111`, glossary `picaso`, `pyproject.toml` extra | **PICASO asks to be cited; we don't.** No Batalha et al. 2019 ref, no Zenodo software DOI. Version *is* recorded, but only in prose: `docs/picaso-runbook.md:55` says **PICASO 4.0.1**, opacity DB Zenodo 14861730. Not in the emitted data. |
| **`colour-science`** (CIE 1931 2° CMFs, XYZ→sRGB) | `pipeline/colour/cie.py` — literally every hex on the site (`MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]`, `sd_to_XYZ`, `XYZ_to_sRGB`) | One passing mention | `how.html:314`, inside a collapsed block | No link, no author, no version, no BSD-3-Clause note. The underlying CIE dataset is explained in the glossary but not credited as a dataset. |
| **Karkoschka (1998)**, *Icarus* 133, 134–146 | The measured spectra behind Jupiter, Saturn, Uranus, Neptune — the pipeline's calibration anchors | Yes, properly | `how.html:214` (journal, volume, pages, instrument, PDS provenance, public domain) | Behind the collapsed "The actual calculations" toggle. No link, no DOI. **Correction:** it *is* on the planet pages it powers — `macros.html:1042` renders the spectrum source as "measured full-disk spectrophotometry (Karkoschka 1998, ESO)". Author + year, no venue or link. |
| **Payne et al. (2026)**, *PSJ* | Earth's measured composite albedo spectrum | Yes, properly | `how.html:220` (journal, what it composites, CC BY 4.0); also named on Earth's page (`macros.html:1042`) | Same burial. DOI `10.3847/PSJ/ae2feb` and Zenodo record 17470005 exist **only** in `data/measured_albedo/README.md`. CC BY 4.0 §3(a)(1) wants creator + copyright notice + licence notice + a URI to the material; we give the name and the licence label, and no link to either. |
| **Carrión-González et al. (2021)**, *A&A* 651, A7 | The Roman target board's eligible-planet list (Table 4) | Yes, best in the repo | `roman.html:201-205` + `data/roman-targets.json` — title, authors, journal, arXiv link, quoted counts | This is the model to copy everywhere else. |
| **Kopparapu et al. (2014)**, ApJ 787, L29 | Habitable-zone edges (`pipeline/habitable.py`, Table 1 coefficients) | Named only | `macros.html:1152,1171` | No journal/DOI on site (it's in the Python docstring). |
| **Thorngren et al. (2016)** mass–metallicity | Sets metallicity for the parametric engine (most planets on the site) | **No** | `pipeline/spectrum/parametric.py:20` docstring only | Invisible to visitors. |
| **Roman CGI bandpasses** (575/660/730/835 nm) | The entire signature feature | **No source cited** | Hard-coded in `pipeline/config.py:74-80` | **Not an attribution gap — a factual error.** Verified 2026-07-30: the published CGI bands are 575 nm/10% (Band 1, imaging+pol), 660 nm/**17%** (Band 2, spectroscopy), 730 nm/**17%** (Band 3, spectroscopy), **825 nm/11%** (Band 4, wide-field imaging). We ship 835 nm/15% and 6% spectroscopic widths. Fix the numbers *before* citing anything. |
| **CGI dark hole** (150–450 mas, 1e-7 raw contrast) | The `/roman` board's geometry copy | Uncited | `data/roman-targets.json` → `instrument` | Same class as the bandpasses: real instrument numbers with no reference attached. |
| **IAU constellation boundaries** (CDS catalogue VI/42; Roman N.G. 1987, *PASP* 99, 695) | Every "Where in the sky" panel — the constellation each host star sits in | **No** | Verbatim copy in `pipeline/data/constellation_boundaries.dat`; credited in that file's header and `pipeline/sky.py:3-4` only | **Missed by the first pass.** We redistribute a CDS catalogue. CDS asks for a specific acknowledgement and that "the original authors and publication references including the publisher have to be explicitely cited". Neither the catalogue, the CDS service nor Roman (1987) appears on the site. |
| **NASA planetary fact sheets** (NSSDC) | Orbit/size data for the five solar-system anchors | **Yes** | Linked from the anchor data card, `macros.html:1051` | None. Public domain. Listed here only so the audit is complete. |
| **Roman @ IPAC** hosting the Cahoy grid | `roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz` | **No** | `pipeline/spectrum/cahoy_ingest.py:9` | The people who host the data we ship get nothing. |
| **PICASO opacity DB** (Zenodo 14861730) | Needed to regenerate the committed PICASO spectra | **No** | `docs/picaso-runbook.md:64` | Zenodo record has its own citation. |
| **Telescope images** (JWST/STScI, ESO/SPHERE, ESO/J. Rameau, NAOJ, NASA/JPL/SSI, Apollo 17) | Planet-page "Telescope" hero | **Yes — exemplary** | `pipeline/observations.py`; rendered with credit + licence + source link in `macros.html:275-287` | None. This is already right. |
| **Surface maps** (NASA Earth Observatory — Reto Stöckli, Robert Simmon; Solar System Scope, CC BY 4.0) | The five anchors' real-map render | **Yes — exemplary** | `web/textures.py`; credit + licence shown in `macros.html:243` | None. |
| **Silkscreen** font (Jason Kottke, SIL OFL 1.1) | Site typeface + OG cards | Repo only, and only the build-time TTFs | `web/assets/fonts/README.md` names the licence but does **not** ship the OFL text; the served `web/static/fonts/*.woff2` have no notice at all | Stronger than first stated: OFL 1.1 condition 2 permits bundling "provided that each copy contains the above copyright notice and this license". Add `OFL.txt` beside the woff2 and credit the face. |
| **Alpine.js** (`web/static/vendor/alpine.min.js`) | All site interactivity, vendored and served | **No** | — | **Verified breach.** The minified bundle carries *no* copyright header — grep finds only the string `alpinejs`. MIT: "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." Notice needed: `Copyright © 2019-2025 Caleb Porzio and contributors`. Version still not recorded anywhere. |
| **Repo licensing** | — | — | — | **No `LICENSE` file, no `CITATION.cff`, no data-sources section in `README.md`.** And **the project's own output has no stated licence anywhere** — while [02](./02-press-kit.md), [04](./04-wikimedia.md), [05](./05-machine-readable.md) and [06](./06-open-data.md) all already promise CC BY / CC BY-SA on the renders and the dataset. Nothing they describe can ship until this line exists. |

**Headline:** images and maps are credited beautifully; the *science* is credited in prose. The
two genuine citations (Karkoschka, Payne) are hidden behind a "The actual calculations" toggle
that is collapsed by default. There is no single page a scientist can be linked to.

## Required citations we owe

Not nice-to-haves. These are asked for by the source.

1. **NASA Exoplanet Archive** — verbatim, from
   [their acknowledgement page](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html):
   > "This research has made use of the NASA Exoplanet Archive, which is operated by the
   > California Institute of Technology, under contract with the National Aeronautics and Space
   > Administration under the Exoplanet Exploration Program."

   Plus the preferred reference, which now supersedes Akeson et al. 2013:
   **Christiansen, J. L., et al. (2025)**, "The NASA Exoplanet Archive and Exoplanet Follow-up
   Observing Program: Data, Tools, and Usage", *PSJ* 6, 186, doi:10.3847/PSJ/ade3c2
   ([arXiv:2506.03299](https://arxiv.org/abs/2506.03299)).
2. **PICASO** — verified against PICASO's own
   [What to Cite](https://natashabatalha.github.io/picaso/credit.html) page, which for
   reflected light asks for **Batalha, N. E., et al. (2019)**, "Exoplanet reflected-light
   spectroscopy with PICASO", *ApJ* 878, 70, doi:10.3847/1538-4357/ab1b51. The version that
   produced the committed `.npz` files is **4.0.1** (`docs/picaso-runbook.md:55`), so the
   PICASO 4.0 paper (Mang et al.) applies to the code and the opacity DB (Zenodo 14861730)
   carries its own citation. Record the version in the emitted data.
3. **Cahoy, K. L., Marley, M. S., & Fortney, J. J. (2010)**, "Exoplanet Albedo Spectra and Colors
   as a Function of Planet Phase, Separation, and Metallicity", *ApJ* 724, 189,
   doi:10.1088/0004-637X/724/1/189. We redistribute the grid; cite it and state the hosting
   source (Roman @ IPAC).
4. **Payne et al. (2026)** — Zenodo 17470005 is confirmed **"Creative Commons Attribution 4.0
   International"**. §3(a)(1) asks us to retain identification of the creators, a copyright
   notice, a notice referring to the licence and to the warranty disclaimer, and "a URI or
   hyperlink to the Licensed Material to the extent reasonably practicable" — satisfiable
   with one link to a page carrying all of it. Lead author is **Allison Payne** (with
   Villanueva, Kofman, Fauchez, Faggi, Mandell, Roberge, Alei). doi:10.3847/PSJ/ae2feb.
5. **Karkoschka (1998)** — public domain via NASA PDS, so no legal obligation, but the dataset
   is the site's whole calibration argument. Link it.
6. **`colour-science`** — BSD-3-Clause, "Copyright 2013 Colour Developers"; a NumFOCUS
   affiliated project. We import rather than redistribute, so the licence text is a courtesy,
   but the project asks to be cited via its Zenodo DOI: **10.5281/zenodo.17837391**.
7. **Alpine.js** — MIT, vendored and served with the notice stripped. This is the second
   outright breach after Payne, and the cheapest to fix.
8. **CDS / VizieR (catalogue VI/42)** — verified requested wording: *"This research has made
   use of the VizieR catalogue access tool, CDS, Strasbourg, France (DOI : 10.26093/cds/vizier).
   The original description of the VizieR service was published in 2000, A&AS 143, 23"*. CDS
   states the data are "free of usage in a scientific context" and that "the original authors
   and publication references including the publisher have to be explicitely cited" — so
   Roman, N. G. (1987), *PASP* 99, 695 must be named too.

## What to build

A `/credits` page (URL `/credits`, title **"Sources & credits"**). Build it exactly like
`/glossary`: data in `data/credits.json`, rendered by `web/build.py` into `credits.html`, so the
list is one file to maintain and can be reused inline.

**Page structure**

1. **Lede, one paragraph.** "Every colour here is modelled, and every model is someone's
   published work. This page is the full list — what each source contributes, and where to read
   the original." On-brand: the site's editorial line is honesty about model vs measurement, and
   a citation *is* that claim made checkable.
2. **The acknowledgement block**, first and unmissable: the NASA Exoplanet Archive sentence
   verbatim, in the site's quote style (reuse `.rtb-quote` from `roman.html`).
3. **Sections in pipeline order**, mirroring `/how` so the two pages interlock:
   *Planet parameters* → *Albedo spectra* → *Measured anchors* → *Colour science* →
   *Roman* → *Images & maps* → *Software & type*.
4. **Every entry, one card, six fields** (this is the `data/credits.json` schema):
   `title`, `authors`, `year`, `venue` (journal, volume, page), `doi` + `url` (DOI link
   preferred, ADS fallback), `contributes` — one plain sentence saying *what on this site would
   not exist without it*, e.g. "The phase slider on every planet page: both the dimming and the
   colour shift with phase come from this grid" — and `license`.
   The `contributes` line is the point. It is what makes the page readable by a non-scientist and
   what makes the email land.
5. **Reuse the existing renderers.** `web/textures.py` and `pipeline/observations.py` already
   carry `credit`/`license`/`source_url`; feed them into this page rather than retyping them, so
   the image credits can never drift from the ones shown in the lightbox.

**Inline attribution, three places**

- **Planet pages.** The data card already names the spectrum engine (`provenance`). Make it a
  link: `parametric` → `/credits#parametric`, `cahoy` → `/credits#cahoy-2010`, `picaso` →
  `/credits#picaso`, `measured-albedo` → `/credits#karkoschka-1998` (or `#payne-2026` for Earth).
  One anchor link per planet, ~5,700 pages carrying a citation, zero new copy to write.
- **`/how`.** Un-bury: pull the Karkoschka and Payne refs out of the collapsed maths block into
  the visible body, and add "Sources & credits →" at the foot of each step.
- **Footer / nav.** There is no footer today. The gallery intro already carries "Planet & star
  data: NASA Exoplanet Archive" (`gallery.html:47`) — add "· Sources & credits" beside it, and
  the same link on `/how`, `/glossary` and `/roman`.

**Repo hygiene, same sitting** (these get checked by anyone who follows the link): add
`LICENSE`, add `CITATION.cff` so the project can be cited *back*, add a `## Data sources` section
to `README.md` pointing at `data/credits.json` as the single source of truth, and record the
PICASO version in the emitted records.

## Who to contact

Order matters: software maintainers first (fastest to reply, lowest stakes, and a good reply is a
warm-up), then model authors, then missions.

| Person | Role / affiliation | Why them | How to reach | Verified? |
|---|---|---|---|---|
| **Thomas Mansencal** | Lead maintainer, `colour-science`; Principal Pipeline Programmer, Epic Games | Every hex on the site comes out of his library, used the way it's meant to be. Open-source authors love a strange application. | GitHub [@KelSolaar](https://github.com/KelSolaar); `thomas.mansencal@gmail.com` (published on his site) | Role verified; email from public listing — **confirm before sending** |
| **Natasha Batalha** | Research Scientist, NASA Ames; PICASO lead author/maintainer; 2025 PECASE recipient | PICASO is a named engine on the site and she is the reason it exists. Actively publishing on PICASO through 2026. | GitHub [@natashabatalha](https://github.com/natashabatalha); site `natashabatalha.github.io`; NASA pattern `natasha.e.batalha@nasa.gov` | Role verified; **email pattern unverified — take it from her CV or a recent paper's corresponding-author line** |
| **Kerri Cahoy** | Full Professor & Space Sector Head, MIT AeroAstro (also MIT EAPS) | First author of the grid that drives the phase slider and the Model Space reference points. Works on direct-imaging tech — this is her lane. | MIT directory; STAR Lab page (`starlab.mit.edu`); MIT pattern `kcahoy@mit.edu` | Affiliation verified; **email pattern unverified** |
| **Mark Marley** | Director, Lunar & Planetary Laboratory + Head, Dept. of Planetary Sciences, U. Arizona (2021–present) | Co-author on *both* Cahoy 2010 and Batalha 2019 — the single most load-bearing name on this project. **Verified alive and active: LPL CV file dated 2026.** | LPL faculty page `lpl.arizona.edu/faculty/mark-s-marley`; X [@astromarkmarley](https://x.com/astromarkmarley); Arizona pattern `<user>@arizona.edu` | Status + role verified; **email pattern unverified** |
| **Jonathan Fortney** | Professor, Chair of Astronomy & Astrophysics, and Director of the Other Worlds Laboratory, UC Santa Cruz | Third Cahoy 2010 author and Batalha 2019 co-author. OWL runs public-facing work — a natural onward path. | `jfortney.sites.ucsc.edu`; UCSC campus directory | Affiliation verified; email unverified |
| **Jessie Christiansen** | NExScI / Caltech-IPAC; lead author of the Archive reference paper (2025) | The Archive is the site's spine and she leads its public face; a heavy science communicator. | Archive [Helpdesk ticket form](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Helpdesk/nph-genTicketForm) — **use the helpdesk first**, it's the sanctioned route | Paper authorship verified; direct email unverified |
| **Roman SSC @ IPAC** | Roman Science Support Center, Caltech-IPAC — runs Coronagraph ops + community support, hosts the Cahoy grid | Institutional owner of both the CGI community programme and the file we redistribute. | `roman-help@ipac.caltech.edu` | Address appeared in search results — **verify on roman.ipac.caltech.edu before sending** |
| **Claire Andreoli** | Roman Communications Lead, NASA GSFC | The `/roman` target board is a launch-countdown asset aimed exactly at her audience. | `claire.andreoli@nasa.gov` | **Verified** on NASA's Roman media-resources page |
| **Ashley Balzer** | Roman Science Writer, NASA GSFC | Writes the mission's public stories; most likely to actually use the page. | `ashley.m.balzer@nasa.gov` | **Verified**, same page |
| **Vanessa Bailey** | JPL, Roman Coronagraph instrument scientist/technologist | Deepest CGI technical contact; the person who'd catch a wrong bandpass number. | JPL science profile `science.jpl.nasa.gov/people/VBailey/` | Involvement verified; **exact title unverified — do not name her role in the email** |
| **Erich Karkoschka** | U. Arizona LPL (1998 *Icarus* spectrophotometry) | His 1995 ESO data is the site's calibration proof. | LPL directory | **Current status unverified — check the LPL directory before writing** |
| **Allison Payne / Geronimo Villanueva** | NASA GSFC (Payne et al. 2026, Earth's composite spectrum) | Earth's swatch is theirs; a 2026 paper means an active, reachable group. | GSFC pattern; corresponding author on doi:10.3847/PSJ/ae2feb | Author list verified from Zenodo 17470005 (Payne is project leader, Villanueva supervisor); **addresses unverified** |
| **Óscar Carrión-González** | Lead author, A&A 651, A7 | Already the best-cited source on the site; `/roman` is built on his Table 4. | Institution *unverified* — check the paper and ADS for current affiliation | Unverified |

## Draft emails

Send plain text. Subject lines matter more than the body. Never ask for a share.

**(a) Model author — Kerri Cahoy / Mark Marley / Jonathan Fortney** (adapt the name)

> Subject: Your 2010 albedo grid, turned into a colour palette site
>
> Dear Prof. Cahoy,
>
> I've built a small site that computes the visible colour of every known exoplanet from
> physics — albedo spectrum × host-star spectrum, through the CIE 1931 colour matching
> functions, out as a hex code. It's a nights-and-weekends project, no funding, no affiliation.
>
> Your 2010 grid (ApJ 724, 189) does two jobs in it: it's one of the spectrum engines, and it's
> the entire basis of the phase slider — both the dimming and the colour shift as a planet goes
> from full to crescent come from your phase files. You're credited here: [link]/credits#cahoy-2010
>
> I'd genuinely like to know if I've misused it anywhere, particularly the phase interpolation
> and how I state the metallicity assumptions. Corrections very welcome.
>
> Thank you for putting the grid out publicly in the first place.
>
> João

**(b) Software maintainer — `colour-science` (swap the specifics for PICASO)**

> Subject: colour-science is doing the colorimetry for 5,700 exoplanets
>
> Hi Thomas,
>
> Thought you might enjoy an odd use of Colour. I've built a site that computes what every known
> exoplanet would look like to the human eye: model the light each planet reflects, multiply by
> its host star's spectrum, then hand the whole thing to `sd_to_XYZ` with the CIE 1931 2°
> observer and `XYZ_to_sRGB`. ~5,700 planets, no hand-rolled CIE maths anywhere — Colour does all
> of it. [link]
>
> You're credited at [link]/credits. One thing I'd love a sanity check on: I treat reflected
> planetary light as an emissive SPD (`illuminant=None`) and deliberately don't white-balance to
> the host star, so a flat-albedo planet around the Sun reads cream rather than white. If that's
> the wrong call, I'd rather hear it from you.
>
> Thanks for the library.
>
> João

**(c) Roman CGI / outreach team**

> Subject: A public countdown page for the Coronagraph's tech-demo targets
>
> Hi Claire,
>
> I run a small independent site that computes the colour of every known exoplanet from published
> albedo models, and shows each one twice: full-spectrum, and rebuilt from only what CGI's four
> bands would catch. The gap between the two is the point — how much of a planet's colour
> identity survives the filter set.
>
> There's a page built around the Coronagraph specifically: the tech-demo target shortlist
> (from Carrión-González et al. 2021), the dark-hole geometry, and a launch countdown. [link]/roman
>
> It's free, has no ads, and is explicit that every swatch is modelled, not photographed. If it's
> useful for launch-window outreach, please use it. If anything about the instrument is wrong —
> the bandpasses especially — I'd rather be told than be polite about it.
>
> João

## Timing

- **Week 0, before anything else** — fix the CGI band centres/widths in `pipeline/config.py`
  and re-emit. It is a data change, not a marketing one, and every Roman claim on the site
  is currently wrong by 10 nm and a factor of ~3 in spectroscopic width.
- **Week 1** — build `/credits`, add the Archive acknowledgement, `LICENSE` (code *and* an
  explicit licence for the site's own output), `CITATION.cff`, the Alpine + OFL notices, and a
  `README` data-sources section.
- **Week 2** — send (b) to Mansencal and Batalha. Low stakes, fast replies, and it shakes out
  whatever is wrong with the page.
- **Week 3** — send (a) to Cahoy, Marley, Fortney. Separate emails, each naming what *their*
  paper does here. Never a group send.
- **Week 4** — Archive helpdesk (confirming the acknowledgement is correctly worded is a
  legitimate reason to write), then Roman SSC / IPAC.
- **T-minus 6 weeks to Roman launch** (currently 30 Aug 2026 per `data/roman-targets.json`) —
  send (c) to Andreoli and Balzer. Their inbox is unmanageable in launch week; go early.
  See [15-roman-launch.md](./15-roman-launch.md).

## How we'll know it worked

- **Replies at all.** A scientist's reply rate to "here's your work, is it right?" is far higher
  than to a pitch. Two replies out of ten is a good week.
- **A correction received.** Better than praise: it means they read it, and the fix makes the
  science defensible.
- **Referrer logs** showing a `.edu`, `nasa.gov`, `ipac.caltech.edu` or mission-page domain.
  Instrument this before sending — see [99-tracking.md](./99-tracking.md).
- **A link from a group, lab or mission page.** Durable in a way social traffic never is.
- **An invitation** — colloquium, outreach talk, AAS/DPS poster, a mission blog post.

## Risks

- **Emailing before `/credits` exists.** Fatal. "I built this on your work" with no visible
  credit reads as extraction. The build is a hard prerequisite, not a parallel task.
- **Overclaiming the model.** The parametric engine — which covers *most* planets on the site —
  is an archetype blend, not a radiative-transfer solution. Never let an email imply PICASO or the
  Cahoy grid produced a colour it didn't. Every claim must survive being checked against the
  planet's own provenance tag.
- **Getting the bandpasses wrong in an email to the people who built the instrument.** No longer
  hypothetical: Band 4 is **825 nm/11%**, not 835 nm/15%, and Bands 2–3 are **17%**, not 6%.
  Emailing JPL or the Roman SSC before fixing `pipeline/config.py` would hand the one audience
  that checks a reason to dismiss the site's signature feature. Fix, rebuild, then write.
- **Wrong email address / dead contact.** Half the addresses above are inferred patterns. A
  bounced email to a department head is a wasted only-chance. Verify each from an institutional
  page or a recent paper.
- **Sounding like marketing.** No "would love if you shared this". The ask is a correction. If
  they share it, that's their choice, and it only happens if the email didn't ask.
- **Three live licence breaches, not one.** Payne et al. (CC BY 4.0 attribution incomplete),
  Alpine.js (MIT notice stripped from the served bundle) and Silkscreen (OFL 1.1 condition 2:
  the woff2 ship with no licence). All three are discourtesies in practice and breaches on
  paper; all three are fixed by one page and two text files.

## Links

- [Marketing plan](./README.md) — hub
- [02-press-kit.md](./02-press-kit.md) — the credits page is press-kit material; scientists check
  provenance before they link
- [05-machine-readable.md](./05-machine-readable.md) — `data/credits.json` and `CITATION.cff` make
  the project citable *back*
- [06-open-data.md](./06-open-data.md) — licensing our own output is the same weekend's work
- [15-roman-launch.md](./15-roman-launch.md) — the CGI outreach email is timed against launch
- [09-show-hn.md](./09-show-hn.md) — "I emailed the authors and they corrected me" is the best
  line a Show HN post can carry
- [99-tracking.md](./99-tracking.md) — instrument referrers before the first email goes out
