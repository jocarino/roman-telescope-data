"""Milestone-1 hard-coded demo planets: three archetypes that exercise the sanity gate.
These use the synthetic albedo provider and a blackbody Sun illuminant. Batch mode
(Milestone 2) will replace these with real Exoplanet Archive parameters.
"""

from __future__ import annotations

from pipeline.emit.build import PlanetInput
from pipeline.illuminant.blackbody import SUN
from pipeline.models import Discovery, HostStar, PlanetParams
from pipeline.spectrum.synthetic import (
    CLOUDFREE_HOT_JUPITER,
    CLOUDY_JUPITER,
    METHANE_NEPTUNE,
)

_SUN_STAR = HostStar(name="Sun (analog)", teff_k=5772.0, spectral_type="G2V")


def demo_planets() -> list[PlanetInput]:
    return [
        PlanetInput(
            id="cloudy-jupiter-analog",
            name="Cloudy Jupiter analog",
            host_star=_SUN_STAR,
            params=PlanetParams(
                equilibrium_temp_k=110.0,
                radius_r_earth=11.2,
                mass_m_earth=317.8,
                semi_major_axis_au=5.2,
                assumed_cloud_state="cloudy (ammonia deck)",
                assumed_metallicity=1.0,
                assumed_phase_angle_deg=0.0,
            ),
            discovery=Discovery(method="Imaging", year=None, facility="synthetic"),
            provider=CLOUDY_JUPITER,
            illuminant=SUN,
        ),
        PlanetInput(
            id="methane-neptune-analog",
            name="Methane Neptune analog",
            host_star=_SUN_STAR,
            params=PlanetParams(
                equilibrium_temp_k=72.0,
                radius_r_earth=3.9,
                mass_m_earth=17.1,
                semi_major_axis_au=30.0,
                assumed_cloud_state="deep methane, thin cloud",
                assumed_metallicity=10.0,
                assumed_phase_angle_deg=0.0,
            ),
            discovery=Discovery(method="Imaging", year=None, facility="synthetic"),
            provider=METHANE_NEPTUNE,
            illuminant=SUN,
        ),
        PlanetInput(
            id="cloudfree-hot-jupiter-analog",
            name="Cloud-free hot Jupiter analog",
            host_star=_SUN_STAR,
            params=PlanetParams(
                equilibrium_temp_k=1200.0,
                radius_r_earth=12.0,
                mass_m_earth=360.0,
                semi_major_axis_au=0.03,
                assumed_cloud_state="cloud-free, sodium-bearing",
                assumed_metallicity=1.0,
                assumed_phase_angle_deg=0.0,
            ),
            discovery=Discovery(method="Transit", year=None, facility="synthetic"),
            provider=CLOUDFREE_HOT_JUPITER,
            illuminant=SUN,
        ),
    ]
