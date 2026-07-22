# Plan — Activating PICASO

Status: **planned, not started.** The router + a guarded PICASO wrapper already exist
(`pipeline/spectrum/picaso_model.py`); this doc is about making PICASO actually produce
trustworthy colours.

## Reframe: the engine is already validated — we configure it, we don't calibrate it

PICASO is NASA's open-source reflected-light package, built by the Roman/exoplanet community
and **validated against the Cahoy et al. 2010 grid**. So:

- We are **not** calibrating a physics engine from scratch. The radiative transfer is trusted.
- Our job is to **drive it correctly** — supply each planet a sensible temperature-pressure
  profile, cloud model, and chemistry using the community's *published recipes* — and then
  **verify our usage** against known answers.

The crude isothermal profile currently in `picaso_model.py` is a placeholder; the real work
is replacing it with a standard setup (below).

## Where PICASO actually adds value

The Cahoy grid we already ship **is** validated PICASO output for cool giants, so PICASO adds
little there. Point it at what Cahoy does **not** cover:

- **Hot Jupiters** (HD 189733 b, 51 Peg b, WASP-*) — currently parametric, all similar blues.
- **Sub-Neptunes / warm Neptunes** off the Cahoy grid points.
- **Arbitrary metallicities / temperatures** between grid nodes.

This is also what fixes the "hot Jupiters all look alike" clustering.

## Verification anchors (a few, two with external truth)

You don't calibrate *with* planets — you verify usage. Anchors:

1. **HD 189733 b — real measured colour.** Hubble measured its optical geometric albedo
   (deep blue; Ag high in blue, low in red — Evans et al. 2013). PICASO should reproduce a
   blue colour. *External ground truth.*
2. **Cross-check vs the Cahoy grid we already have.** Run PICASO with cool-Jupiter parameters
   (1× solar, ~2–5 AU) and confirm it reproduces `data/cahoy_grid/Jupiter_1x_*`. *Self-
   contained, no external data.*
3. **A cloudy vs cloud-free pair** — confirm clouds brighten/whiten as expected.
4. **A Neptune-metallicity case** — confirm methane drives it blue-green (matches Cahoy 10×).

If (1) and (2) pass, trust PICASO across the interpolated space. ~3–4 checks, two free.

## Setup

```bash
uv pip install -e '.[picaso]'     # picaso + astropy + pandas (already in the extra)
```
Then download PICASO's reference + opacity data (see PICASO install guide):
- reference data (stellar spectra, etc.) — ~0.2–1 GB
- opacity database — ~2–15 GB depending on resolution; a resampled/low-R file is fine for
  visible reflected light. **Verify the exact file/size from PICASO's docs before pulling.**
- point PICASO at it via its documented env vars / `opannection`.

All build-time only — never enters the Docker image or the VPS.

## Build order (when picked up)

1. **Install + smoke test.** Install PICASO + opacity DB. Confirm `opannection` succeeds and a
   single reflected-light run returns a spectrum. (Until this works, the router keeps falling
   back — no harm.)
2. **Replace the atmosphere setup** in `picaso_model.py`: swap the isothermal placeholder for a
   community-standard recipe — a Guillot or self-consistent TP profile at the planet's
   irradiation, chemical equilibrium (`chemeq`), and Virga/A&M clouds (`fsed` parameter).
   Keep it all inside the existing `try/except -> ProviderUnavailable` guard.
3. **Anchor verification** (the checks above), as pytest cases where feasible:
   - PICASO cool-Jupiter vs our Cahoy `Jupiter_1x` — ΔE within a threshold.
   - HD 189733 b comes out blue (b-channel dominant).
4. **Cache + batch.** Computed spectra already cache to `data/cache/spectra/`. Run the full
   catalog; hot Jupiters and off-grid planets now route to PICASO (recorded as
   `spectrum_source: picaso`). Commit the resulting `planets.json` + cached spectra (or
   regenerate in CI).
5. **UI.** No changes needed — the "How to read this" panel already reports the engine.

## Disk / performance

- Opacity DB: multi-GB, dev/CI only.
- PICASO is slow (seconds+ per planet) — the disk cache (keyed by planet + engine) means the
  cost is paid once. The deployed site never runs PICASO; it consumes the baked `planets.json`.

## Honest caveats

- **Configuration, not calibration** — but configuration still has choices (TP profile, cloud
  `fsed`, C/O ratio) that affect colour. The anchor checks are what keep those honest.
- **Cool giants gain little** — Cahoy already covers them with validated output. Consider
  routing cool giants to Cahoy even when PICASO is available (current router already prefers
  Cahoy for T_eq < 500 K, so this is already the behaviour).
- **Hot-Jupiter reflected colour is genuinely uncertain** in reality (clouds, thermal
  contribution) — PICASO gives a defensible *model* colour, still "modelled, not photographed."
