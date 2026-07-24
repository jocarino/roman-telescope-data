# Spectrum engines & the router

The albedo A(λ) that drives every colour comes from a `SpectrumProvider`. Three exist, and a
**router** (`pipeline/spectrum/router.py`) picks the best *available* one per planet, falling
back gracefully. The chosen engine is recorded on each record as `params.spectrum_source` and
shown in the "How to read this" panel — a run with no grid/opacity data simply reports
`parametric` everywhere, never silently.

## Preference order

| Planet type | Preference (first available wins) |
|---|---|
| rocky (< 2 R⊕) | `parametric` only |
| cool giant (T_eq < 500 K) | `cahoy` → `picaso` → `parametric` |
| hot / other giant | `picaso` → `parametric` |
| everything else | `parametric` |

`parametric` is always available, so there is always an answer. Cahoy/PICASO "light up"
automatically once their data is installed — **no code changes.** In the deployed full
catalog (5,759 planets) the mix is **4,439 parametric / 1,320 cahoy**, with PICASO active
for selected targets via its committed spectrum cache (see Provider 3).

## Provider 1 — parametric (always on)

`pipeline/spectrum/parametric.py`. Maps equilibrium temperature + radius to an albedo regime
via documented physical heuristics. Fast, offline, no data. Good enough for a striking
gallery; coarse (planets in the same temperature bucket look similar).

## Provider 2 — Cahoy et al. 2010 grid  ✅ INCLUDED

`pipeline/spectrum/cahoy_grid.py`. Precomputed geometric-albedo spectra (0° phase) for cool
Jupiter/Neptune-class planets — the Roman community reference set. **The grid is committed to
this repo** at `data/cahoy_grid/` (16 points: Jupiter 1×/3×, Neptune 10×/30×, at 0.8/2/5/10 AU;
~260 KB), so it is active out of the box for genuinely cool giants (T_eq < 500 K).

Data credit: **Cahoy, Marley & Fortney 2010, ApJ 724, 189.** Source tarball:
`https://roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz`.

To regenerate the grid from scratch:

```bash
curl -L https://roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz -o cahoy.tgz
tar xzf cahoy.tgz -C /tmp/cahoy
uv run python -m pipeline.spectrum.cahoy_ingest /tmp/cahoy   # -> data/cahoy_grid/*.csv + manifest.json
```

Each CSV has two columns `wavelength_nm, geometric_albedo`. The provider picks the nearest grid
point in (log-distance, log-metallicity) — jovians (Z≈1–3) map to the Jupiter models, ice
giants (Z≈10) to the Neptunes — and interpolates onto the CIE grid. (Bilinear interpolation
across the four surrounding points is a straightforward upgrade from the v1 nearest-neighbour.)

Note on scope: Cahoy models *cool, reflected-light-dominated* giants. Hot young imaged giants
(HR 8799, etc.) look hot in the archive (`pl_eqt` ~1000 K+), but that is *internal* heat, not
irradiation — the router now selects by the **irradiation** temperature in such cases, so at
their true ~45 K they route to Cahoy and render the correct cold-giant colours (see the
ARTIFACT — FIXED entry in `docs/picaso-runbook.md`). Genuinely hot irradiated giants go to
PICASO.

## Provider 3 — PICASO  ✅ ACTIVE (selected targets)

`pipeline/spectrum/picaso_model.py`. NASA's radiative-transfer package; the engine for
hot/exotic giants Cahoy does not cover. **As built** (full detail in
`docs/picaso-runbook.md`): PICASO cannot share the main venv (numba requires NumPy ≤ 2.4,
the project runs 2.5), so `pipeline/spectrum/picaso_runner.py` runs in a separate
`.venv-picaso` and writes small resampled `.npz` spectra to `data/picaso_spectra/`
(**committed**); `picaso_model.py` in the main venv just loads that cache and raises
`ProviderUnavailable` on a miss. The main pipeline, tests, and deploy therefore need
neither PICASO nor its opacity DB.

Disk (runner venv only): reference data ~179 MB; opacity DB ~7.34 GB (Zenodo record
14861730). All **build-time only**; it never enters the Docker image or the VPS. Verified
against both anchors: HD 189733 b comes out blue, and a cool Jupiter reproduces the Cahoy
grid. Any failure (missing lib, missing cache entry, run error) degrades cleanly to
`ProviderUnavailable` → the router falls back.

## Why the fallback design

You can develop, test, build the site, and deploy with **zero** heavy data — everything runs
on `parametric`. Installing Cahoy and/or PICASO is a pure upgrade that changes *which* engine
each planet uses (and improves differentiation between similar planets) without touching the
colour pipeline, the web app, or the deploy. The `spectrum_source` field keeps it honest about
which engine actually produced each colour.
