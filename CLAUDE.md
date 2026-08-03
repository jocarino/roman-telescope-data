# Exoplanet Palette

Derive colour palettes for real exoplanets from physics: generate each planet's
reflected-light spectrum, convert it to a perceptual colour via CIE colour matching,
and present the result as a designer-friendly palette. Tagline: "the colour scheme
of every known exoplanet, derived from physics."

## Why this works (domain background)

- A planet's visible colour comes from its **geometric albedo spectrum** (fraction of
  starlight reflected at each wavelength) multiplied by the **host star's spectrum**
  (the illuminant).
- Physics drives the palette: methane absorbs red (Neptune-likes go blue-green),
  thick clouds brighten everything toward white, cloud-free hot Jupiters are dark
  with sodium eating the yellow (HD 189733b measured deep cobalt blue).
- IMPORTANT caveat: most real measured exoplanet spectra (JWST/Hubble transit work)
  are infrared and CANNOT give a visible colour. Use albedo **models**, not transit
  spectra, for the colour computation. Do not go down the JWST-spectra path.

## Data sources

1. **NASA Exoplanet Archive** (https://exoplanetarchive.ipac.caltech.edu) — planet
   parameters: equilibrium temperature, radius, mass, semi-major axis, host star
   Teff/type. Use the TAP API (`pscomppars` table). Free, no key needed.
2. **PICASO** (`pip install picaso`) — NASA's open-source Python package that
   generates reflected-light albedo spectra from planet parameters (gravity,
   temperature, metallicity, clouds, phase angle). In production it is used for
   selected hot/exotic targets via a committed spectrum cache; most of the catalog
   uses the parametric engine or the Cahoy grid (see `docs/spectrum-engines.md`).
3. **Cahoy et al. 2010 albedo model grids** — precomputed Jupiter/Neptune-class
   albedo spectra at varying star-planet distances, metallicities, and cloud states.
   Good fallback/validation set; these are what the Roman Coronagraph community uses.
4. **Host-star illuminants** — stars are blackbodies from Teff. DECIDED (2026-07): this is
   the v1 convention, not a stopgap — no PHOENIX/Kurucz upgrade planned. A blackbody captures
   the first-order effect (the star's tint, which dominates for cool hosts); model spectra
   would only refine M-dwarf band structure, and swapping illuminants means regenerating
   every colour. The per-planet `sun_swap` field makes the illuminant's role explicit instead.
5. **Roman Coronagraph (CGI) bandpasses** — the Roman hook. Per the CGI Primer (CPP,
   8 Jan 2025), the FLIGHT configuration supports three visible bands: Band 1 imaging /
   polarimetry at 575 nm (10%), Band 3 slit + R~50 prism spectroscopy at 730 nm (15%),
   and Band 4 wide-field imaging at 825 nm (10%). **Only Band 1 with the hybrid Lyot
   coronagraph is a formal requirement; the rest are "best effort"** — a contractual term
   meaning not formally required, NOT a forecast that they won't happen. Band 2 (660 nm,
   15%) is physically installed on the CFAM filter wheel but was never characterised on
   the ground, so it is not a supported observing mode — installed but untested, not
   absent. Model these as top-hat filters for v1; widths above are the Primer's nominal
   spec, and as-built FWHMs run ~1–2 points wider. Do NOT reintroduce the old 660/6%,
   730/6%, 835/15% numbers: they appear in no primary source and were our own error. The CGI team's published simulated observation products
   (predicted exoplanet spectra with realistic noise) can be run through the same
   pipeline; post-launch, real CGI measurements of the tech-demo targets slot in.

## The pipeline (spectrum → hex)

1. Fetch planet + star parameters from the Exoplanet Archive.
2. Generate albedo spectrum A(λ) over 380–780 nm (PICASO, or interpolate Cahoy grid).
3. Compute reflected flux F(λ) = A(λ) × S(λ), where S(λ) is the star's spectrum.
4. Convolve F(λ) with the CIE 1931 2° colour-matching functions → XYZ tristimulus.
5. Normalise, convert XYZ → linear sRGB (standard 3×3 matrix), gamma-encode, clamp.
6. Derive a palette from the base colour: lightness ramp (5 stops), plus accent
   colours sampled from spectral features (e.g. the colour at the methane band edge).

Use the `colour-science` Python package for steps 4–5 (`colour.sd_to_XYZ`,
`colour.XYZ_to_sRGB`) rather than hand-rolling the maths. Hand-rolled CIE Gaussian
approximations are fine only for quick tests.

## Architecture

Two-stage design — do NOT run PICASO inside a web request; it is heavy and slow:

- `pipeline/` — Python. Batch script: pull N planets from the archive, generate
  spectra, compute colours, emit `data/planets.json` (one record per planet:
  params, downsampled spectrum, base hex, palette stops). Runs offline/CI.
- `web/` — Jinja2 static-site generator + htmx + Alpine.js. Statically consumes
  `planets.json`. Pages: gallery grid of planet swatches; per-planet page with the
  spectrum plot, palette, and the physical explanation of why it has that colour.
  Client-side interactivity (search/filter/sort) in Alpine/vanilla JS; no backend.

## Design principle: dual audience

The site must be **equally enjoyable for someone who knows nothing about exoplanets or this
project as for an astronomy nerd**. This is a hard requirement, not a nicety. In practice:

- **Labels are self-explanatory.** No cryptic, insider, or costume term is ever the *only*
  signpost for a control. A real oscilloscope's "RUN / SINGLE" means nothing to a newcomer;
  "Full spectrum / Roman 3-band" does. The retro/oscilloscope styling is a costume — it must
  never make a control harder to understand than a plain button would be.
- **Info buttons where it matters.** Complex or easily-misread ideas (full spectrum vs Roman,
  modelled vs measured, classic vs stylised render) get an ℹ button **in the accent colour**
  that reveals a plain-English explanation on demand — present when needed, out of the way
  otherwise. Don't bury the explanation; don't clutter simple controls with it either.
- **Honest wording.** Prefer "Modelled" over "Model"; never imply a colour is photographed when
  it is computed. Honesty about what is model vs measurement is the whole point of the project.
- **Jargon is marked, never assumed.** Every technical word is defined once in
  `data/glossary.json` and marked in templates with the `g()` macro
  (`{{ g('quadrature') }}`) — a subtle pixel-dotted underline that reveals a plain-English
  definition on hover/tap/focus, plus the full list at `/glossary` (URL-only, not in the nav).
  Rule of thumb: `g()` for **terms**, the `[i]` info button for **controls**. When you add copy
  with a new technical word, add the glossary entry in the same change —
  `tests/test_glossary.py` fails if a template marks a term that isn't defined.

## Conventions

- Python: 3.11+, `uv` for deps, `ruff` for lint, type hints throughout.
- Web: Jinja2 templates + htmx + Alpine.js, vanilla JS. Spectrum plots with a
  lightweight canvas/SVG component (no heavy chart lib needed for a single line plot).
- All displayed numbers rounded sensibly; store spectra downsampled to 5 nm steps.
- Keep the science honest: every palette page must state model assumptions
  (cloud state, metallicity, phase angle) — these are modelled, not photographed.

## Working in parallel (multiple sessions)

The owner sometimes runs **two Claude Code sessions on this repo at once**. Two sessions
editing the same files in the same checkout, both pushing to `main`, causes surprise
divergence and merge churn. To avoid it:

- **One git worktree per session.** Each session works in its own directory + branch under
  `.claude/worktrees/`, never the shared checkout. Create with the `EnterWorktree` tool (or
  `git worktree add ../<dir> -b <branch>`). Merge to `main` deliberately, one session at a time.
- **Split the work by area so merges stay conflict-free.** Almost all collisions have been two
  sessions both editing `web/static/app.js`, `web/templates/gallery.html`, or
  `web/static/style.css`. Keep the areas apart:
  - **Data/science side** — `pipeline/`, `data/`, `web/build.py`, `web/svg.py`, `tests/`.
  - **Web/UI side** — `web/templates/`, `web/static/`.
  If a task truly needs both, say so and coordinate before touching the other side's files.
- **Rebase before every push.** `git pull --rebase origin main` replays your commits on top of
  the other session's — no merge commits, and divergence is caught early instead of at a
  rejected push. Commit small and push often to shrink the collision window.
- **Never force-push `main`** — the other session's work lives there. On a rejected push,
  fetch + rebase + resolve; force only to overwrite your *own* just-pushed mistake.
- `data/planets.json` is the source of truth but is NOT committed (too big at 6k planets):
  it lives on disk locally and is published to GitHub Releases via `scripts/release-data.sh`;
  the committed `data/RELEASE` names the tag and deploy builds fetch it
  (`scripts/fetch_data.py`). **Staying current is automated** — `.github/workflows/catalogue.yml`
  probes the Archive on Thursdays/Friday and opens a PR with a *draft* release when it has moved;
  see `pipeline/drift.py` and the README. Two rules that keep it honest: the gated set is defined
  once in `catalog.GATE_CLAUSES` (Python predicate + ADQL together — never retype the gate for a
  remote query, that produced a phantom "560 planets behind"), and the probe fingerprints sums
  rather than counting rows, because `pscomppars` revises existing rows silently.
  Regenerate with `pipeline build --bulk N`; `dist/` is gitignored
  and built at deploy. Regenerating/releasing data is a "data side" change — don't do it from
  a UI-side session.
- **Preview servers: use `tools/exohub.py`, not a bare `http.server`.** When several sessions
  each serve their own `dist/`, nobody can tell which `localhost:PORT` is which worktree. Instead:
  - `python3 tools/exohub.py serve --build` — builds `dist/` and serves it on **this worktree's
    stable port** (`main`→8799; every other worktree hashes its branch into 8800–8889, same port
    every run). It also injects a `▟ <worktree> :<port>` badge into every page so the browser tab
    itself says which worktree you're viewing. **Always tell the user the resulting URL/port.**
  - `python3 tools/exohub.py dash` — a live table of every running preview server mapped back to
    its worktree (works even for servers started the old way, flagged `⚠ off-slot`).
  - `python3 tools/exohub.py mprocs` — one labelled pane per worktree (plus a dash pane) in
    [mprocs](https://github.com/pvolok/mprocs), for watching them all at once.
  Note: the machine only has `python3` (no bare `python`). See the README for the full rundown.

## Milestones

Milestones 1–5 are DONE; the catalog is the full archive pull (5,759 planets live).

1. **Validate the pipeline on one planet.** (DONE) Script that generates a Jupiter-analog
   albedo spectrum (PICASO quickstart or a Cahoy grid file), runs the CIE conversion,
   prints a hex code. Sanity check: a cloudy Jupiter analog should come out warm
   off-white/cream; a deep methane Neptune-like should come out blue-green;
   cutting clouds and methane should go dark.
2. Batch: 20 well-characterised planets → `planets.json`. (DONE; since scaled to the
   full catalog — see `docs/scaling-plan.md`.)
3. Gallery + planet detail page. (DONE — built as the Jinja2/htmx static site, not Next.js.)
4. **Roman view.** (DONE — computed at quadrature, schema v4.) For each planet, integrate
   the reflected-light spectrum through
   the supported CGI bandpasses only, then reconstruct a colour from those samples
   (interpolate between band centres before the CIE step). Show side by side:
   "true colour" (full spectrum) vs "as Roman would see it". This is the project's
   signature feature — how much colour identity survives Roman's filter set. Flag microlensing-discovered planets honestly: no light is ever
   received from them, so their swatches are model-only, marked as such.
5. Palette export (copy hex, CSS variables, maybe .ase file). (DONE — .ase + CSS vars.)
6. Stretch: phase-angle slider (DONE — colour vs. orbital phase), host-star illuminant
   comparison (DONE — `sun_swap` data + the "Light source" knob on the planet page);
   post-launch, ingest real CGI photometry for the tech-demo targets (future — runbook:
   `docs/roman-measured-data.md`).
7. **Solar system anchors.** (DONE) Jupiter, Saturn, Uranus, Neptune and Earth run through
   the exact same pipeline from MEASURED albedo spectra (Karkoschka 1998 via PDS for the
   giants; Payne et al. 2026 for Earth — see `data/measured_albedo/README.md`), with a real
   NASA photograph beside each swatch (`provenance: "measured-albedo"`,
   `pipeline/solar_system.py`). They are the site's calibration proof — the one place the
   spectrum→colour conversion is checked against a photographed planet — and the visitor's
   anchor for reading every exoplanet swatch.

## Gotchas

- PICASO needs reference data files downloaded on first run; it also cannot share the
  main venv (numba/NumPy conflict). Setup is documented in `docs/picaso-runbook.md`.
- sRGB clamping: many planet colours are low-luminance; normalise luminance before
  gamma encoding or everything renders near-black. Decide and document a consistent
  brightness convention (e.g. normalise Y to 0.6 for the base swatch).
- The Exoplanet Archive TAP API rate-limits; batch queries, cache responses to disk.
- Equilibrium temperature in the archive can be null; fall back to computing it
  from stellar Teff, radius, and semi-major axis.
