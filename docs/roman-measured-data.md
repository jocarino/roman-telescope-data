# Runbook: ingesting real Roman CGI photometry

The day the Roman Coronagraph tech demo publishes real reflected-light photometry of an
exoplanet, this is the complete procedure to put humanity's first measured exoplanet
colours on the site, next to our predictions. Designed to take minutes, not days —
**the code path already exists and is tested**; you are only supplying four numbers.

## How it works (30 seconds)

`pipeline/emit/build.py :: obtain_band_samples` is the seam: for every planet × instrument
it first looks for a real-measurement file on disk; only if none exists does it simulate
the band values from the model. Everything downstream — reconstruction → CIE colour →
palette → page — is byte-identical either way. A measured file flips the record's
provenance to `measured-cgi`, and the UI already renders the "Roman: measured" badge and
caption ("Measured: real Roman photometry in three bands…").

## The procedure

1. **Create the file** `data/cgi_measured/<planet-slug>.roman-cgi.json`:

   ```json
   {
     "epoch": "2027-03-14",
     "samples": [
       {"band_id": "cgi-575", "center_nm": 575.0, "value": 0.31, "uncertainty": 0.04},
       {"band_id": "cgi-730", "center_nm": 730.0, "value": 0.25, "uncertainty": 0.05},
       {"band_id": "cgi-825", "center_nm": 825.0, "value": 0.22, "uncertainty": 0.06}
     ]
   }
   ```

   - The slug is our planet id: lowercase NASA `pl_name`, non-alphanumerics → `-`
     (`47 UMa b` → `47-uma-b`). The likely tech-demo targets already in the catalog:
     `47-uma-b`, `47-uma-c`, `ups-and-d` (pinned with provenance `simulated-cgi`).
   - Any subset of bands is fine — spectroscopy-only or imaging-only epochs still work;
     the reconstruction interpolates whatever bands exist.
   - `uncertainty` is optional per band and carried into the data for the UI.

2. **What `value` means — read this before pasting numbers.** Each value is the
   **star-weighted mean geometric albedo in that band**, i.e. albedo-like, `A·Φ(α)`
   dimensionless in [0, ~1] — NOT a raw contrast. Published CGI results will most likely
   be flux ratios (contrast, ~1e-9). Convert with the standard relation
   `contrast = A·Φ(α) · (Rp/a)²`, so `value = contrast / (Rp/a)²` (planet radius and
   semi-major axis in the same units; both are on the planet's data card). If the paper
   already quotes geometric-albedo-times-phase-function, use it directly. Note the phase
   angle α of the observation is baked into a real measurement — that is physical truth,
   no correction wanted.

3. **Rebuild — mind the cache.** Measured files are *deliberately not* part of the
   per-planet record-cache key, so a plain rebuild would reuse the cached simulated
   record. Either bump `PIPELINE_VERSION` in `pipeline/config.py` (cleanest — busts every
   record) or rebuild without cache:

   ```bash
   uv run python -m pipeline build --bulk <N> --no-cache   # or bump PIPELINE_VERSION
   ```

   The build log prints `(source=measured)` for the planet — verify it.

4. **Check the page locally** (`uv run python -m web.build`, serve `dist/`): the planet
   should show the **"Roman: measured"** badge, the measured caption with the epoch, and
   the CH2 ROMAN channel now reconstructed from the real numbers. The ΔE readout becomes
   the real "how much colour Roman's bands preserved" — the project's headline
   number, now with actual data in it.

   **Also check `/roman`, the target board.** That planet's empty "Measured" slot should now
   be filled with the real colour, its row outlined in the accent, and the board's headline
   count should read 1 instead of 0. This needs no edit anywhere: the board reads the same
   `measured-cgi` provenance this seam sets (`pipeline/roman_board.py`). If the planet is not
   on the board, check its `catalog_id` in `data/roman-targets.json` — the board joins on that
   explicit id, not on the name, precisely because of the alias problem in the caveats below.

5. **Ship**: `scripts/release-data.sh` → commit `data/RELEASE` (and the measured JSON —
   it is small and IS committed; only `planets.json` is release-hosted) → push. The
   deploy webhook does the rest.

## Caveats recorded for that day

- **Identity matching is by slug** (documented v1 assumption in `pipeline/fetch/targets.py`).
  If the published name doesn't slug-match ours (aliases like `HD 95128 b` for `47 UMa b`), <!-- factcheck: ignore -->
  either name the file with OUR slug (simplest) or add the `resolve_planet_id()` alias step
  described there.
- **Multiple epochs**: the current seam holds one file per planet × instrument. A second
  epoch replaces the first (keep the old one in git history), or extend the seam to a list —
  the `BandSampleSetModel` already carries `epoch`.
- **Phase honesty**: a real measurement happens at whatever phase Roman caught the planet
  (near quadrature). The simulated Roman view is likewise computed at quadrature
  (`CGI_OBSERVATION_PHASE_DEG` in `pipeline/config.py`), so prediction and measurement are
  like-for-like. If the paper quotes the observation's actual phase angle, note it in the
  planet's entry here for the record.
- `tests/test_seam.py` exercises this exact path with a fixture file — if in doubt, mimic it.
