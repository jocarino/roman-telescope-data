# Measured full-disk albedo spectra (solar system anchors)

Real, measured whole-disk albedo spectra of solar system planets. These are the
calibration anchors: the one place the pipeline's spectrum → colour conversion can be
checked against planets we have actual photographs of. Committed because they are small,
static, and the science depends on their exact provenance.

## karkoschka1998_low.tab (+ .lbl)

Full-disk albedo spectra of **Jupiter, Saturn, Uranus, Neptune** (and Titan), 300–1050 nm
at 1 nm resolution (0.4 nm sampling), observed by Erich Karkoschka at ESO in July 1995.

- Source: NASA PDS Atmospheres Node, dataset `ESO-J/S/N/U-SPECTROPHOTOMETER-4-V2.0`,
  volume `gbat_0001`, file `data/1995low.tab` (verbatim copy, with its PDS label).
  https://pds-atmospheres.nmsu.edu/pdsd/archive/data/eso-jsnu-spectrophotometer-4-v20/
- Citation: Karkoschka, E. (1998), "Methane, Ammonia, and Temperature Measurements of the
  Jovian Planets and Titan from CCD–Spectrophotometry", Icarus 133, 134–146.
- License: NASA PDS data, public domain.
- Columns (fixed width, see the .lbl for byte offsets): vacuum wavelength (nm),
  air wavelength (nm), methane absorption coefficient (1/km-amagat), then albedos —
  Jupiter (full-disk at phase 6.8°), Saturn (full-disk at 5.7°, zero ring tilt),
  Uranus (geometric, i.e. 0° phase), Neptune (geometric), Titan (full-disk at 5.7°).

## earth_payne2026.csv

**Earth's** disk-integrated geometric albedo spectrum, 0.1–2.5 µm — a calibrated composite
of real observations (EPOXI photometry, Earthshine spectroscopy, LCROSS, satellite data),
standardised to geometric albedo by Payne et al. Columns: wavelength (µm), geometric albedo.

- Source: Zenodo record 17470005 (`earth_albedo.csv`, verbatim copy),
  https://zenodo.org/records/17470005
- Citation: Payne, A., Villanueva, G. L., Kofman, V., et al. (2026), "A Comprehensive
  Spectroscopic Reference of the Solar System and Its Application to Exoplanet Direct
  Imaging", Planetary Science Journal, doi:10.3847/PSJ/ae2feb.
- License: CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>), © the authors.
  Redistributed verbatim; §3(a)(1) attribution is rendered to visitors on `/how`.
  Provided without warranties of any kind — see §5 of the licence.

## Honesty notes

- These curves are **measurements** (Earth's is a calibrated composite of measurements) —
  unlike every exoplanet in the dataset, whose albedo is modelled. The record provenance
  (`measured-albedo`) and the planet-page copy must keep that distinction explicit.
- Jupiter/Saturn/Titan columns are full-disk albedo at the small quoted phase angles, not
  strictly geometric albedo (Uranus/Neptune are geometric). At ≤7° phase the spectral
  *shape* — which is what sets the colour — is essentially unchanged; we record the phase
  angle per planet in the emitted data.
