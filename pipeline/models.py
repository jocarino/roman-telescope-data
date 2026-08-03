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
    # Solar system anchors: the albedo spectrum is a real measurement (Karkoschka 1998 /
    # Payne et al. 2026), only the solar illuminant is modelled. The one provenance whose
    # colour can be checked against an actual photograph.
    "measured-albedo",
]
ColourMethod = Literal["full-spectrum", "band-reconstruction"]
Confidence = Literal["high", "medium", "low"]

# Where a single modelling parameter's value came from. This is NOT a quality score — it just
# states, honestly and per-field, whether we used a real measurement, derived the value from
# other measurements, or fell back to an archetype assumption because no data exists.
DataSource = Literal["measured", "computed", "assumed"]

# Habitable-zone classification (pipeline.habitable). "conservative" and "optimistic" are the
# two standard zone widths in the literature, not a confidence rating.
HabitableZoneClass = Literal["conservative", "optimistic", "too-hot", "too-cold", "unknown"]
# Whether there is a solid surface for an ocean to sit on, from the planet's size alone.
SurfaceClass = Literal["rocky", "uncertain", "enveloped", "unknown"]


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
    # Phase angle the simulated view is computed at (quadrature for a coronagraph — it can
    # never see full phase). None for measured data, whose phase is whatever Roman caught.
    observed_phase_deg: float | None = None


class PhaseColourModel(BaseModel):
    """The planet's colour at one orbital phase angle. `hex` is the colour identity
    (chromaticity at the display luminance); `luminance_y` is the true relative brightness
    including the phase dimming, so 0° ≈ the base luminance and 180° → 0."""

    phase_deg: int
    hex: str
    luminance_y: float


class PhaseSetModel(BaseModel):
    """Phase-resolved colours for the phase slider / animation, 0-180° in 10° steps.
    `source` states where the phase behaviour comes from: "cahoy-grid" (the planet's own
    spectra are phase-resolved), "cahoy-ratio" (phase bending borrowed from the nearest
    Cahoy archetype), or "lambert-grey" (brightness dims, colour held constant)."""

    source: Literal["cahoy-grid", "cahoy-ratio", "lambert-grey"]
    colours: list[PhaseColourModel]


class IlluminantSwapModel(BaseModel):
    """The same albedo spectrum re-lit by a reference star — "this planet around the Sun".
    Separates what the PLANET contributes to its colour from what its host star's light
    contributes. `delta_e2000_vs_true` is the perceptual distance from the native colour:
    ~0 for Sun-like hosts, large for M-dwarf planets whose colour is mostly their star."""

    illuminant: str  # e.g. "sun-blackbody-5772k"
    teff_k: float
    colour: ColourResultModel
    delta_e2000_vs_true: float


class HostStar(BaseModel):
    name: str
    teff_k: float
    spectral_type: str | None = None
    # Stellar radius (solar radii) and the luminosity derived from it via Stefan-Boltzmann.
    # Luminosity is what sets the habitable zone; both are optional because the Archive does
    # not have a radius for every host. Absent in pre-v5 releases.
    radius_r_sun: float | None = None
    luminosity_lsun: float | None = None


class SkyPosition(BaseModel):
    """Where the host star sits in Earth's sky (J2000), for the "go outside and look at
    it" star chart. `naked_eye` uses the conventional dark-sky limit (V ≤ 6.5) — honest
    wording on the page must say "under a dark sky", never promise city visibility. What
    you would see is always the host STAR; the planet itself is never visible."""

    ra_deg: float
    dec_deg: float
    constellation: str  # full IAU name, e.g. "Pegasus"
    constellation_abbr: str  # 3-letter IAU code, e.g. "Peg"
    v_mag: float | None = None  # system V magnitude (Archive sy_vmag); None if unmeasured
    naked_eye: bool = False


class ParamSources(BaseModel):
    """Per-parameter data origin, so the page can show exactly which numbers are real
    measurements, which we computed from other measurements, and which are archetype
    assumptions. Cloud state / metallicity / phase are always assumed (we hold no per-planet
    atmosphere data); the rest are 'measured' when the Archive has them."""

    equilibrium_temp_k: DataSource = "assumed"
    radius_r_earth: DataSource = "assumed"
    mass_m_earth: DataSource = "assumed"
    semi_major_axis_au: DataSource = "assumed"
    distance_pc: DataSource = "assumed"
    star_teff_k: DataSource = "assumed"
    metallicity: DataSource = "assumed"
    cloud_state: DataSource = "assumed"
    phase_angle_deg: DataSource = "assumed"


class PlanetParams(BaseModel):
    equilibrium_temp_k: float | None = None
    radius_r_earth: float | None = None
    mass_m_earth: float | None = None
    semi_major_axis_au: float | None = None
    eccentricity: float | None = None  # orbital eccentricity; 0 = circular
    distance_pc: float | None = None  # distance from Earth, parsecs
    # Model assumptions, surfaced for honesty ("modelled, not photographed").
    assumed_cloud_state: str
    assumed_metallicity: float | None = None  # None for rocky worlds (no meaningful metallicity)
    assumed_phase_angle_deg: float
    # Which spectrum engine produced the albedo: "parametric" | "cahoy" | "picaso".
    spectrum_source: str = "parametric"
    # Per-field data origin (measured / computed / assumed). Optional for back-compat.
    sources: ParamSources | None = None


class Discovery(BaseModel):
    method: str
    year: int | None = None
    facility: str | None = None


class RealObservation(BaseModel):
    """A genuine processed image of the planet — never an artist's impression. Present only
    for the handful of directly-imaged exoplanets (infrared point-source dots; the page
    colour is still modelled) and the solar system anchors (real visible-light spacecraft
    photographs — the ground truth for the measured-albedo swatch). Everything else has no
    image of its own (microlensing: none ever; RV/transit: not yet)."""

    telescope: str  # short selector tag: "JWST", "Roman", "VLT", "Subaru"
    file: str  # path under web/static/, e.g. "obs/hr-8799-b.jpg"
    instrument: str  # "Keck II / NIRC2"
    band: str  # "near-infrared (L′, 3.8 µm)"
    year: int | None = None
    credit: str  # attribution string required by the source
    license: str  # e.g. "CC BY 4.0"
    source_url: str
    note: str  # which point source is the planet; that the light is IR / false-coloured


class SystemSibling(BaseModel):
    """Another planet orbiting the same host star, for the "same system" neighbourhood links."""

    id: str
    name: str
    letter: str | None = None  # the planet letter (b, c, d, …), if the name carries one
    semi_major_axis_au: float | None = None
    base_hex: str | None = None  # the sibling's full-spectrum colour, for its swatch


class PlanetSystem(BaseModel):
    """The planet's stellar neighbourhood: every OTHER planet of the same host star that is
    present in this dataset, sorted inner → outer. `member_count` counts the whole system as
    we have it (this planet + its siblings). Grouped purely by shared host — never by sky
    proximity, which mixes unrelated stars at different distances."""

    hostname: str
    member_count: int  # planets of this host in our data, including this one
    siblings: list[SystemSibling] = Field(default_factory=list)


class Habitability(BaseModel):
    """Where the orbit sits relative to the star's liquid-water zone (pipeline.habitable).

    Orbital geography, not a habitability claim: it follows from the host star's temperature
    and radius and the planet's orbital distance, and says nothing about an atmosphere — none
    has been measured for any of these planets. `caveats` carries the plain-English limits of
    this particular verdict and the UI must show them wherever the badge appears.
    """

    zone: HabitableZoneClass
    surface: SurfaceClass
    insolation_earth: float | None = None  # starlight received, Earth = 1
    inner_au: float | None = None  # conservative inner edge (runaway greenhouse)
    outer_au: float | None = None  # conservative outer edge (maximum greenhouse)
    optimistic_inner_au: float | None = None  # recent Venus
    optimistic_outer_au: float | None = None  # early Mars
    # True when the host is outside the 2,600-7,200 K range the climate models cover.
    extrapolated: bool = False
    # The badge case: in the zone AND plausibly has a surface for an ocean to sit on.
    is_candidate: bool = False
    caveats: list[str] = Field(default_factory=list)


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
    # Stretch-goal data (milestone 6): the planet re-lit by the Sun, for the host-star
    # illuminant comparison. Optional for back-compat with schema-v1 records.
    sun_swap: IlluminantSwapModel | None = None
    # Phase-resolved colours (0-180° in 10° steps) for the phase slider / animation.
    phase_colours: PhaseSetModel | None = None
    instrument_views: list[InstrumentViewModel] = Field(default_factory=list)
    # Zero or more genuine telescope images (JWST, Roman, VLT, …), each additive — a new
    # instrument's image is appended, never substituted. The UI shows a per-telescope toggle.
    real_observations: list[RealObservation] = Field(default_factory=list)
    system: PlanetSystem | None = None
    # Optional for back-compat: data releases generated before the sky chart lack it.
    sky: SkyPosition | None = None
    # Habitable-zone lens. Optional for back-compat with pre-v5 releases.
    habitability: Habitability | None = None
    meta: RecordMeta


class BandpassHeader(BaseModel):
    """One bandpass as emitted in the file header, so the file says which filter set produced
    its `instrument_views` instead of leaving a reader to infer it from band ids."""

    id: str
    center_nm: float
    bandwidth_frac: float
    lo_nm: float
    hi_nm: float
    shape: str
    role: str


class InstrumentHeader(BaseModel):
    id: str
    name: str
    mission: str
    bands: list[BandpassHeader]


class PlanetsFile(BaseModel):
    schema_version: int
    grid: str
    generated_at: str
    # Why this is here: on 2026-08-03 the CGI band set was corrected from four bands to the
    # flight three. The record SHAPE did not change, so schema_version stayed at 5 -- and a
    # consumer pinned to v5 silently began receiving cgi-825 where it had been getting
    # cgi-660 and cgi-835, with every instrument_views colour and delta_e2000 different.
    # A version number cannot express that; the band set itself can. Emitting it makes the
    # file self-describing, so two releases can be told apart without reading a changelog.
    instruments: list[InstrumentHeader] = Field(default_factory=list)
    # Rights and sources travel INSIDE the file. A licence stated only in a repo README is a
    # licence nobody who downloaded the JSON ever sees, and the Archive acknowledgement we owe
    # is inherited by anything built on this data. See pipeline/rights.py.
    rights: dict = Field(default_factory=dict)
    planets: list[PlanetRecord]
