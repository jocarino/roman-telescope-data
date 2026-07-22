"""PICASO reflected-light albedo provider (main-env side).

PICASO's numba pins NumPy <= 2.4, which conflicts with the project's 2.5, so PICASO **cannot
run in the main venv**. Instead the heavy run happens in an isolated venv via
`pipeline/spectrum/picaso_runner.py`, which writes a small `.npz` albedo cache. This module
just **loads that cache** — and, if configured, invokes the runner as a subprocess to generate
a missing spectrum on demand.

Activation (env vars, see docs/picaso-runbook.md):
    PICASO_VENV_PYTHON  -> interpreter of the isolated picaso venv (e.g. .venv-picaso/bin/python)
    PICASO_REFDATA      -> cloned reference/ dir
    PICASO_OPACITY_DB   -> path to opacities_*.db

If a spectrum is neither cached nor generatable (no venv/data), `make_picaso` raises
ProviderUnavailable and the router falls back — the fallback contract is preserved.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import numpy as np

from pipeline.config import SPECTRA_CACHE_DIR
from pipeline.spectrum.base import ProviderUnavailable


class PicasoProvider:
    """Loads a precomputed albedo curve (from the isolated-venv runner) and interpolates."""

    def __init__(self, wavelengths_nm: np.ndarray, albedo: np.ndarray):
        self._wl = wavelengths_nm
        self._albedo = albedo

    def geometric_albedo(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        wl = np.asarray(wavelengths_nm, dtype=float)
        return np.clip(np.interp(wl, self._wl, self._albedo), 0.0, 1.0)


def _cache_key(eqt: float, radius: float, mass: float, teff: float, metallicity: float) -> str:
    """MUST match pipeline.spectrum.picaso_runner.cache_key exactly."""
    payload = repr(sorted({
        "eqt": round(eqt, 1), "r": round(radius, 3), "m": round(mass, 2),
        "teff": round(teff, 1), "z": round(metallicity, 3),
    }.items()))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _load(cache_file: Path) -> PicasoProvider:
    d = np.load(cache_file)
    return PicasoProvider(d["wl_nm"], d["albedo"])


def _try_generate(cache_file: Path, *, eqt, radius, mass, teff, metallicity, semi_major) -> bool:
    """Invoke the isolated-venv runner to produce the spectrum. Returns True on success."""
    venv_py = os.environ.get("PICASO_VENV_PYTHON", ".venv-picaso/bin/python")
    if not Path(venv_py).exists() or "PICASO_OPACITY_DB" not in os.environ:
        return False
    # Invoke the runner by FILE PATH: it is standalone (no `pipeline.*` imports), so it runs
    # in the isolated venv which has picaso+numpy but not the pipeline package.
    runner = Path(__file__).with_name("picaso_runner.py")
    cmd = [
        venv_py, str(runner),
        "--eqt", str(eqt), "--radius", str(radius), "--mass", str(mass),
        "--teff", str(teff), "--metallicity", str(metallicity),
        "--semi-major", str(semi_major if semi_major is not None else 0.05),
        "--out", str(cache_file),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1200)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return cache_file.exists()


def make_picaso(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None,
    teff_k: float,
    metallicity: float,
    semi_major_axis_au: float | None = None,
    **_ignored,
) -> PicasoProvider:
    """Factory for the router. Loads a cached PICASO spectrum, generating it via the isolated
    venv if configured. Raises ProviderUnavailable if unavailable."""
    if radius_r_earth is None or mass_m_earth is None or equilibrium_temp_k is None:
        raise ProviderUnavailable("PICASO needs radius, mass and equilibrium temperature.")

    key = _cache_key(equilibrium_temp_k, radius_r_earth, mass_m_earth, teff_k, metallicity)
    cache_file = SPECTRA_CACHE_DIR / f"picaso_{key}.npz"

    if cache_file.exists():
        return _load(cache_file)

    if _try_generate(
        cache_file, eqt=equilibrium_temp_k, radius=radius_r_earth, mass=mass_m_earth,
        teff=teff_k, metallicity=metallicity, semi_major=semi_major_axis_au,
    ):
        return _load(cache_file)

    raise ProviderUnavailable(
        "No cached PICASO spectrum and the isolated picaso venv/data is not configured "
        "(set PICASO_VENV_PYTHON + PICASO_OPACITY_DB + PICASO_REFDATA)."
    )
