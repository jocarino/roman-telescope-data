"""Global constants: the CIE wavelength grid, the instrument (bandpass) registry, and
the brightness convention. These are data, not behaviour — keeping them in one place is
what lets the rest of the pipeline stay source-agnostic and future-mission-additive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# --- Spectrum-engine data locations ------------------------------------------------------
# Cahoy et al. 2010 albedo grid: drop the grid files + a manifest.json here to activate the
# CahoyProvider (see pipeline/spectrum/cahoy_grid.py and docs). Absent by default -> the
# router falls back. PICASO availability is detected by import, not a path.
CAHOY_GRID_DIR = Path("data/cahoy_grid")
# Precomputed PICASO spectra (PICASO is slow + needs a 7 GB opacity DB to regenerate, so
# these are COMMITTED for reproducibility — the pipeline/deploy rebuild reads them without
# needing PICASO installed). Keyed by planet params.
SPECTRA_CACHE_DIR = Path("data/picaso_spectra")

# --- The one fixed grid every ReflectedFlux curve lives on -------------------------------
# 380-780 nm at 5 nm => 81 samples. Tag every stored curve with GRID_ID so a stale record
# can never be silently misread on a different grid.
GRID_ID = "cie-vis-380-780-5"
GRID_START_NM = 380.0
GRID_END_NM = 780.0
GRID_STEP_NM = 5.0
GRID_NM: np.ndarray = np.arange(GRID_START_NM, GRID_END_NM + GRID_STEP_NM / 2, GRID_STEP_NM)
GRID_N = len(GRID_NM)  # 81

# --- Brightness convention (see CLAUDE.md gotcha) ----------------------------------------
# Many planet colours are low-luminance; normalise relative luminance Y to this value
# before gamma-encoding so swatches don't all render near-black. Documented + consistent.
BASE_SWATCH_LUMINANCE_Y = 0.60

# --- Instrument / bandpass registry ------------------------------------------------------
# An instrument is DATA. Adding HWO later = appending an Instrument here; nothing in the
# band-integration or reconstruction code is hard-coded to a band COUNT -- which is what let
# the CGI set drop from four bands to three without touching either.


@dataclass(frozen=True)
class Bandpass:
    id: str
    center_nm: float
    bandwidth_frac: float  # fractional bandwidth; top-hat half-width = center * frac / 2
    shape: str  # "tophat" | "gaussian"
    role: str  # "imaging" | "spectroscopy" | "polarimetry"

    @property
    def half_width_nm(self) -> float:
        return self.center_nm * self.bandwidth_frac / 2.0

    @property
    def lo_nm(self) -> float:
        return self.center_nm - self.half_width_nm

    @property
    def hi_nm(self) -> float:
        return self.center_nm + self.half_width_nm


@dataclass(frozen=True)
class Instrument:
    id: str
    name: str
    mission: str
    bands: tuple[Bandpass, ...]

    @property
    def band_centers_nm(self) -> np.ndarray:
        return np.array([b.center_nm for b in self.bands])


# Roman Coronagraph (CGI), FLIGHT configuration per the CGI Primer (CPP, 8 Jan 2025), p.5:
#   Band 1  575 nm, 10%  imaging/polarimetry, hybrid Lyot  -- the ONLY formally supported mode
#   Band 3  730 nm, 15%  slit + R~50 prism spectroscopy, shaped pupil   } best effort
#   Band 4  825 nm, 10%  wide-FoV imaging, shaped pupil                 } best effort
#
# Band 2 (660 nm, 15%) is NOT here, and the reason matters if you ever write this up: the
# filter IS physically on the CFAM wheel and the spectrometer carries a second Amici prism
# for it. It was never characterised on the ground, so it is not an officially supported
# observing mode (Bailey et al. 2021, Table 1 note). Installed but untested -- not absent.
#
# Earlier versions of this file carried 660/6%, 730/6% and 835/15%. The "835 nm" centre and
# the "6%" widths appear in NO primary CGI source; they were our own errors, not a
# superseded spec. Widths here are the Primer's nominal filter spec; the as-built FWHMs
# measured by Bailey et al. 2021 and Zellem et al. 2022 run ~1-2 points wider (730 nm:
# 16.7-17%, 825 nm: 11.4-12%). The difference is worth well under 1 dE2000 -- but say which
# convention you used when publishing, because a referee-minded reader will check.
#
# Modelled as top-hats for v1: real filter profiles have sloped shoulders, so "15%" is a
# design width, not a measured FWHM.
ROMAN_CGI = Instrument(
    id="roman-cgi",
    name="Roman Coronagraph",
    mission="Roman",
    bands=(
        Bandpass("cgi-575", 575.0, 0.10, "tophat", "imaging"),
        Bandpass("cgi-730", 730.0, 0.15, "tophat", "spectroscopy"),
        Bandpass("cgi-825", 825.0, 0.10, "tophat", "imaging"),
    ),
)

INSTRUMENTS: dict[str, Instrument] = {ROMAN_CGI.id: ROMAN_CGI}

# The phase angle at which the simulated Roman view is computed. A coronagraph can never
# observe full phase (a fully-lit planet sits behind its star); CGI catches planets near
# QUADRATURE, half-lit. Simulated band samples, the reconstructed Roman colour, and its
# delta-E (against the full spectrum at the SAME phase, isolating what the filters lose)
# all use this geometry, so post-launch measured photometry is compared like-for-like.
CGI_OBSERVATION_PHASE_DEG = 90.0

PIPELINE_VERSION = "0.1.0"
# v4: Roman view at quadrature + observed_phase_deg; v3: phase_colours; v2: sun_swap
SCHEMA_VERSION = 5
