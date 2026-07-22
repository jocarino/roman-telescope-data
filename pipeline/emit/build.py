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
from pipeline.config import GRID_ID, GRID_NM, Instrument
from pipeline.fetch.targets import load_measured_samples
from pipeline.illuminant.base import Illuminant
from pipeline.models import (
    BandSampleModel,
    BandSampleSetModel,
    ColourResultModel,
    Discovery,
    HostStar,
    InstrumentViewModel,
    PaletteStopModel,
    PlanetParams,
    PlanetRecord,
    ReconstructionError,
    ReconstructionModel,
    RecordMeta,
    SpectralCurve,
)
from pipeline.palette.derive import derive_palette
from pipeline.spectrum.base import SpectrumProvider


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

    views: list[InstrumentViewModel] = []
    for inst in instruments:
        band_set = obtain_band_samples(pin.id, pin.provider, pin.illuminant, inst)
        recon = reconstruct_curve(band_set)
        roman_flux = recon.values * star
        roman_colour = reflected_flux_to_colour(
            roman_flux, method="band-reconstruction", illuminant_flux=star, confidence="low"
        )
        roman_palette = derive_palette(roman_colour)
        de = _delta_e2000(true_colour, roman_colour)
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
                    note="Perceptual distance from the full-spectrum true colour; how much "
                    "colour identity survives this instrument's filters.",
                ),
            )
        )

    provenance = _determine_provenance(pin, views)

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
        instrument_views=views,
        meta=RecordMeta(
            generated_at=generated_at,
            pipeline_version=PIPELINE_VERSION,
            schema_version=SCHEMA_VERSION,
        ),
    )
