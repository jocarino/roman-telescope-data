"""Global constants: the CIE wavelength grid, the instrument (bandpass) registry, and
the brightness convention. These are data, not behaviour — keeping them in one place is
what lets the rest of the pipeline stay source-agnostic and future-mission-additive.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
# band-integration or reconstruction code is hard-coded to four bands.


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


# Roman Coronagraph (CGI): imaging/polarimetry at 575 nm (10%) and 835 nm (15%);
# slit spectroscopy at 660 nm and 730 nm (6% each). Modelled as top-hats for v1.
ROMAN_CGI = Instrument(
    id="roman-cgi",
    name="Roman Coronagraph",
    mission="Roman",
    bands=(
        Bandpass("cgi-575", 575.0, 0.10, "tophat", "imaging"),
        Bandpass("cgi-660", 660.0, 0.06, "tophat", "spectroscopy"),
        Bandpass("cgi-730", 730.0, 0.06, "tophat", "spectroscopy"),
        Bandpass("cgi-835", 835.0, 0.15, "tophat", "imaging"),
    ),
)

INSTRUMENTS: dict[str, Instrument] = {ROMAN_CGI.id: ROMAN_CGI}

PIPELINE_VERSION = "0.1.0"
SCHEMA_VERSION = 1
