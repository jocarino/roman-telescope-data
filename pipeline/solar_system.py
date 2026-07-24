"""The solar system anchors: Jupiter, Saturn, Uranus, Neptune, Earth.

These five run through the exact same pipeline as every exoplanet — but their albedo
spectra are MEASURED (Karkoschka 1998 for the giants, the Payne et al. 2026 calibrated
composite for Earth; see data/measured_albedo/README.md), and each has a real photograph
on its page. They are the Rosetta stones of the dataset: the one place a visitor can watch
the spectrum → colour conversion reproduce a planet whose true colour everyone knows, and
the anchor that makes an exoplanet swatch legible ("Neptune-ish, and I know Neptune").

Parameters are NASA planetary fact-sheet values, not Exoplanet Archive fetches — the
solar system is not in the Archive. Every parameter is a measurement, so all sources are
"measured"; the atmosphere fields that are archetype guesses for exoplanets are here the
real observed atmosphere. Metallicity is still recorded (it selects the nearest Cahoy
archetype for phase-angle behaviour) using each planet's measured atmospheric enrichment.
"""

from __future__ import annotations

from pipeline.emit.build import PlanetInput
from pipeline.illuminant.blackbody import SUN
from pipeline.models import Discovery, HostStar, ParamSources, PlanetParams
from pipeline.spectrum.base import ProviderUnavailable, SpectrumProvider
from pipeline.spectrum.measured import karkoschka1998, payne2026_earth

_AU_TO_PC = 1.0 / 206264.806

_SUN = HostStar(name="Sun", teff_k=SUN.teff_k, spectral_type="G2 V")

# Every number below is measured, and the "assumed" atmosphere fields are the real observed
# atmosphere — record them as such so the page's origin chips say the honest thing.
_ALL_MEASURED = ParamSources(
    equilibrium_temp_k="measured",
    radius_r_earth="measured",
    mass_m_earth="measured",
    semi_major_axis_au="measured",
    distance_pc="measured",
    star_teff_k="measured",
    metallicity="measured",
    cloud_state="measured",
    phase_angle_deg="measured",
)


def _params(
    *,
    eq_temp_k: float,
    radius_r_earth: float,
    mass_m_earth: float,
    sma_au: float,
    metallicity: float | None,
    phase_deg: float,
    spectrum_source: str,
) -> PlanetParams:
    return PlanetParams(
        equilibrium_temp_k=eq_temp_k,
        radius_r_earth=radius_r_earth,
        mass_m_earth=mass_m_earth,
        semi_major_axis_au=sma_au,
        # Mean distance from Earth ~ the planet's own orbital radius (0 for Earth itself).
        distance_pc=sma_au * _AU_TO_PC if sma_au != 1.0 else 0.0,
        assumed_cloud_state="as observed",
        assumed_metallicity=metallicity,
        assumed_phase_angle_deg=phase_deg,
        spectrum_source=spectrum_source,
        sources=_ALL_MEASURED,
    )


def _spec(builder, *args) -> SpectrumProvider | None:
    """Build a measured provider, or None if its data file is absent (planet is skipped)."""
    try:
        return builder(*args)
    except ProviderUnavailable as exc:
        print(f"Solar system: skipping ({exc})")
        return None


def solar_system_planets() -> list[PlanetInput]:
    """The five anchors, inner to outer. Phase angles are the observation geometry of the
    measured spectra (Karkoschka's Jupiter/Saturn were caught at 6.8°/5.7°; Uranus/Neptune
    and Earth's composite are true geometric, 0°). Metallicities are the measured
    atmospheric enrichments (~3x solar for Jupiter, ~10x Saturn, ~30-80x ice giants),
    which double as the nearest-Cahoy-archetype key for phase behaviour."""
    entries = [
        (
            "earth",
            "Earth",
            _spec(payne2026_earth),
            _params(
                eq_temp_k=255.0, radius_r_earth=1.0, mass_m_earth=1.0, sma_au=1.0,
                metallicity=None, phase_deg=0.0, spectrum_source="payne2026",
            ),
            Discovery(method="Home planet", year=None, facility=None),
        ),
        (
            "jupiter",
            "Jupiter",
            _spec(karkoschka1998, "jupiter"),
            _params(
                eq_temp_k=110.0, radius_r_earth=11.209, mass_m_earth=317.83, sma_au=5.204,
                metallicity=3.0, phase_deg=6.8, spectrum_source="karkoschka1998",
            ),
            Discovery(method="Known since antiquity", year=None, facility=None),
        ),
        (
            "saturn",
            "Saturn",
            _spec(karkoschka1998, "saturn"),
            _params(
                eq_temp_k=81.0, radius_r_earth=9.449, mass_m_earth=95.16, sma_au=9.573,
                metallicity=10.0, phase_deg=5.7, spectrum_source="karkoschka1998",
            ),
            Discovery(method="Known since antiquity", year=None, facility=None),
        ),
        (
            "uranus",
            "Uranus",
            _spec(karkoschka1998, "uranus"),
            _params(
                eq_temp_k=58.0, radius_r_earth=4.007, mass_m_earth=14.54, sma_au=19.165,
                metallicity=30.0, phase_deg=0.0, spectrum_source="karkoschka1998",
            ),
            Discovery(method="Telescope", year=1781, facility="W. Herschel"),
        ),
        (
            "neptune",
            "Neptune",
            _spec(karkoschka1998, "neptune"),
            _params(
                eq_temp_k=47.0, radius_r_earth=3.883, mass_m_earth=17.15, sma_au=30.178,
                metallicity=30.0, phase_deg=0.0, spectrum_source="karkoschka1998",
            ),
            Discovery(method="Telescope", year=1846, facility="Berlin Observatory"),
        ),
    ]
    return [
        PlanetInput(
            id=pid,
            name=name,
            host_star=_SUN,
            params=params,
            discovery=discovery,
            provider=provider,
            illuminant=SUN,
            is_light_isolable=True,
            is_cgi_target=False,
            has_measured_albedo=True,
        )
        for pid, name, provider, params, discovery in entries
        if provider is not None
    ]
