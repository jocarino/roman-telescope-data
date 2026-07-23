# Exoplanet Palette — developer handover

For a developer new to the project. Assumes you know tech, not astronomy — the
domain concepts are explained inline. Read this once and you can navigate the repo.

## What it is

**"The colour scheme of every known exoplanet, derived from physics."** A batch
pipeline computes each planet's visible colour from physical models, emits one JSON
file, and a static website renders a gallery + per-planet pages. No live backend, no
database. The output is real colours (hex + designer palettes) for ~20 real planets,
each shown two ways: its **true colour** and **as the Roman Space Telescope would
see it**.

## The one idea everything rests on

A planet has no light of its own — it reflects its star's light. So:

```
colour = (what the star emits at each wavelength)  ×  (what fraction the planet reflects at each wavelength)
              S(λ)  [illuminant]                          A(λ)  [geometric albedo]
```

Multiply those two curves → the light reaching a camera → collapse it to how a human
eye sees → an sRGB hex. That's the whole product.

### Domain concepts (the minimum you need)

- **Wavelength / λ** — "which colour" of light, in nanometres (nm). Human vision spans
  ~380 nm (violet) to 780 nm (red). Everything here lives on a fixed grid: **380–780 nm
  in 5 nm steps = 81 samples** (`GRID_ID = "cie-vis-380-780-5"`). Every curve is tagged
  with that grid id so a stale one can't be misread.
- **Spectrum** — a value per wavelength; i.e. an 81-element array.
- **Geometric albedo A(λ)** — fraction of light the planet reflects at each wavelength.
  0 = black, ~1 = mirror. This is the planet's colour *fingerprint*. Its shape is
  driven by chemistry: **methane** absorbs red → planet looks blue-green (why Neptune is
  blue); **thick clouds** reflect everything → bright/white; **sodium** absorbs yellow →
  hot cloud-free planets look dark cobalt.
- **Illuminant S(λ)** — the star's emitted spectrum. A star is approximated as a
  **blackbody**: an idealized glower whose colour depends only on its temperature
  (`Teff`, effective temperature in Kelvin) — cool = red, hot = blue-white. Same planet
  around a red star vs the Sun → different colour.
- **CIE 1931 colour-matching functions** — three standard curves modelling the human
  eye's three cone types. "Convolving" a spectrum with them (multiply + sum) collapses
  81 numbers → **XYZ tristimulus** (3 numbers), the canonical device-independent name
  for a colour. **XYZ → sRGB** is a fixed matrix + gamma curve → the hex your screen
  shows. We use the `colour-science` library for this, never hand-rolled.
- **ΔE2000 (delta-E)** — a perceptual distance between two colours (~1 = just-noticeable
  difference). Used to quantify "how much colour is lost" in the Roman view.

### The Roman hook (the signature feature)

The **Roman Space Telescope's Coronagraph (CGI)** is a real NASA instrument. A
*coronagraph* blocks the star's glare so the faint planet beside it is visible. But CGI
only observes through **four narrow filters** (top-hat bands at 575, 660, 730, 835 nm) —
it does *not* capture the full smooth spectrum.

So for each planet we also simulate: integrate the full spectrum through just those four
bands → 4 numbers → interpolate a curve back → recompute the colour. Then show **true
colour vs "as Roman would see it"** side by side, with the ΔE2000 between them. The
honest catch, surfaced in the UI: the four bands only cover 575–835 nm (yellow→near-IR),
so **the entire blue half of vision is extrapolated/guessed** — the plots hatch that
zone.

### Honesty is a design constraint

These colours are **modelled, not photographed**, and the code refuses to hide that:

- Every record carries its **`provenance`**: `model`, `model-microlensing`,
  `simulated-cgi`, `measured-cgi`, `measured-hwo`.
- Every record records which **spectrum engine** produced it (`parametric` / `cahoy` /
  `picaso`) and its model assumptions (cloud state, metallicity, phase angle).
- **Microlensing** planets (discovered by their gravity bending a background star's
  light) emit *no* isolable light ever — flagged `is_light_isolable=False`, marked
  model-only.
- The swatch `hex` is a colour *identity* rendered at a fixed display brightness
  (`BASE_SWATCH_LUMINANCE_Y = 0.6`) so genuinely-dark planets aren't just black; the
  *true* brightness is reported separately as `luminance_y`.

## Architecture: two stages, one file

```
  pipeline/  (Python, offline batch)                 web/  (Python, static-site generator)
  ─────────────────────────────────                 ──────────────────────────────────────
  archive fetch → engine router → CIE colour  ──►    reads planets.json, renders Jinja
  → palette → Roman-band reconstruction              templates → dist/ (html + htmx
  → emit  ───────────────────────────────────►       fragments + css/js + .ase files)
                         │                                          │
                         ▼                                          ▼
                 data/planets.json   ◄── the ONLY handoff      static files, any host
```

**Rule:** the expensive physics never runs in a web request. `pipeline/` runs offline
(your laptop / CI), commits `data/planets.json`; `web/` is a pure static consumer with
**no colour maths client-side**. Refreshing the data = regenerate the JSON, rebuild,
redeploy. Nothing dynamic.

### Seams (the extensibility pattern used throughout)

Everything swappable hides behind a Protocol/interface so alternatives slot in with zero
downstream change:

- **`SpectrumProvider`** (`pipeline/spectrum/base.py`) — anything that turns params into
  A(λ). Three impls: `parametric` (always available), `cahoy` (grid data), `picaso`
  (heavy engine). A **router** (`spectrum/router.py`) picks the best *available* one per
  planet type and falls back gracefully.
- **`Illuminant`** — the star's S(λ). v1 = blackbody; PHOENIX/Kurucz models later.
- **The measured-data seam** (`emit/build.py::obtain_band_samples`) — if a file
  `data/cgi_measured/{id}.roman-cgi.json` exists, real Roman photometry *replaces* the
  simulated band samples with byte-identical downstream code; provenance flips
  `simulated`→`measured` automatically. Empty today; the whole app is built to accept
  real Roman data post-launch by dropping in files.
- **Instrument views are a `list`**, never a hard-coded `roman` key — future missions
  (HWO) are purely additive.

## The pipeline, end to end

1. **Fetch** (`fetch/archive.py`) — query the NASA Exoplanet Archive TAP API
   (`pscomppars` table, no key needed) for a curated list of ~20 real planets
   (`catalog.py::CURATED_NAMES`). Responses cached to `data/cache/` (the API
   rate-limits). Missing equilibrium temperature is computed from stellar Teff, radius,
   and orbit distance.
2. **Route** (`spectrum/router.py`) — pick the albedo engine by planet type (rocky →
   parametric; cool giant → cahoy→picaso→parametric; hot giant → picaso→parametric).
   Records which engine actually ran.
3. **Albedo A(λ)** — the chosen provider evaluates albedo on the grid. v1 default is
   `parametric.py`: a transparent rule set mapping temperature + radius → cloud/chemistry
   regime → analytic albedo (`synthetic.py`). Not radiative transfer — an honest,
   documented stand-in.
4. **Colour** (`colour/cie.py`) — `F = A × S`; convolve with CIE CMFs → XYZ → sRGB →
   hex, plus the separate true-brightness `luminance_y`.
5. **Palette** (`palette/derive.py`) — a 5-stop lightness ramp around the base hue,
   optionally with accents sampled from real spectral windows.
6. **Roman view** (`bands/integrate.py` + `bands/reconstruct.py`) — integrate through
   the 4 CGI bands, PCHIP-interpolate back to a curve, recompute colour + ΔE2000.
7. **Assemble & emit** (`emit/build.py`, `emit/writer.py`) — build one validated
   `PlanetRecord` (pydantic, `models.py` is the JSON contract) → write
   `data/planets.json`.

## The web app

Static-site generator in `web/build.py`: reads `planets.json`, renders Jinja2 templates
to `dist/` — a gallery (`index.html`), a full page + an htmx **fragment** per planet,
and one `.ase` palette file per planet (Adobe Swatch Exchange). Client side (no build
step, vendored libs):

- **htmx** loads a planet's detail fragment into a drawer on click.
- **Alpine.js** (`static/app.js`) drives search / filter / sort over an inlined index,
  the **true↔Roman toggle**, palette export (hex / CSS vars / .ase), and procedural
  planet renders (`static/planet-render.js`).

Deploy is a multi-stage `Dockerfile` (Python renders → nginx serves); `nginx.conf`
handles clean URLs and `.ase` downloads.

## Run it

```bash
uv sync                                        # venv + core deps (Python 3.11+, uv)

uv run python -m pipeline build                # real archive catalog → data/planets.json
uv run python -m pipeline build --source demo  # 3 synthetic archetypes, fully offline
uv run python -m pipeline build --limit 1      # just the first planet
uv run pytest                                  # sanity gate + seam + export (test_picaso.py needs the isolated PICASO env)
uv run ruff check pipeline web tests

uv run python -m web.build --out dist          # render the static site
python3 -m http.server 8799 --directory dist   # preview → http://localhost:8799

docker build -t exoplanet-palette . && docker run -p 8080:80 exoplanet-palette
```

`build` prints each planet's true hex, Roman hex, ΔE2000, and palette as it goes.

## Repo map

```
pipeline/
  config.py          grid, brightness convention, instrument/bandpass registry (data, not code)
  models.py          pydantic PlanetRecord — the planets.json contract (single source of truth)
  catalog.py         curated planet list; Archive record → PlanetInput; display-name expansion
  fetch/archive.py   NASA Exoplanet Archive TAP client + disk cache + Teq fallback
  spectrum/          SpectrumProvider seam: base, router, parametric+synthetic, cahoy_*, picaso_*
  illuminant/        Illuminant seam: base + blackbody
  colour/cie.py      F(λ) → XYZ → sRGB; luminance; the ONE shared colour codepath
  bands/             integrate.py (4-band simulate) + reconstruct.py (PCHIP curve back)
  palette/           derive.py (ramp/accents) + export.py (.ase writer)
  emit/              build.py (assemble PlanetRecord, the measured-data seam) + writer.py
web/
  build.py           static-site generator; svg.py (spectrum plot); templates/ + static/
data/
  planets.json       the emitted artifact the site renders (committed)
  cahoy_grid/        Cahoy 2010 albedo CSVs + manifest
  picaso_spectra/    cached PICASO .npz outputs
docs/                spectrum-engines.md, picaso-plan/runbook.md, discovery-plan.md, this file
tests/               sanity gate (archetype colours), seam, router, cahoy, export, catalog
```

## Status & what's not built

- **Working now:** archive fetch, parametric engine, full colour + palette + Roman
  reconstruction, planets.json (20 planets), static site, Docker deploy, tests.
- **PICASO** (real radiative-transfer engine) is wired via the router but gated: it
  needs multi-GB opacity data and, critically, **can't share the main venv** (its `numba`
  dep pins NumPy ≤ 2.4 vs the project's 2.5) — it runs in an isolated `.venv-picaso` and
  writes cached spectra the main pipeline consumes. See `docs/picaso-runbook.md`.
- **Cahoy grid** provider exists; lights up automatically when its data is present.
- **Planned, not started:** a **discovery stage** (`docs/discovery-plan.md`) to find
  candidate planets from public light curves (TESS/Kepler, Roman microlensing) — a new
  parameter source upstream of the colour pipeline, behind the same seam pattern.

## Gotchas worth knowing

- Don't chase JWST/Hubble transit spectra for colour — they're infrared and can't yield a
  visible colour. Colour comes from albedo **models**, by design.
- Low-luminance planets render near-black unless luminance is normalised before gamma —
  hence the fixed-brightness swatch convention above.
- The Archive abbreviates names (`ups And d`); `catalog.py` expands them for *display*
  only — ids/slugs and data matching use the raw Archive name.
- Young directly-imaged giants have an archive `pl_eqt` reflecting *internal* heat, not
  irradiation; the router uses the computed *irradiation* temp to avoid mis-routing them
  to the hot-Jupiter engine (see `catalog.py::_model_temperature`).
```
