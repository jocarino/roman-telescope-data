"""PICASO reflected-light albedo provider.

PICASO (NASA's open-source radiative-transfer package) generates reflected-light albedo
spectra from planet + star parameters. It is the engine for hot / exotic giants that the
Cahoy grid does not cover.

ACTIVATION: `pip install -e '.[picaso]'` AND download PICASO's reference/opacity data (multi-
GB — see PICASO's install guide, and docs/ here). Until both are present, `make_picaso()`
raises ProviderUnavailable (via a guarded import + a guarded opannection) and the router falls
back. Nothing else in the pipeline changes when PICASO becomes available.

IMPORTANT (honesty): the atmosphere setup below (TP profile + chemistry) is a *starting
point*. Once the opacity data is installed, validate the output against a known planet (e.g.
HD 189733 b should trend blue) and tune the profile/cloud treatment before trusting colours.
This wrapper is the integration seam; the atmospheric physics needs a validation pass on
install. All setup is wrapped so any failure degrades gracefully to ProviderUnavailable.
"""

from __future__ import annotations

import hashlib

import numpy as np

from pipeline.config import SPECTRA_CACHE_DIR
from pipeline.spectrum.base import ProviderUnavailable

# Wavelength window for the reflected-light run (µm) — a little past the CIE grid so the
# Roman 835 nm band is covered.
_WAVE_RANGE_UM = (0.36, 0.95)


class PicasoProvider:
    """Holds a precomputed albedo curve (PICASO is slow, so we run once and interpolate)."""

    def __init__(self, wavelengths_nm: np.ndarray, albedo: np.ndarray):
        self._wl = wavelengths_nm
        self._albedo = albedo

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        return np.clip(np.interp(wl, self._wl, self._albedo), 0.0, 1.0)


def _cache_key(**params) -> str:
    payload = repr(sorted(params.items()))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _run_picaso(
    *, equilibrium_temp_k: float, radius_r_earth: float, mass_m_earth: float,
    teff_k: float, metallicity: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Run one PICASO reflected-light spectrum. Imports are lazy and any failure propagates
    (the caller converts it to ProviderUnavailable)."""
    from astropy import units as u  # noqa: PLC0415
    from picaso import justdoit as jdi  # noqa: PLC0415

    # opannection needs the opacity database; this line fails loudly if it is missing.
    opa = jdi.opannection(wave_range=list(_WAVE_RANGE_UM))

    case = jdi.inputs()
    case.phase_angle(0)
    case.gravity(
        mass=mass_m_earth, mass_unit=u.M_earth,
        radius=radius_r_earth, radius_unit=u.R_earth,
    )
    case.star(opa, temp=teff_k, metal=0.0, logg=4.5)

    # Atmosphere: a simple isothermal-ish profile at the equilibrium temperature with
    # chemical-equilibrium abundances. STARTING POINT — validate/tune on install.
    import pandas as pd  # noqa: PLC0415

    n_layers = 60
    pressure = np.logspace(-6, 2, n_layers)  # bars
    temperature = np.full(n_layers, max(equilibrium_temp_k, 50.0))
    atmo = pd.DataFrame({"pressure": pressure, "temperature": temperature})
    case.atmosphere(df=atmo)
    case.chemeq_visscher(c_o=1.0, log_mh=np.log10(max(metallicity, 0.1)))

    df = case.spectrum(opa, calculation="reflected", full_output=True)
    wno = np.asarray(df["wavenumber"])  # cm^-1
    albedo = np.asarray(df["albedo"])
    wl_nm = 1e7 / wno  # cm^-1 -> nm
    order = np.argsort(wl_nm)
    return wl_nm[order], albedo[order]


def make_picaso(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    teff_k: float,
    metallicity: float,
    **_ignored,
) -> PicasoProvider:
    """Factory for the router. Raises ProviderUnavailable if PICASO or its data is missing,
    or if any step of the run fails."""
    if radius_r_earth is None or mass_m_earth is None or equilibrium_temp_k is None:
        raise ProviderUnavailable("PICASO needs radius, mass and equilibrium temperature.")

    key = _cache_key(
        eqt=round(equilibrium_temp_k, 1), r=round(radius_r_earth, 3),
        m=round(mass_m_earth, 2), teff=round(teff_k, 1), z=round(metallicity, 3),
    )
    cache_file = SPECTRA_CACHE_DIR / f"picaso_{key}.npz"
    if cache_file.exists():
        d = np.load(cache_file)
        return PicasoProvider(d["wl_nm"], d["albedo"])

    try:
        wl_nm, albedo = _run_picaso(
            equilibrium_temp_k=equilibrium_temp_k, radius_r_earth=radius_r_earth,
            mass_m_earth=mass_m_earth, teff_k=teff_k, metallicity=metallicity,
        )
    except ProviderUnavailable:
        raise
    except Exception as exc:  # ImportError, missing opacity DB, run failure, ...
        raise ProviderUnavailable(f"PICASO unavailable or run failed: {exc}") from exc

    SPECTRA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(cache_file, wl_nm=wl_nm, albedo=albedo)
    return PicasoProvider(wl_nm, albedo)
