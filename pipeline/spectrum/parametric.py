"""Map real planet parameters -> synthetic-albedo knobs via documented physical heuristics.

This is NOT radiative transfer. It is a transparent, honest rule set that places a planet
into a cloud/chemistry regime from its parameters, then hands the resulting albedo to the
same pipeline. It is the v1 stand-in for a real grid (Cahoy 2010) or model (PICASO), both of
which slot in behind SpectrumProvider unchanged.

The knobs vary *continuously* with temperature, surface gravity, and metallicity (rather than
snapping to a handful of fixed buckets), so two planets that differ in mass/size/orbit get
different colours instead of collapsing onto an identical archetype. Everything here is still
an assumption (we hold no per-planet atmosphere data) — but a better-justified, continuous one.

Regime behaviour (still the CLAUDE.md domain background, now as smooth blends):
  - cold ice giants / jovians  -> thick clouds + methane      -> blue-green / cream
  - temperate / warm           -> water/ammonia cloud + haze  -> bright, pale, muted
  - hot                        -> cloud-free, alkali (Na)      -> dark, sodium-blue
  - hot, ~1,600-1,900 K        -> SILICATE cloud returns       -> bright again
  - ultra-hot (above ~1,900 K) -> cloud-free, very dark
  - small rocky                -> grey, moderate-low albedo

Note the fourth line: cloudiness is NOT monotonic in temperature. Different condensates are
stable over different temperature ranges, so the sky clears and then clouds over again as a
planet gets hotter. `_silicate_deck` carries that argument and its sources; it is the one place
to read if you want to know why a 1,700 K planet here can be brighter than a 1,400 K one.

Metallicity follows the observed mass–metallicity relation (Thorngren et al. 2016: smaller
planets are more metal-rich), and feeds the methane/haze knobs, so it actually affects colour
instead of being a cosmetic label.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pipeline.spectrum.synthetic import SyntheticAlbedo

_M_EARTH_PER_M_JUP = 317.8


@dataclass(frozen=True)
class AlbedoModel:
    albedo: SyntheticAlbedo
    cloud_state: str
    # None for rocky worlds (no meaningful atmosphere metallicity).
    assumed_metallicity: float | None
    phase_angle_deg: float


def _sigmoid(x: float, x0: float, w: float) -> float:
    """Smooth 0->1 ramp centred at x0 with width w. Replaces the old hard temperature cuts."""
    return 1.0 / (1.0 + math.exp(-(x - x0) / w))


# --- The silicate-cloud window -----------------------------------------------------------
# Clouds are NOT a monotonically decreasing function of temperature, and modelling them as one
# (which this file did until 2026-08) makes a cloudy hot giant unrepresentable at any parameter
# choice. It is not a tuning error: it puts a real, measured class of planet outside the model's
# reach. Kepler-7 b (T_eq 1,630 K) has a Kepler-band geometric albedo of 0.32 +- 0.03 (Demory
# et al. 2011, ApJL 735, L12, arXiv:1105.5143: "this translates to a Kepler geometric albedo of
# 0.32+-0.03, the most precise value measured so far for an exoplanet"; refined to 0.35 +- 0.02
# by Demory et al. 2013, ApJL 776, L25, arXiv:1309.7894). The monotonic rule gave it 0.11.
#
# The physical reason a cloud exists is not "it is cold enough" but "SOME condensate's
# condensation curve crosses the temperature-pressure profile above the photosphere" — and each
# species does that over its own narrow temperature range. Parmentier et al. 2016 (ApJ 828, 22,
# doi:10.3847/0004-637X/828/1/22, arXiv:1602.03088) works the sequence through for hot Jupiters.
# Its ABSTRACT states the principle — "each cloud species can produce an offset only over a
# narrow range of effective temperatures" — and its CONCLUSION states the observable consequence:
# "We also predict an increase in the planet geometric albedo in the Kepler bandpass for planets
# with an equilibrium temperature between 1600 and 1700 K due to the presence of silicate clouds
# and with an equilibrium temperature around 1200-1300 K due to the presence of manganese sulfide
# clouds". Two separate albedo bumps at two temperatures: an explicit, citable statement that
# albedo is non-monotonic in T_eq.
#
# (Section/quote attribution here has been checked against the paper itself, because it matters
# which sentence carries which claim. Abstract: the "narrow range" principle, the ~1900 K
# reflected/thermal transition, and the partial-cloudiness prediction. Conclusion: the geometric
# albedo bumps and the 1600 K silicate/MnS transition. Section 4.2: the iron/perovskite edge.
# Section 3.1.2: Kepler-7 b and Kepler-8 b.)
#
# What this function encodes, and only this: the SILICATE window, from the same paper.
#   rises 1,600-1,700 K  Abstract: "We suggest that a transition occurs between silicate and
#                         manganese sulfide clouds at a temperature near 1600 K, analogous to the
#                         L/T transition on brown dwarfs", with Table 1 listing "Lack of silicate
#                         clouds for Teq<1600 K" — silicates are the HOTTER side of that
#                         transition. Below it the MgSiO3/Mg2SiO4 condensation curve crosses the
#                         profile under the photosphere ("the cold trapping of cloud species
#                         below the photosphere naturally produces such a transition"), which is
#                         a cold trap, not an absence of silicon. The predicted albedo rise runs
#                         "between 1600 and 1700 K", so the edge is a sigmoid centred at 1,600 K,
#                         width 30 K: half-formed at 1,600, 96% formed by 1,700, matching both.
#                         (An earlier draft of this comment quoted a sentence about silicates
#                         "present ... larger than 1600 K but not ... in cooler planets" that is
#                         NOT in the paper. The wording above is what the paper actually says.)
#   falls 1,800-1,900 K  Section 4.2: "We predict the disappearance of iron and perovskite clouds
#                         between 1800 K and 1900 K"; Conclusion: "We predict that a change from
#                         a reflected to a thermal dominated lightcurve should occur at an
#                         equilibrium temperature of ~1900 K". The closing edge is centred at
#                         1,850 K, width 30 K. THIS IS THE LEAST CONSTRAINED NUMBER HERE: the
#                         paper gives no upper temperature for the silicates themselves, so the
#                         edge is placed where the paper says the optical light stops being
#                         reflected light at all.
#
#   NOT USED, because it could not be checked to the value: the per-species condensation
#   temperatures in Wakeford et al. 2017 (MNRAS 464, 4247, doi:10.1093/mnras/stw2639,
#   arXiv:1610.03325) would be the natural way to place these edges from first principles, but
#   the specific figures a draft of this comment carried (forsterite ~1,592 K, enstatite
#   ~1,508 K at 0.1 bar) were not verified against the paper's own table, so nothing here rests
#   on them. The edges above come from Parmentier 2016 alone.
#
# Amplitude — one calibrated number, and say so. How bright a silicate-clouded planet gets is
# set by two things this model cannot separate: how much of the dayside the deck covers, and how
# reflective the deck is. Both are bounded above — Parmentier 2016 (abstract) predicts "that
# partial cloudiness should be common at the limb and that the dayside hot spot should often be
# cloud-free", and Demory et al. 2013 resolve Kepler-7 b's reflecting region as off-centre, "high
# altitude, optically reflective clouds located west from the substellar point" — but neither is
# separately measured. So the deck is given a
# grey reflectivity of 0.58 (a silicate deck, taken as slightly less reflective than the cold
# ammonia/water deck's 0.62) and the PEAK COVERING FRACTION BELOW IS THE ONE FITTED NUMBER in
# this function, chosen so Kepler-7 b reproduces its measured 0.32. One free parameter against
# one measurement is not a validated model; it is a calibration, and the two other measured
# planets in reach (TrES-2 b, HD 189733 b) are checks on it, not further fits.
#
# Gravity — why two planets in the window differ. Whether the deck reaches the photosphere or
# rains out below it is a competition between sedimentation and vertical mixing (the f_sed
# picture of Ackerman & Marley 2001, ApJ 556, 872, doi:10.1086/321540, which is the cloud model
# Demory et al. 2013 fit to Kepler-7 b). Demory 2013 lists, among the reasons this particular
# planet is cloudy, "very low surface gravity to suppress cloud sedimentation" — Kepler-7 b's
# surface gravity is ~0.4 Earth g. So the window's amplitude is scaled down for high-gravity
# planets, more strongly than the cool deck is.
#
# The one INDEPENDENT check available, i.e. a planet not used to fit anything: Parmentier 2016
# section 3.1.2 concludes "Models with silicate or manganese sulfide clouds can match the albedo
# and phase shift of Kepler-7b and Kepler-8b." Kepler-8 b (T_eq 1,680 K) falls inside the window
# this function draws and comes out cloudy, which is the paper's own verdict on it.
#
# HONEST LIMITS, because they matter more than the fit:
#   - The OBSERVED population trend is contested, and this is the biggest caveat on the whole
#     idea. Heng & Demory 2013 (ApJ 777, 100, doi:10.1088/0004-637X/777/2/100, arXiv:1309.5956)
#     find "the geometric albedo and the incident stellar flux do not exhibit a clear
#     correlation, as revealed by our re-analysis of Q0 to Q14 Kepler data", and expect "any
#     correlation between the geometric albedo and the stellar flux to be weak and characterized
#     by considerable scatter". Adams et al. 2022 (ApJ, doi:10.3847/1538-4357/ac3d32,
#     arXiv:2112.00041) find "a diverse set of geometric albedos for hot Jupiters with
#     equilibrium temperatures between 1550-1700 K" — i.e. real planets scatter across exactly
#     the band this function brightens. So this predicts a population TENDENCY, not any
#     individual planet: real cloudiness depends on the vertical mixing, grain size and
#     metallicity of one atmosphere, none of which we hold for any planet in this catalogue.
#     The gravity term below is the only thing giving two planets at one temperature different
#     answers, and it is a proxy, not a measurement of their clouds.
#   - We do NOT model the manganese-sulfide bump Parmentier also predicts at 1,200-1,300 K. The
#     one planet in that range with a measured optical albedo argues against it being visible in
#     an integrated colour: HD 189733 b (T_eq 1,209 K) is dark and blue, "Ag=0.40+-0.12 across
#     290-450 nm and Ag<0.12 across 450-570 nm" (Evans et al. 2013, ApJL 772, L16,
#     arXiv:1307.3239). Adding a second bump would move most of the warm catalogue on a
#     prediction the only nearby measurement does not support.
#   - Related, and worth stating plainly: Evans 2013 reads HD 189733 b as thick cloud WITH
#     sodium absorption on top of it ("optically thick reflective clouds on the dayside
#     hemisphere with sodium absorption suppressing the scattered light signal beyond ~450 nm").
#     This model gets that planet's colour right for a different reason — it places it in the
#     clear gap between the two cloud windows. A model that could be cloudy AND dark-blue at
#     once needs pressure-broadened alkali wings, which the analytic albedo (a 30 nm Na trough)
#     does not have. Recorded as a known limitation, not fixed here.
#   - The DARK end is still wrong, and this change does not improve it. TrES-2 b's measured
#     Kepler-band albedo is "Ag = 0.0253 +/- 0.0072" (Kipping & Spiegel 2011, MNRAS 417, L88,
#     doi:10.1111/j.1745-3933.2011.01127.x, arXiv:1108.2297), and the same paper notes the true
#     albedo may be "<1%" once thermal emission is accounted for. This model floors out near
#     0.09-0.10 for any cloud-free giant, because `deep_albedo` plus the Rayleigh slope never
#     get darker than that — so the darkest known planet comes out roughly 4x too bright, before
#     and after this change alike. Fixing that is a separate defect in the analytic albedo's
#     floor, not in the cloud rule, and is deliberately not bundled in here.
def _silicate_deck(t: float, grav_hi: float) -> float:
    """Covering fraction of a high silicate cloud deck at equilibrium temperature `t` (K).

    Zero everywhere outside ~1,600-1,900 K, so this term does nothing at all to the cool and
    temperate catalogue: it only re-opens a regime the old rule had closed.
    """
    window = _sigmoid(t, 1600.0, 30.0) * (1.0 - _sigmoid(t, 1850.0, 30.0))
    # 0.76 = the fitted peak covering fraction (see above), cut by up to 45% at high gravity
    # because sedimentation wins there. A 0.4 g planet like Kepler-7 b keeps ~96% of it; a 10 g
    # planet in the same window keeps ~65%, and that is where the model's spread at fixed
    # temperature comes from. Kepler-7 b itself lands at a covering fraction of ~0.53 — a
    # genuinely patchy deck, which is the picture Demory et al. 2013 measured rather than an
    # artefact of the fit.
    return 0.76 * window * (1.0 - 0.45 * grav_hi)


def _metallicity(mass_m_earth: float | None, radius_r_earth: float | None) -> float:
    """Atmospheric metallicity (× solar) from the mass–metallicity relation. Smaller planets
    are more metal-rich; continuous, so it varies planet to planet. Clamped to a sane range.
    Falls back to a radius proxy when mass is unknown (small radius -> Neptune-like, metal-rich)."""
    if mass_m_earth and mass_m_earth > 0:
        m_jup = mass_m_earth / _M_EARTH_PER_M_JUP
        return max(1.0, min(60.0, 9.7 * m_jup**-0.45))
    if radius_r_earth and radius_r_earth > 0:
        return max(1.0, min(60.0, 9.7 * (radius_r_earth / 11.2) ** -0.9))
    return 3.0


def model_for(
    *,
    equilibrium_temp_k: float | None,
    radius_r_earth: float | None,
    mass_m_earth: float | None = None,
    metallicity_override: float | None = None,
) -> AlbedoModel:
    """`metallicity_override` replaces the mass-metallicity relation's value — the knob the
    what-if panel turns (pipeline.modelspace). Ignored for rocky worlds, which carry no
    meaningful atmospheric metallicity. None (the default) = derive it from mass as usual."""
    t = equilibrium_temp_k if equilibrium_temp_k is not None else 300.0
    radius = radius_r_earth if radius_r_earth is not None else 8.0
    z_rel = (
        metallicity_override
        if metallicity_override is not None
        else _metallicity(mass_m_earth, radius_r_earth)
    )

    if radius < 1.6:
        # Rocky: grey, but albedo + Rayleigh drift a little with temperature so terrestrial
        # worlds aren't all one colour. Metallicity is left None — a rocky world has no H/He
        # envelope, so the (giant) mass–metallicity relation is meaningless here and unused.
        cool = _sigmoid(-t, -350, 180)  # 1 for cooler rocky worlds
        return AlbedoModel(
            albedo=SyntheticAlbedo(
                cloud_albedo=0.25, cloud_fraction=0.20 + 0.15 * cool, methane=0.0,
                rayleigh=0.12 + 0.14 * cool, sodium=0.0, deep_albedo=0.10 + 0.05 * cool,
            ),
            cloud_state="rocky / thin atmosphere (grey)",
            assumed_metallicity=None,
            phase_angle_deg=0.0,
        )

    # Continuous giant / sub-Neptune model. Smooth temperature blends:
    hot = _sigmoid(t, 900, 130)     # the cool cloud deck is gone; sodium-bearing hot regime
    warm = _sigmoid(t, 500, 120)    # methane starts dissociating above this
    ice_giant = 2.0 <= radius < 6.0

    # Above this, reflected light is swamped by the planet's own thermal emission: Parmentier
    # et al. 2016 (ApJ 828, 22, arXiv:1602.03088) "predict that a change from a reflected to a
    # thermal dominated lightcurve should occur at an equilibrium temperature of ~1900 K". We
    # model reflected light only, so this is where the reflected continuum is dark and stays
    # dark. (This centre was 1600 K before, which was unsourced and put the darkest regime on
    # top of the silicate-cloud window below.)
    ultra = _sigmoid(t, 1900, 130)

    # Surface gravity in Earth g's; high gravity compresses the atmosphere -> thinner clouds.
    gravity = (mass_m_earth / radius**2) if (mass_m_earth and radius) else 1.5
    grav_hi = _sigmoid(math.log10(max(gravity, 0.1)), 0.5, 0.4)

    z_factor = min(1.8, (z_rel / 9.7) ** 0.35)  # metallicity's pull on methane / haze depth

    silicate = _silicate_deck(t, grav_hi)
    # The two decks are different condensates stable in different temperature ranges and never
    # coexist, so take whichever one is available rather than adding them. `max` of two smooth
    # curves that never overlap is itself smooth here (the cool deck is ~0.003 at 1,450 K,
    # where the silicate deck is still ~0.001).
    cool_deck = 0.9 * (1.0 - hot) * (1.0 - 0.25 * grav_hi)
    cloud_fraction = max(cool_deck, silicate)
    silicate_frac = silicate / cloud_fraction if cloud_fraction > 1e-6 else 0.0

    # Cloud-deck reflectivity, by which condensate is doing the work. Silicate grains scatter
    # efficiently in the optical but the deck is thinner and patchier than a cold ammonia/water
    # deck, so it is given a slightly lower grey reflectivity than the cool deck's 0.62. With
    # no condensate at all the number is nearly inert (it is weighted by `cloud_fraction`).
    cloud_albedo = (
        0.62 * (1.0 - hot) + 0.22 * hot
    ) * (1.0 - silicate_frac) + 0.58 * silicate_frac
    methane = (1.4 if ice_giant else 0.5) * (1.0 - warm) * z_factor
    # A silicate deck sits ABOVE the alkali it would otherwise show through: Demory et al. 2013
    # describe Kepler-7 b's as "high altitude, optically reflective clouds", so the fraction of
    # the disc it covers is a fraction where the sodium trough is hidden. Only the silicate deck
    # does this — the cool deck's effect on sodium is left exactly as it was, so nothing below
    # ~1,500 K moves because of this line.
    #
    # NOT a general rule, and the counter-example is the best-measured planet of the three:
    # Evans et al. 2013 read HD 189733 b as thick cloud WITH sodium absorption on top of it,
    # "optically thick reflective clouds on the dayside hemisphere with sodium absorption
    # suppressing the scattered light signal beyond ~450 nm". Whether the alkali sits above or
    # below the deck is a per-planet fact we do not hold for any planet in this catalogue.
    sodium = 0.9 * hot * (1.0 - silicate)
    rayleigh = 0.35 + 0.35 * (1.0 - cloud_fraction) + 0.15 * (z_factor - 0.7)
    deep_albedo = 0.09 * (1.0 - hot) + 0.04 * hot - 0.02 * ultra

    if silicate_frac > 0.5 and cloud_fraction > 0.15:
        label = "hot, reflective silicate cloud"
    elif ultra > 0.5:
        label = "ultra-hot, cloud-free, very dark"
    elif hot > 0.5:
        label = "hot, cloud-free, alkali (sodium) absorption"
    elif t < 220:
        label = "cold, thick clouds + methane" + (" (ice giant)" if ice_giant else "")
    else:
        label = "temperate / warm, partial cloud + haze"

    return AlbedoModel(
        albedo=SyntheticAlbedo(
            cloud_albedo=cloud_albedo, cloud_fraction=max(0.0, cloud_fraction),
            methane=max(0.0, methane), rayleigh=max(0.1, rayleigh), sodium=sodium,
            deep_albedo=max(0.02, deep_albedo),
        ),
        cloud_state=label,
        assumed_metallicity=round(z_rel, 1),
        phase_angle_deg=0.0,
    )
