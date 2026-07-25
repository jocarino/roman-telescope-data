"""Convergence: assemble one PlanetRecord. The swap seam (`obtain_band_samples`) lives
here — everything after it (reconstruct -> cie -> palette) is byte-identical whether the
four band values were simulated from the model or measured by Roman.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from colour import XYZ_to_Lab, delta_E

from pipeline.bands.integrate import BandSampleSet, simulate_band_samples
from pipeline.bands.reconstruct import reconstruct_curve
from pipeline.colour.cie import ColourResult, reflected_flux_to_colour
from pipeline.config import CGI_OBSERVATION_PHASE_DEG, GRID_ID, GRID_NM, Instrument
from pipeline.fetch.targets import load_measured_samples
from pipeline.habitable import assess as assess_habitability
from pipeline.illuminant.base import Illuminant
from pipeline.illuminant.blackbody import SUN
from pipeline.models import (
    BandSampleModel,
    BandSampleSetModel,
    ColourResultModel,
    Discovery,
    Habitability,
    HostStar,
    IlluminantSwapModel,
    InstrumentViewModel,
    PaletteStopModel,
    PhaseColourModel,
    PhaseSetModel,
    PlanetParams,
    PlanetRecord,
    ReconstructionError,
    ReconstructionModel,
    RecordMeta,
    SkyPosition,
    SpectralCurve,
)
from pipeline.observations import observations_for
from pipeline.palette.derive import derive_palette
from pipeline.spectrum.base import SpectrumProvider
from pipeline.spectrum.phase import PHASE_ANGLES_DEG, PhasedAlbedo


@dataclass(frozen=True)
class PlanetInput:
    id: str
    name: str
    host_star: HostStar
    params: PlanetParams
    discovery: Discovery
    provider: SpectrumProvider
    illuminant: Illuminant
    is_light_isolable: bool = True
    is_cgi_target: bool = False
    sky: SkyPosition | None = None
    # Solar system anchors: the provider holds a real measured albedo spectrum, not a model.
    has_measured_albedo: bool = False


def obtain_band_samples(
    planet_id: str,
    provider: SpectrumProvider,
    illuminant: Illuminant,
    instrument: Instrument,
) -> BandSampleSet:
    """THE SEAM. Prefer real measured photometry if a file exists; otherwise simulate from
    the model. Nothing downstream reads `.source` except a provenance badge."""
    measured = load_measured_samples(planet_id, instrument)
    if measured is not None:
        return measured
    return simulate_band_samples(provider, illuminant, instrument)


def _colour_to_model(colour: ColourResult, palette_stops) -> ColourResultModel:
    return ColourResultModel(
        method=colour.method,
        hex=colour.hex,
        srgb=colour.srgb,
        xyz=colour.xyz,
        luminance_y=colour.luminance_y,
        out_of_gamut=colour.out_of_gamut,
        confidence=colour.confidence,
        palette=[
            PaletteStopModel(hex=s.hex, role=s.role, source_nm=s.source_nm) for s in palette_stops
        ],
    )


def _delta_e2000(a: ColourResult, b: ColourResult) -> float:
    lab_a = XYZ_to_Lab(np.array(a.xyz))
    lab_b = XYZ_to_Lab(np.array(b.xyz))
    return float(delta_E(lab_a, lab_b, method="CIE 2000"))


def _determine_provenance(pin: PlanetInput, views: list[InstrumentViewModel]) -> str:
    if any(v.band_samples.source == "measured" for v in views):
        return "measured-cgi"
    if pin.has_measured_albedo:
        return "measured-albedo"
    if not pin.is_light_isolable:
        return "model-microlensing"
    if pin.is_cgi_target:
        return "simulated-cgi"
    return "model"


def build_record(
    pin: PlanetInput, instruments: list[Instrument], generated_at: str
) -> PlanetRecord:
    from pipeline.config import PIPELINE_VERSION, SCHEMA_VERSION

    star = pin.illuminant.spectrum(GRID_NM)
    albedo = pin.provider.geometric_albedo(GRID_NM)
    flux = albedo * star

    true_colour = reflected_flux_to_colour(
        flux, method="full-spectrum", illuminant_flux=star, confidence="high"
    )
    true_palette = derive_palette(true_colour)

    # Illuminant swap: the same albedo under the Sun. Same pipeline, different S(lambda) —
    # isolates the planet's own contribution to its colour from its host star's tint.
    sun_spectrum = SUN.spectrum(GRID_NM)
    sun_colour = reflected_flux_to_colour(
        albedo * sun_spectrum, method="full-spectrum", illuminant_flux=sun_spectrum,
        confidence="high",
    )
    sun_swap = IlluminantSwapModel(
        illuminant=f"sun-blackbody-{SUN.teff_k:.0f}k",
        teff_k=SUN.teff_k,
        colour=_colour_to_model(sun_colour, derive_palette(sun_colour)),
        delta_e2000_vs_true=_delta_e2000(true_colour, sun_colour),
    )

    # Phase-resolved colours (the phase slider): A(λ, α) under the planet's own star,
    # 0-180° in 10° steps. hex = colour identity at that phase; luminance_y = true
    # relative brightness including the phase dimming (0° ≈ base, 180° → 0).
    phased = PhasedAlbedo(
        pin.provider,
        semi_major_axis_au=pin.params.semi_major_axis_au,
        metallicity=pin.params.assumed_metallicity,
    )
    phase_stops = []
    for deg in PHASE_ANGLES_DEG:
        p_flux = phased(GRID_NM, float(deg)) * star
        p_colour = reflected_flux_to_colour(
            p_flux, method="full-spectrum", illuminant_flux=star, confidence="high"
        )
        phase_stops.append(
            PhaseColourModel(
                phase_deg=deg, hex=p_colour.hex, luminance_y=round(p_colour.luminance_y, 5)
            )
        )
    phase_colours = PhaseSetModel(source=phased.source, colours=phase_stops)

    # Instrument views are simulated at QUADRATURE (half-lit) — the geometry a coronagraph
    # actually observes; a fully-lit planet sits behind its star. The delta-E compares the
    # band-reconstructed colour against the full spectrum at the SAME phase, so it isolates
    # what the filter set loses rather than mixing in the phase difference.
    quad_deg = CGI_OBSERVATION_PHASE_DEG
    quad_provider = phased.at(quad_deg)
    quad_colour = reflected_flux_to_colour(
        phased(GRID_NM, quad_deg) * star, method="full-spectrum", illuminant_flux=star,
        confidence="high",
    )
    views: list[InstrumentViewModel] = []
    for inst in instruments:
        band_set = obtain_band_samples(pin.id, quad_provider, pin.illuminant, inst)
        recon = reconstruct_curve(band_set)
        roman_flux = recon.values * star
        roman_colour = reflected_flux_to_colour(
            roman_flux, method="band-reconstruction", illuminant_flux=star, confidence="low"
        )
        roman_palette = derive_palette(roman_colour)
        de = _delta_e2000(quad_colour, roman_colour)
        views.append(
            InstrumentViewModel(
                instrument_id=inst.id,
                band_samples=BandSampleSetModel(
                    instrument_id=band_set.instrument_id,
                    source=band_set.source,
                    epoch=band_set.epoch,
                    samples=[
                        BandSampleModel(
                            band_id=s.band_id,
                            center_nm=s.center_nm,
                            value=s.value,
                            uncertainty=s.uncertainty,
                        )
                        for s in band_set.samples
                    ],
                ),
                reconstruction=ReconstructionModel(
                    grid=recon.grid_id,
                    values=[float(v) for v in recon.values],
                    interpolant=recon.interpolant,
                    extrapolated_below_nm=recon.extrapolated_below_nm,
                    extrapolated_above_nm=recon.extrapolated_above_nm,
                ),
                colour=_colour_to_model(roman_colour, roman_palette),
                reconstruction_error=ReconstructionError(
                    delta_e2000=de,
                    note="Perceptual distance from the full spectrum at the same (quadrature) "
                    "phase; how much colour identity survives this instrument's filters.",
                ),
                observed_phase_deg=quad_deg if band_set.source == "simulated" else None,
            )
        )

    provenance = _determine_provenance(pin, views)

    # Habitable-zone lens. Independent of the colour pipeline — it reads only the measured
    # star and orbit, so it stays correct regardless of which spectrum engine ran above.
    hab = assess_habitability(
        teff_k=pin.host_star.teff_k,
        star_radius_r_sun=pin.host_star.radius_r_sun,
        semi_major_axis_au=pin.params.semi_major_axis_au,
        radius_r_earth=pin.params.radius_r_earth,
        mass_m_earth=pin.params.mass_m_earth,
        eccentricity=pin.params.eccentricity,
        axis_source=pin.params.sources.semi_major_axis_au if pin.params.sources else None,
    )
    habitability = Habitability(
        zone=hab.zone,  # type: ignore[arg-type]
        surface=hab.surface,  # type: ignore[arg-type]
        insolation_earth=hab.insolation_earth,
        inner_au=hab.inner_au,
        outer_au=hab.outer_au,
        optimistic_inner_au=hab.optimistic_inner_au,
        optimistic_outer_au=hab.optimistic_outer_au,
        extrapolated=hab.extrapolated,
        is_candidate=hab.is_candidate,
        caveats=hab.caveats,
    )

    return PlanetRecord(
        id=pin.id,
        name=pin.name,
        host_star=pin.host_star,
        params=pin.params,
        discovery=pin.discovery,
        is_light_isolable=pin.is_light_isolable,
        provenance=provenance,  # type: ignore[arg-type]
        spectrum=SpectralCurve(grid=GRID_ID, values=[float(a) for a in albedo]),
        true_colour=_colour_to_model(true_colour, true_palette),
        sun_swap=sun_swap,
        phase_colours=phase_colours,
        instrument_views=views,
        real_observations=observations_for(pin.id),
        sky=pin.sky,
        habitability=habitability,
        meta=RecordMeta(
            generated_at=generated_at,
            pipeline_version=PIPELINE_VERSION,
            schema_version=SCHEMA_VERSION,
        ),
    )
