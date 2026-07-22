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
   temperature, metallicity, clouds, phase angle). This is the core spectrum engine.
3. **Cahoy et al. 2010 albedo model grids** — precomputed Jupiter/Neptune-class
   albedo spectra at varying star-planet distances, metallicities, and cloud states.
   Good fallback/validation set; these are what the Roman Coronagraph community uses.
4. **Host-star illuminants** — approximate stars as blackbodies from Teff for v1;
   upgrade to PHOENIX/Kurucz model spectra later if needed.
5. **Roman Coronagraph (CGI) bandpasses** — the Roman hook. CGI observes in four
   visible bands: imaging/polarimetry at 575 nm (10% bandwidth) and 835 nm (15%),
   slit spectroscopy at 660 nm and 730 nm (6% each, R~50). Model these as top-hat
   filters for v1. The CGI team's published simulated observation products
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
- `web/` — Next.js (App Router, TypeScript). Statically consumes `planets.json`.
  Pages: gallery grid of planet swatches; per-planet page with the spectrum plot,
  palette, and the physical explanation of why it has that colour. Client-side
  interactivity (search/filter/sort) in React state; no backend needed for v1.

## Conventions

- Python: 3.11+, `uv` for deps, `ruff` for lint, type hints throughout.
- TypeScript: strict mode. Spectrum plots with a lightweight canvas/SVG component
  (no heavy chart lib needed for a single line plot).
- All displayed numbers rounded sensibly; store spectra downsampled to 5 nm steps.
- Keep the science honest: every palette page must state model assumptions
  (cloud state, metallicity, phase angle) — these are modelled, not photographed.

## Milestones

1. **Validate the pipeline on one planet.** Script that generates a Jupiter-analog
   albedo spectrum (PICASO quickstart or a Cahoy grid file), runs the CIE conversion,
   prints a hex code. Sanity check: a cloudy Jupiter analog should come out warm
   off-white/cream; a deep methane Neptune-like should come out blue-green;
   cutting clouds and methane should go dark.
2. Batch: 20 well-characterised planets → `planets.json`.
3. Next.js gallery + planet detail page.
4. **Roman view.** For each planet, integrate the reflected-light spectrum through
   the four CGI bandpasses only, then reconstruct a colour from those four samples
   (interpolate between band centres before the CIE step). Show side by side:
   "true colour" (full spectrum) vs "as Roman would see it" (four bands). This is
   the project's signature feature — how much colour identity survives Roman's
   filter set. Flag microlensing-discovered planets honestly: no light is ever
   received from them, so their swatches are model-only, marked as such.
5. Palette export (copy hex, CSS variables, maybe .ase file).
6. Stretch: phase-angle slider (colour vs. orbital phase), host-star illuminant
   comparison ("this planet around a red dwarf vs. the Sun"); post-launch, ingest
   real CGI photometry for the tech-demo targets.

## Gotchas

- PICASO needs reference data files downloaded on first run (see its docs); cache
  them and document the setup step in the README.
- sRGB clamping: many planet colours are low-luminance; normalise luminance before
  gamma encoding or everything renders near-black. Decide and document a consistent
  brightness convention (e.g. normalise Y to 0.6 for the base swatch).
- The Exoplanet Archive TAP API rate-limits; batch queries, cache responses to disk.
- Equilibrium temperature in the archive can be null; fall back to computing it
  from stellar Teff, radius, and semi-major axis.
