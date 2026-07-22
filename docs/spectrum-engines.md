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
automatically once their data is installed — **no code changes.**

## Provider 1 — parametric (always on)

`pipeline/spectrum/parametric.py`. Maps equilibrium temperature + radius to an albedo regime
via documented physical heuristics. Fast, offline, no data. Good enough for a striking
gallery; coarse (planets in the same temperature bucket look similar).

## Provider 2 — Cahoy et al. 2010 grid

`pipeline/spectrum/cahoy_grid.py`. Precomputed albedo spectra for cool Jupiter/Neptune-class
planets — the Roman community reference set.

**Activate:** populate `data/cahoy_grid/` with the grid files and a `manifest.json`:

```json
{
  "points": [
    {"dist_au": 2.0, "metallicity": 1.0, "cloud": "cloudy", "file": "d2_m1_cloudy.csv"}
  ]
}
```

Each referenced CSV has two columns: `wavelength_nm, geometric_albedo`. The provider picks the
nearest point in (log-distance, log-metallicity) and interpolates onto the CIE grid. Disk: tens
of MB. (Bilinear interpolation across the four surrounding points is a straightforward upgrade
from the v1 nearest-neighbour.)

## Provider 3 — PICASO

`pipeline/spectrum/picaso_model.py`. NASA's radiative-transfer package; the engine for
hot/exotic giants Cahoy does not cover.

**Activate:**
```bash
uv pip install -e '.[picaso]'         # picaso + astropy + pandas
# then download PICASO's reference/opacity data (multi-GB) per its install guide,
# and point PICASO at it (e.g. the picaso_refdata / opacity env vars it documents).
```

Disk: reference data ~0.2–1 GB; the **opacity database ~2–15 GB** depending on resolution —
verify the exact size from PICASO's install guide before downloading. All of this is
**build-time only**; it never enters the Docker image or the VPS. Computed spectra are cached
to `data/cache/spectra/` (PICASO is slow), keyed by planet + engine.

**⚠ Validation required on install.** The atmosphere setup in `picaso_model.py` (TP profile +
chemistry) is a *starting point*, not a validated model. Once the opacity data is present:
1. Run the pipeline and check a known planet (HD 189733 b should trend blue).
2. Tune the TP profile / cloud treatment / chemistry against published spectra.
3. Only then trust the colours. The wrapper is the integration seam; the atmospheric physics
   is the part that needs a human validation pass. Any failure (missing lib, missing opacity
   DB, run error) degrades cleanly to `ProviderUnavailable` → the router falls back.

## Why the fallback design

You can develop, test, build the site, and deploy with **zero** heavy data — everything runs
on `parametric`. Installing Cahoy and/or PICASO is a pure upgrade that changes *which* engine
each planet uses (and improves differentiation between similar planets) without touching the
colour pipeline, the web app, or the deploy. The `spectrum_source` field keeps it honest about
which engine actually produced each colour.
