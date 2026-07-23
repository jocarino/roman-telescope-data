"""The planets.json contract, authored once in pydantic. This is the single source of
truth for the emitted data; the web templates consume validated instances of it.

Naming note: instrument views are stored as a LIST (`instrument_views`), never a hard-coded
`roman` key — that is what makes HWO and future missions purely additive.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Provenance = Literal[
    "model",
    "model-microlensing",
    "simulated-cgi",
    "measured-cgi",
    "measured-hwo",
]
ColourMethod = Literal["full-spectrum", "band-reconstruction"]
Confidence = Literal["high", "medium", "low"]


class SpectralCurve(BaseModel):
    grid: str  # GRID_ID
    values: list[float]  # albedo or flux samples on the grid


class PaletteStopModel(BaseModel):
    hex: str
    role: str
    source_nm: float | None = None


class ColourResultModel(BaseModel):
    method: ColourMethod
    hex: str
    srgb: tuple[int, int, int]
    xyz: tuple[float, float, float]
    luminance_y: float
    out_of_gamut: bool
    confidence: Confidence
    palette: list[PaletteStopModel]


class BandSampleModel(BaseModel):
    band_id: str
    center_nm: float
    value: float
    uncertainty: float | None = None


class BandSampleSetModel(BaseModel):
    instrument_id: str
    source: Literal["simulated", "measured"]
    epoch: str | None = None
    samples: list[BandSampleModel]


class ReconstructionModel(BaseModel):
    grid: str
    values: list[float]
    interpolant: str
    extrapolated_below_nm: float
    extrapolated_above_nm: float


class ReconstructionError(BaseModel):
    delta_e2000: float
    note: str


class InstrumentViewModel(BaseModel):
    instrument_id: str
    band_samples: BandSampleSetModel
    reconstruction: ReconstructionModel
    colour: ColourResultModel
    reconstruction_error: ReconstructionError | None = None


class HostStar(BaseModel):
    name: str
    teff_k: float
    spectral_type: str | None = None


class PlanetParams(BaseModel):
    equilibrium_temp_k: float | None = None
    radius_r_earth: float | None = None
    mass_m_earth: float | None = None
    semi_major_axis_au: float | None = None
    # Model assumptions, surfaced for honesty ("modelled, not photographed").
    assumed_cloud_state: str
    assumed_metallicity: float
    assumed_phase_angle_deg: float
    # Which spectrum engine produced the albedo: "parametric" | "cahoy" | "picaso".
    spectrum_source: str = "parametric"


class Discovery(BaseModel):
    method: str
    year: int | None = None
    facility: str | None = None


class RealObservation(BaseModel):
    """A genuine processed telescope image of the planet — a direct-imaging point source,
    never an artist's impression. Present ONLY for the handful of directly-imaged planets;
    everything else has no image of its own (microlensing: none ever; RV/transit: not yet).
    The colour on the page is still modelled — this is the actual, usually infrared, dot."""

    file: str  # path under web/static/, e.g. "obs/hr-8799-b.jpg"
    instrument: str  # "Keck II / NIRC2"
    band: str  # "near-infrared (L′, 3.8 µm)"
    year: int | None = None
    credit: str  # attribution string required by the source
    license: str  # e.g. "CC BY 4.0"
    source_url: str
    note: str  # which point source is the planet; that the light is IR / false-coloured


class RecordMeta(BaseModel):
    generated_at: str
    pipeline_version: str
    schema_version: int


class PlanetRecord(BaseModel):
    id: str
    name: str
    host_star: HostStar
    params: PlanetParams
    discovery: Discovery
    is_light_isolable: bool
    provenance: Provenance
    spectrum: SpectralCurve | None = None
    true_colour: ColourResultModel | None = None
    instrument_views: list[InstrumentViewModel] = Field(default_factory=list)
    real_observation: RealObservation | None = None
    meta: RecordMeta


class PlanetsFile(BaseModel):
    schema_version: int
    grid: str
    generated_at: str
    planets: list[PlanetRecord]
