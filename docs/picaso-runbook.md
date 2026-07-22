# Runbook — Implementing & verifying PICASO (for Claude Code)

This is the **executable** companion to `docs/picaso-plan.md`. It is written for a future
Claude Code session to follow step by step. The **verification tests are the source of
truth**: PICASO's exact API varies by version, so adjust the code until the tests below pass —
do not trust the spectrum until the anchors do.

Guiding principle (from the plan): PICASO's engine is already NASA-validated. We are
**configuring** it, not calibrating physics. The tests verify *our configuration*, using two
anchors with external truth (HD 189733 b's measured blue; our committed Cahoy grid).

---

## 0. Preconditions & install

```bash
# Deps (already declared in the picaso optional-extra)
uv pip install -e '.[picaso]'          # picaso + astropy + pandas

# Reference + opacity data (the heavy part — build-time only, never in the image)
#   - reference data (stellar spectra etc.): ~0.2–1 GB
#   - opacity DB: ~2–15 GB; a resampled/low-R visible file is enough for reflected light.
#   VERIFY the current file + size from PICASO's install guide before downloading.
# Point PICASO at the data via its documented env vars, e.g.:
export picaso_refdata=/path/to/picaso/reference
export PYSYN_CDBS=/path/to/grp/redcat/trds        # pysynphot stellar data, if required
```

Smoke test the install (should print a wavenumber grid, no exception):
```bash
uv run python -c "from picaso import justdoit as jdi; print(jdi.opannection(wave_range=[0.4,0.9]).wno[:3])"
```
If this raises, the opacity DB is missing/mispathed — fix before proceeding. Until it works,
the router keeps falling back to Cahoy/parametric (no harm).

---

## 1. Replace the atmosphere setup

Edit `pipeline/spectrum/picaso_model.py`, function `_run_picaso`. Replace the isothermal
placeholder with a community-standard reflected-light setup. Intended shape (adjust to the
installed PICASO version):

```python
from picaso import justdoit as jdi
from astropy import units as u

opa = jdi.opannection(wave_range=[0.36, 0.95])     # µm; covers the CIE grid + Roman 835 band
case = jdi.inputs()
case.phase_angle(0)                                 # 0 -> geometric albedo (what we want)
case.gravity(mass=mass_m_earth, mass_unit=u.M_earth,
             radius=radius_r_earth, radius_unit=u.R_earth)
case.star(opa, temp=teff_k, metal=0.0, logg=4.5)    # host star illuminant

# TP profile: prefer a self-consistent or Guillot profile at the planet's irradiation
# instead of isothermal. Chemistry: chemical equilibrium at the chosen metallicity.
case.atmosphere(df=guillot_or_selfconsistent_tp(equilibrium_temp_k, n_layers=60))
case.chemeq_visscher(c_o=0.55, log_mh=np.log10(max(metallicity, 0.1)))   # solar-ish C/O

# Clouds: Virga / Ackerman–Marley. fsed controls sedimentation (cloud thickness).
#   Skip clouds first to match the cloud-free anchor, then enable for cloudy cases.
# case.clouds(...) / case.virga(...)  per installed API

df = case.spectrum(opa, calculation="reflected", full_output=True)
wno, albedo = np.asarray(df["wavenumber"]), np.asarray(df["albedo"])
wl_nm = 1e7 / wno                                   # cm^-1 -> nm
```

Keep the whole thing inside the existing `try/except -> ProviderUnavailable` guard so any
failure still degrades gracefully. Do NOT remove the disk cache (`data/cache/spectra/`).

---

## 2. Verification tests

Create `tests/test_picaso.py`. Every test **skips cleanly if PICASO is unavailable** (mirror
`tests/test_cahoy.py`), so the suite stays green with no opacity DB installed. Thresholds are
starting points — tighten once passing.

```python
import numpy as np, pytest
from pipeline.config import GRID_NM
from pipeline.spectrum.base import ProviderUnavailable

def _picaso_or_skip(**kw):
    from pipeline.spectrum.picaso_model import make_picaso
    try:
        return make_picaso(**kw)
    except ProviderUnavailable:
        pytest.skip("PICASO or its opacity data not installed")

# --- ANCHOR 1 (external truth): a cool Jupiter should reproduce our Cahoy Jupiter_1x ---
def test_picaso_reproduces_cahoy_cool_jupiter():
    from pipeline.spectrum.cahoy_grid import make_cahoy
    from pipeline.colour.cie import reflected_flux_to_colour
    from pipeline.illuminant.blackbody import SUN
    from colour import XYZ_to_Lab, delta_E
    star = SUN.spectrum(GRID_NM)
    pic = _picaso_or_skip(equilibrium_temp_k=150.0, radius_r_earth=11.0,
                          mass_m_earth=318.0, teff_k=5772.0, metallicity=1.0)
    cah = make_cahoy(semi_major_axis_au=5.0, metallicity=1.0)
    c_pic = reflected_flux_to_colour(pic.geometric_albedo(GRID_NM)*star,
                                     method="full-spectrum", illuminant_flux=star)
    c_cah = reflected_flux_to_colour(cah.geometric_albedo(GRID_NM)*star,
                                     method="full-spectrum", illuminant_flux=star)
    de = float(delta_E(XYZ_to_Lab(np.array(c_pic.xyz)), XYZ_to_Lab(np.array(c_cah.xyz)),
                       method="CIE 2000"))
    assert de < 12.0, f"PICASO cool-Jupiter should resemble Cahoy Jupiter_1x, ΔE={de:.1f}"

# --- ANCHOR 2 (external truth): HD 189733 b should come out BLUE (Hubble measured it blue) ---
def test_picaso_hd189733b_is_blue():
    from pipeline.colour.cie import reflected_flux_to_colour
    from pipeline.illuminant.blackbody import BlackbodyStar
    star = BlackbodyStar(teff_k=5052.0).spectrum(GRID_NM)
    p = _picaso_or_skip(equilibrium_temp_k=1209.0, radius_r_earth=12.7,
                        mass_m_earth=359.0, teff_k=5052.0, metallicity=1.0)
    c = reflected_flux_to_colour(p.geometric_albedo(GRID_NM)*star,
                                 method="full-spectrum", illuminant_flux=star)
    r, g, b = c.srgb
    assert b > r, f"HD 189733 b should be blue (B>R), got {c.srgb} {c.hex}"

# --- Sanity: albedo bounded on the full grid ---
def test_picaso_albedo_bounded():
    p = _picaso_or_skip(equilibrium_temp_k=1000.0, radius_r_earth=12.0,
                        mass_m_earth=300.0, teff_k=5500.0, metallicity=1.0)
    alb = p.geometric_albedo(GRID_NM)
    assert alb.shape == GRID_NM.shape and np.all((alb >= 0) & (alb <= 1))

# --- Physics: higher metallicity (more methane) should push a Neptune blue-green ---
def test_picaso_metallicity_reddens_less():   # more CH4 -> more red absorbed -> bluer
    from pipeline.colour.cie import reflected_flux_to_colour
    from pipeline.illuminant.blackbody import SUN
    star = SUN.spectrum(GRID_NM)
    lo = _picaso_or_skip(equilibrium_temp_k=150.0, radius_r_earth=3.9,
                         mass_m_earth=17.0, teff_k=5772.0, metallicity=1.0)
    hi = _picaso_or_skip(equilibrium_temp_k=150.0, radius_r_earth=3.9,
                         mass_m_earth=17.0, teff_k=5772.0, metallicity=30.0)
    c_lo = reflected_flux_to_colour(lo.geometric_albedo(GRID_NM)*star,
                                    method="full-spectrum", illuminant_flux=star)
    c_hi = reflected_flux_to_colour(hi.geometric_albedo(GRID_NM)*star,
                                    method="full-spectrum", illuminant_flux=star)
    # bluer = higher B relative to R
    assert (c_hi.srgb[2]-c_hi.srgb[0]) >= (c_lo.srgb[2]-c_lo.srgb[0])

# --- Contract: fallback preserved when unavailable (this one does NOT skip) ---
def test_router_still_falls_back_without_picaso(monkeypatch):
    from pipeline.spectrum import router
    def unavailable(**kw): raise ProviderUnavailable("test")
    monkeypatch.setattr(router, "make_picaso", unavailable)
    chosen = router.choose_model(equilibrium_temp_k=1400.0, radius_r_earth=13.0,
                                 mass_m_earth=800.0, semi_major_axis_au=0.05, teff_k=5000.0)
    assert chosen.source in ("parametric", "cahoy")   # never crashes
```

### Pass criteria
- **Anchor 1** (PICASO ≈ Cahoy cool Jupiter, ΔE < ~12): confirms the reflected-light setup is
  physically sane against validated output. This is the most important test.
- **Anchor 2** (HD 189733 b blue): confirms hot-Jupiter usage against a real measurement.
- If Anchor 1 fails, the atmosphere/cloud setup is wrong — iterate on the TP profile / clouds /
  chemistry (step 1), NOT on the colour pipeline.
- Tighten ΔE thresholds once green.

---

## 3. Run, batch, commit

```bash
uv run pytest tests/test_picaso.py -q          # anchors must pass (or skip if uninstalled)
uv run pytest -q && uv run ruff check pipeline web tests
uv run python -m pipeline build                # hot Jupiters / off-grid now route to picaso
# spot-check: spectrum_source == "picaso" for hot Jupiters; cool giants stay "cahoy"
uv run python -m web.build --out dist
```
Commit `data/planets.json` (+ cached spectra, or regenerate in CI). No web/template changes
needed — the "How to read this" panel already reports the engine.

---

## 4. Gotchas

- **Opacity DB path** is the #1 failure. `opannection` throws if it can't find it → our guard
  turns that into ProviderUnavailable → silent fallback. If PICASO "isn't doing anything,"
  check the smoke test in §0 first.
- **API drift:** `chemeq_visscher`, `atmosphere`, cloud calls differ across PICASO versions.
  The tests are the contract; adjust calls to the installed version.
- **wavenumber vs wavelength / µm vs nm:** PICASO returns wavenumber (cm⁻¹); convert
  `wl_nm = 1e7 / wno` and sort ascending (already handled in the wrapper).
- **Cool giants:** the router prefers Cahoy for T_eq < 500 K even when PICASO is available —
  intended (Cahoy is already validated there). PICASO is for the hot/off-grid cases.
- **Speed:** PICASO is slow; the disk cache (`data/cache/spectra/`, keyed by planet+engine)
  makes re-runs instant. Never runs at deploy time.
- **Honesty:** even a correct PICASO colour for a hot Jupiter is "modelled, not photographed"
  — real reflected colour there is genuinely uncertain (clouds, thermal contribution).
