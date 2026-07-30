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
| **PICASO** (Batalha et al.) | Spectrum engine for selected targets; 7 precomputed spectra committed in `data/picaso_spectra/`, a `provenance` value users can see | Named only | `how.html:111`, glossary `picaso`, `pyproject.toml` extra | **PICASO asks to be cited; we don't.** No Batalha et al. 2019 ref, no Zenodo software DOI, no version recorded in the emitted data. |
| **`colour-science`** (CIE 1931 2° CMFs, XYZ→sRGB) | `pipeline/colour/cie.py` — literally every hex on the site (`MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]`, `sd_to_XYZ`, `XYZ_to_sRGB`) | One passing mention | `how.html:314`, inside a collapsed block | No link, no author, no version, no BSD-3-Clause note. The underlying CIE dataset is explained in the glossary but not credited as a dataset. |
| **Karkoschka (1998)**, *Icarus* 133, 134–146 | The measured spectra behind Jupiter, Saturn, Uranus, Neptune — the pipeline's calibration anchors | Yes, properly | `how.html:214` (journal, volume, pages, instrument, PDS provenance, public domain) | Behind the collapsed "The actual calculations" toggle. No link, no DOI. Not on the four planet pages it powers. |
| **Payne et al. (2026)**, *PSJ* | Earth's measured composite albedo spectrum | Yes, properly | `how.html:220` (journal, what it composites, CC BY 4.0) | Same burial. DOI `10.3847/PSJ/ae2feb` and Zenodo record 17470005 exist **only** in `data/measured_albedo/README.md`. CC BY 4.0 requires attribution *with a link*; we give neither link nor DOI to the visitor. |
| **Carrión-González et al. (2021)**, *A&A* 651, A7 | The Roman target board's eligible-planet list (Table 4) | Yes, best in the repo | `roman.html:201-205` + `data/roman-targets.json` — title, authors, journal, arXiv link, quoted counts | This is the model to copy everywhere else. |
| **Kopparapu et al. (2014)**, ApJ 787, L29 | Habitable-zone edges (`pipeline/habitable.py`, Table 1 coefficients) | Named only | `macros.html:1152,1171` | No journal/DOI on site (it's in the Python docstring). |
| **Thorngren et al. (2016)** mass–metallicity | Sets metallicity for the parametric engine (most planets on the site) | **No** | `pipeline/spectrum/parametric.py:20` docstring only | Invisible to visitors. |
| **Roman CGI bandpasses** (575/660/730/835 nm) | The entire signature feature | **No source cited** | Hard-coded in `pipeline/config.py:74-80` | *Unverified*: no reference for where these numbers came from. Check them against the CGI reference document (`roman.ipac.caltech.edu/docs/Coronagraph_Technical_Information.updated.pdf`) and cite it. |
| **Roman @ IPAC** hosting the Cahoy grid | `roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz` | **No** | `pipeline/spectrum/cahoy_ingest.py:9` | The people who host the data we ship get nothing. |
| **PICASO opacity DB** (Zenodo 14861730) | Needed to regenerate the committed PICASO spectra | **No** | `docs/picaso-runbook.md:64` | Zenodo record has its own citation. |
| **Telescope images** (JWST/STScI, ESO/SPHERE, ESO/J. Rameau, NAOJ, NASA/JPL/SSI, Apollo 17) | Planet-page "Telescope" hero | **Yes — exemplary** | `pipeline/observations.py`; rendered with credit + licence + source link in `macros.html:275-287` | None. This is already right. |
| **Surface maps** (NASA Earth Observatory — Reto Stöckli, Robert Simmon; Solar System Scope, CC BY 4.0) | The five anchors' real-map render | **Yes — exemplary** | `web/textures.py`; credit + licence shown in `macros.html:243` | None. |
| **Silkscreen** font (Jason Kottke, SIL OFL 1.1) | Site typeface + OG cards | Repo only | `web/assets/fonts/README.md` | OFL doesn't strictly require it, but it belongs on the credits page. |
| **Alpine.js** (`web/static/vendor/alpine.min.js`) | All site interactivity, vendored | **No** | — | MIT — needs a licence notice since we redistribute it. *Unverified*: version not recorded anywhere; check the file header. |
| **Repo licensing** | — | — | — | **No `LICENSE` file, no `CITATION.cff`, no data-sources section in `README.md`.** |

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
2. **PICASO** — **Batalha, N. E., Marley, M. S., Lewis, N. K., & Fortney, J. J. (2019)**,
   "Exoplanet Reflected-light Spectroscopy with PICASO", *ApJ* 878, 70,
   doi:10.3847/1538-4357/ab1b51. Plus the software DOI for the version used
   (e.g. Zenodo 10.5281/zenodo.14160128 for v3.3 — *unverified which version produced the
   committed `.npz` files; record it in the emitted data*).
3. **Cahoy, K. L., Marley, M. S., & Fortney, J. J. (2010)**, "Exoplanet Albedo Spectra and Colors
   as a Function of Planet Phase, Separation, and Metallicity", *ApJ* 724, 189,
   doi:10.1088/0004-637X/724/1/189. We redistribute the grid; cite it and state the hosting
   source (Roman @ IPAC).
4. **Payne et al. (2026)** — CC BY 4.0 requires attribution **with a link to the licence and the
   source**. Currently we give neither. doi:10.3847/PSJ/ae2feb, Zenodo record 17470005.
5. **Karkoschka (1998)** — public domain via NASA PDS, so no legal obligation, but the dataset
   is the site's whole calibration argument. Link it.
6. **`colour-science`** — BSD-3-Clause; the licence text must accompany redistribution of the
   *code*, which we don't do, but the library asks to be cited. Add the release + Zenodo DOI.
7. **Alpine.js** — MIT, vendored and served. Needs the copyright notice.

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
| **Geronimo Villanueva / Amber Payne** | NASA GSFC (Payne et al. 2026, Earth's composite spectrum) | Earth's swatch is theirs; a 2026 paper means an active, reachable group. | GSFC pattern; corresponding author on doi:10.3847/PSJ/ae2feb | **Unverified — read the paper's author list and corresponding address** |
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

- **Week 1** — build `/credits`, add the Archive acknowledgement, `LICENSE`, `CITATION.cff`,
  `README` data-sources section. Verify the CGI bandpass numbers against the CGI reference
  document *before* emailing anyone at JPL.
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
- **Getting the bandpasses wrong in an email to the people who built the instrument.** The
  575/660/730/835 nm numbers are currently uncited in `pipeline/config.py`. Verify first.
- **Wrong email address / dead contact.** Half the addresses above are inferred patterns. A
  bounced email to a department head is a wasted only-chance. Verify each from an institutional
  page or a recent paper.
- **Sounding like marketing.** No "would love if you shared this". The ask is a correction. If
  they share it, that's their choice, and it only happens if the email didn't ask.
- **CC BY 4.0 non-compliance on Payne et al.** currently live on the site. This is the one item
  in the audit that is a licence breach rather than a discourtesy — fix it first.

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
