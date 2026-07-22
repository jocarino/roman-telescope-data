"""Standalone PICASO runner — executes in the ISOLATED picaso venv (.venv-picaso), NOT the
main env (PICASO's numba pins NumPy <= 2.4, which conflicts with the project's 2.5).

It computes one reflected-light geometric-albedo spectrum and writes a small cache file that
the main pipeline's `picaso_model.make_picaso` loads. This keeps the dependency conflict fully
isolated: heavy PICASO runs here; the main package just reads `.npz` cache.

Deliberately imports ONLY picaso + numpy + astropy (no `pipeline.*`), so it needs nothing from
the main package installed in the picaso venv.

Env vars (set before running):
    PICASO_REFDATA      -> the cloned reference/ dir (…/picaso-repo/reference)
    PICASO_OPACITY_DB   -> path to opacities_*.db
    PYSYN_CDBS          -> any existing dir (we feed a blackbody star via filename, not CDBS)

Usage (one planet):
    .venv-picaso/bin/python -m pipeline.spectrum.picaso_runner \
        --eqt 1209 --radius 12.7 --mass 359 --teff 5052 --metallicity 1.0 \
        --logg-star 4.5 --out data/cache/spectra/picaso_<key>.npz
"""

from __future__ import annotations

import argparse
import hashlib
import os

import numpy as np

# Resample the albedo onto this grid before caching (nm). Covers the CIE grid (380–780) plus
# the Roman 835 nm band's red edge (~898 nm). Small + sufficient.
_OUT_LO_NM, _OUT_HI_NM, _OUT_STEP_NM = 350.0, 1000.0, 1.0

_H, _C, _KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23


def cache_key(eqt: float, radius: float, mass: float, teff: float, metallicity: float) -> str:
    """MUST match pipeline.spectrum.picaso_model._cache_key exactly."""
    payload = repr(sorted({
        "eqt": round(eqt, 1), "r": round(radius, 3), "m": round(mass, 2),
        "teff": round(teff, 1), "z": round(metallicity, 3),
    }.items()))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _blackbody_starfile(teff: float, path: str) -> None:
    wl_um = np.linspace(0.30, 1.05, 3000)
    wl_m = wl_um * 1e-6
    flux = (2 * _H * _C**2) / (wl_m**5 * np.expm1(_H * _C / (wl_m * _KB * teff)))  # shape only
    np.savetxt(path, np.column_stack([wl_um, flux]))


def run(eqt, radius, mass, teff, metallicity, logg_star, semi_major, out) -> None:
    import warnings

    warnings.filterwarnings("ignore")
    os.environ.setdefault("picaso_refdata", os.environ["PICASO_REFDATA"])
    os.environ.setdefault("PYSYN_CDBS", os.environ.get("PYSYN_CDBS", os.environ["PICASO_REFDATA"]))

    from astropy import units as u
    from picaso import justdoit as jdi

    db = os.environ["PICASO_OPACITY_DB"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    starfile = out + ".starbb.dat"
    _blackbody_starfile(teff, starfile)

    opa = jdi.opannection(wave_range=[0.36, 0.95], filename_db=db)
    case = jdi.inputs()
    case.phase_angle(0)  # 0 -> geometric albedo
    case.gravity(mass=mass, mass_unit=u.M_earth, radius=radius, radius_unit=u.R_earth)
    case.star(
        opa, filename=starfile, w_unit="um", f_unit="erg/(cm**2 s AA)",
        radius=1.0, radius_unit=u.R_sun,
        semi_major=max(semi_major, 0.01), semi_major_unit=u.AU,
    )
    # Atmosphere: Guillot TP profile at the planet's irradiation + chemical equilibrium.
    # v1 is cloud-free (correct blue for Rayleigh-dominated hot Jupiters); clouds via virga
    # are a documented upgrade. C/O = 0.55 (solar).
    case.guillot_pt(Teq=max(eqt, 60.0))
    case.chemeq_visscher(0.55, float(np.log10(max(metallicity, 0.1))))

    df = case.spectrum(opa, calculation="reflected", full_output=False)
    wno = np.asarray(opa.wno)
    albedo = np.asarray(df["albedo"])
    wl_nm = 1e7 / wno
    order = np.argsort(wl_nm)
    wl_nm, albedo = wl_nm[order], np.clip(albedo[order], 0.0, 1.0)

    grid = np.arange(_OUT_LO_NM, _OUT_HI_NM + _OUT_STEP_NM / 2, _OUT_STEP_NM)
    resampled = np.interp(grid, wl_nm, albedo)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez(out, wl_nm=grid, albedo=resampled)
    if os.path.exists(starfile):
        os.remove(starfile)
    print(f"wrote {out}  (A(450)={resampled[100]:.3f} A(700)={resampled[350]:.3f})")


def main() -> None:
    ap = argparse.ArgumentParser(prog="pipeline.spectrum.picaso_runner")
    ap.add_argument("--eqt", type=float, required=True)
    ap.add_argument("--radius", type=float, required=True)
    ap.add_argument("--mass", type=float, required=True)
    ap.add_argument("--teff", type=float, required=True)
    ap.add_argument("--metallicity", type=float, default=1.0)
    ap.add_argument("--logg-star", type=float, default=4.5)
    ap.add_argument("--semi-major", type=float, default=0.05)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()
    out = args.out or (
        "data/cache/spectra/picaso_"
        + cache_key(args.eqt, args.radius, args.mass, args.teff, args.metallicity)
        + ".npz"
    )
    run(args.eqt, args.radius, args.mass, args.teff, args.metallicity,
        args.logg_star, args.semi_major, out)


if __name__ == "__main__":
    main()
