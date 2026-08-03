# Cahoy et al. (2010) albedo grid

Precomputed geometric-albedo spectra for Jupiter- and Neptune-class planets. These are the
reference spectra the Roman Coronagraph community uses, and one of this project's three
spectrum engines (`pipeline/spectrum/cahoy_grid.py`).

**None of this is our data.** Until this file existed, the directory held 305 CSVs of two
unlabelled numeric columns and a `manifest.json` that was a pure filename lookup — anyone who
opened the folder, or copied it out, had no way to know whose work it was.

## Where it comes from

- **Citation:** Cahoy, K. L., Marley, M. S., & Fortney, J. J. (2010), "Exoplanet Albedo Spectra
  and Colors as a Function of Planet Phase, Separation, and Metallicity", *The Astrophysical
  Journal* **724**, 189. [doi:10.1088/0004-637X/724/1/189](https://doi.org/10.1088/0004-637X/724/1/189)
- **Source tarball:** `https://roman.ipac.caltech.edu/data/sims/cahoy2010_spectra.tgz`
- **Ingested by:** `pipeline/spectrum/cahoy_ingest.py` (µm → nm, one CSV per phase, plus the
  manifest). See `docs/spectrum-engines.md` for the full runbook.

## What the files contain

`manifest.json` indexes 16 grid points — star–planet distance (0.8, 2, 5, 10 AU) × metallicity
(Jupiters at 1× and 3× solar; Neptunes at 10× and 30×) — each phase-resolved from 0° (full) to
180° (new) in 10° steps.

Each CSV is two columns, **no header row**:

| column | meaning | units |
|---|---|---|
| 1 | wavelength | nm (converted from the upstream µm) |
| 2 | geometric albedo | dimensionless |

Non-zero-phase files include the brightness fall-off, not just a spectral shape.

## Licence status — unresolved, and we should resolve it

⚠️ **The upstream distribution carries no licence file**, which
`pipeline/spectrum/cahoy_grid.py` has noted since it was written. That leaves a real gap:

- **Deriving** colours from published model output is uncontroversial — model results are facts,
  and this is the ordinary use of a published grid.
- **Redistributing the grid files themselves** is a separate act, and it is the one we have not
  cleared. These 305 CSVs are committed to a public repository, so we are doing it right now.

Two ways to close it, in order of preference:

1. Ask the Roman SSC (`roman-help@ipac.caltech.edu`) whether the archive carries terms of use.
2. Failing that, stop shipping them here: drop the CSVs from the repo and fetch the tarball at
   build time, the way `data/planets.json` already works.

Until one of those happens, **do not include this directory in any dataset deposit**.
`scripts/release-data.sh` publishes only `planets.json`, so the release path is already clear.

See `LICENSE-DATA` §5.
