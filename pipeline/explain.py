"""Why is *this* planet *that* colour — derived from its own spectrum, not written by hand.

The one sentence of physics is the only part of a post with any value, and it is also the part
nobody has time to reconstruct at 23:40. But it does not need reconstructing: the colour came
out of a deterministic pipeline, so the reason is already in the record. This reads it back.

Two inputs, both already in `planets.json`:

  * the albedo spectrum itself — 81 points over 380–780 nm. Which band is depressed IS the
    mechanism. Methane eats the red; sodium eats the yellow-orange; Rayleigh lifts the blue;
    thick cloud raises everything and flattens it toward white.
  * the regime label the parametric engine assigned (`assumed_cloud_state`), which names the
    chemistry it placed the planet in.

Both are stated, so every claim here is checkable — against the spectrum plot on the planet
page, and against `pipeline/spectrum/parametric.py` where the regimes are defined. That is
the point. This is a cheat sheet you verify, not a caption you paste: it explains what our
model did, which is a claim about our model, not a measurement of the planet.

Stdlib only (plain arithmetic over the 81 floats), so `tools/newswatch.py` can import it
without breaking its no-dependency guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass

GRID_LO_NM = 380.0
GRID_STEP_NM = 5.0

# Bands chosen to line up with what the eye does, and with where the absorbers actually sit:
# methane's strong visible bands are in the red, sodium's D lines at 589 nm, Rayleigh rises
# steeply toward the blue end.
BANDS = (("blue", 380.0, 500.0), ("green", 500.0, 590.0), ("red", 590.0, 780.0))

# How far from flat a spectrum has to tilt before the tilt is the story rather than noise.
TILT_STRONG = 0.60      # red/blue below this: the red end is being eaten
TILT_MILD = 0.85
TILT_RED = 1.20         # red/blue above this: the blue end is being eaten
BRIGHT = 0.35           # mean geometric albedo above this reads as a bright, cloudy world
DARK = 0.12             # below this the planet reflects almost nothing


@dataclass(frozen=True)
class Physics:
    """One explanation, split so a caller can use as much of it as it has room for."""

    mechanism: str            # the sentence — what is happening to the light
    evidence: str             # the numbers behind it, checkable against the spectrum plot
    illuminant: str           # what the host star contributes
    caveat: str               # which engine, and what was assumed rather than measured
    contradiction: str | None = None   # our own spectrum disagrees with our own regime

    def one_line(self) -> str:
        return self.mechanism

    def lines(self) -> list[str]:
        out = [self.mechanism, self.evidence, self.illuminant, self.caveat]
        if self.contradiction:
            # Surfaced, never smoothed over: a planet whose spectrum disagrees with the regime
            # we filed it under is one to check before posting, not one to write around.
            out.insert(2, f"⚠ Check this one: {self.contradiction}.")
        return out


def band_means(values: list[float]) -> dict[str, float]:
    """Mean geometric albedo in each band. The grid is fixed and stated in the file header
    (`cie-vis-380-780-5`), so the index arithmetic is safe."""
    out: dict[str, float] = {}
    for name, lo, hi in BANDS:
        i0 = max(0, int((lo - GRID_LO_NM) / GRID_STEP_NM))
        i1 = min(len(values), int((hi - GRID_LO_NM) / GRID_STEP_NM) + 1)
        chunk = values[i0:i1]
        out[name] = sum(chunk) / len(chunk) if chunk else 0.0
    return out


def _star_note(teff: float | None, spectral_type: str | None) -> str:
    """What the illuminant does to the answer. This is the half of the physics people forget:
    the colour is albedo × starlight, so a cool host warms every planet around it."""
    kind = (spectral_type or "").strip()
    label = f" ({kind})" if kind else ""
    if teff is None:
        return "Host star temperature unknown — the illuminant's tint is unconstrained."
    if teff < 4000:
        return (f"The host is {teff:,.0f} K{label} — a red-heavy illuminant, so the result "
                f"is warmer than the albedo alone would make it.")
    if teff > 7000:
        return (f"The host is {teff:,.0f} K{label} — a blue-heavy illuminant, which pushes "
                f"the result cooler than the albedo alone would make it.")
    return (f"The host is {teff:,.0f} K{label} — near-solar, so the albedo is doing most of "
            f"the work and the starlight little of it.")


# What each regime's own name claims about the mechanism, and the spectrum shape that would
# corroborate it. Regime first, because the regime IS what the engine did — the spectrum is
# the evidence for it, not a competing opinion.
#
# Getting this order wrong is not cosmetic. An earlier version led with the spectrum tilt, and
# so described HD 189733 b and WASP-12 b — both cloud-free, sodium-bearing and dark — as
# "blue-green", because a dark planet's residual blue does tilt that way. The mechanism was
# wrong even though the numbers were right.
def _mechanism(regime: str, tilt: float, mean: float,
               eq_temp_k: float | None = None) -> tuple[str, str | None]:
    """(sentence, contradiction). The second is set when our own spectrum does not look like
    the regime we assigned — worth saying out loud rather than smoothing over."""
    r = regime.lower()

    if "rocky" in r:
        odd = None if TILT_MILD <= tilt <= TILT_RED else (
            f"the regime says featureless grey, but the spectrum tilts {tilt:.2f} red-to-blue")
        return ("A thin atmosphere over rock: nothing in the visible absorbs strongly, so the "
                "spectrum is close to flat and the planet reads as grey.", odd)

    if "sodium" in r or "alkali" in r or "cloud-free" in r:
        dark = ("and little light returns at all" if mean < 0.2
                else "though it is not especially dark")
        odd = None if mean < 0.25 else (
            f"cloud-free regimes should be dark, but the mean albedo is {mean:.2f}")
        return (f"Cloud-free and hot: sodium takes the yellow-orange out of the middle of the "
                f"band, {dark} — what you see is the little that survives, not a bright hue.",
                odd)

    if "methane" in r:
        odd = None if tilt < TILT_MILD else (
            f"methane should suppress the red, but red/blue is {tilt:.2f}")
        return ("Methane absorbs the long wavelengths — the spectrum falls away toward the red "
                "end — so what comes back is blue-green.", odd)

    if mean > BRIGHT and TILT_MILD <= tilt <= TILT_RED:
        return ("A thick cloud deck reflects across the whole visible band more or less "
                "evenly, which is why it comes out bright and close to white.", None)
    if mean < DARK:
        return ("Almost nothing is reflected at any visible wavelength — this is a dark world, "
                "and its hue is what little survives rather than what dominates.", None)
    if tilt < TILT_STRONG:
        # The measured anchors (Karkoschka, Payne) carry no chemistry in their regime label —
        # it is literally "as observed" — so the absorber has to be inferred here or Neptune,
        # the textbook methane case, gets a generic sentence. Methane is only named when the
        # planet is cold enough for it to survive; above that the honest answer is "something".
        if eq_temp_k is not None and eq_temp_k < 500:
            return ("Methane absorbs the long wavelengths — the spectrum falls away toward the "
                    "red end — so what comes back is blue-green.", None)
        return ("Absorption at the long wavelengths pulls the red end down, so what returns is "
                "weighted to the blue-green.", None)
    if tilt > TILT_RED:
        return ("The blue end is suppressed and the red survives, so the planet keeps a warm "
                "cast rather than the blue one scattering alone would give.", None)
    return ("Cloud and haze reflect fairly evenly across the visible band, with only a mild "
            f"tilt ({tilt:.2f} red-to-blue), so the colour is pale and low in saturation.", None)


def physics_note(rec: dict) -> Physics | None:
    """Read the reason for a planet's colour back out of its record. None if it has no
    spectrum — better nothing than a story invented around missing data."""
    spectrum = (rec.get("spectrum") or {}).get("values") or []
    if len(spectrum) < 20:
        return None
    params, star = rec.get("params", {}), rec.get("host_star", {})
    bands = band_means(spectrum)
    mean = sum(spectrum) / len(spectrum)
    tilt = bands["red"] / bands["blue"] if bands["blue"] else 1.0
    regime = str(params.get("assumed_cloud_state") or "")

    evidence = (f"Our albedo: {bands['blue']:.2f} blue, {bands['green']:.2f} green, "
                f"{bands['red']:.2f} red (mean {mean:.2f}) — check it against the spectrum "
                f"plot on the planet page.")

    src = params.get("sources", {})
    assumed = [k.replace("_", " ") for k, v in src.items() if v == "assumed"]
    engine = params.get("spectrum_source", "unknown")
    caveat = (f"Regime '{regime}' from the {engine} engine"
              + (f"; assumed (not measured): {', '.join(assumed)}." if assumed else "."))

    mechanism, contradiction = _mechanism(
        regime, tilt, mean, params.get("equilibrium_temp_k"))
    return Physics(
        mechanism=mechanism,
        evidence=evidence,
        illuminant=_star_note(star.get("teff_k"), star.get("spectral_type")),
        caveat=caveat,
        contradiction=contradiction,
    )
