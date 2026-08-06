# Why these colours — the cheat sheet

The one sentence of physics in a post is the only part with any value, and it is the part
you cannot safely improvise at 23:40. You do not have to: the colour came out of a
deterministic pipeline, so the reason is already in the record.

`pipeline/explain.py` reads it back, and `tools/newswatch.py` prints it under **WHY THIS
COLOUR**. This page is what you check that against before you post.

> **What it is a claim about.** Everything below describes what *our model* did. It is a
> statement about the model, not a measurement of the planet. Only the five solar-system
> anchors use measured spectra; every exoplanet colour is modelled.

## The two-step every explanation has

A planet's colour is **albedo × starlight**, then CIE. So there are always two halves, and
skipping the second is the commonest way to say something wrong:

1. **What the atmosphere does to the light** — which wavelengths come back.
2. **What the star sent in the first place** — a 2,500 K M dwarf illuminates its planets
   with red-heavy light, so the same albedo curve lands warmer there than around the Sun.

## The regimes

Assigned by `pipeline/spectrum/parametric.py` from temperature, radius, mass and metallicity.
The knobs vary continuously, so neighbouring planets differ rather than snapping to
archetypes — the labels below are the ends of a blend, not buckets.

| Regime (`assumed_cloud_state`) | What happens to the light | Expect |
|---|---|---|
| `rocky / thin atmosphere (grey)` | Nothing in the visible absorbs strongly. | Flat spectrum, grey, moderate-low albedo |
| `cold, thick clouds + methane` | Methane absorbs the long wavelengths; cloud reflects the rest. | Red end falls away → **blue-green** |
| `temperate / warm, partial cloud + haze` | Water/ammonia cloud plus haze, reflecting fairly evenly. | Bright, pale, low saturation |
| `hot, cloud-free, alkali (sodium) absorption` | Sodium takes the yellow-orange; no cloud deck to reflect. | **Dark**; what survives is blue |
| `ultra-hot, cloud-free, very dark` | As above, more so. | Very dark; hue is the residue, not the story |

Two engines can supersede the parametric one for giants — the **Cahoy 2010** grid for cool
giants and **PICASO** for hot ones. `spectrum_source` on each record says which ran, and the
regime label still describes the chemistry.

## Reading a spectrum in five seconds

The briefing prints the mean geometric albedo in three bands. The plot on each planet page is
the same numbers.

| What you see | What it means |
|---|---|
| Red much lower than blue (ratio < 0.6) | Something is eating the long wavelengths — methane, in the cold regimes |
| Flat and high (mean > 0.35) | A thick cloud deck; bright and close to white |
| Flat and low (mean < 0.12) | Reflects almost nothing; the hue is the residue |
| A dip around 590 nm | Sodium — the D lines sit there |
| Rising steeply toward 380 nm | Rayleigh scattering, which is what makes a clear sky blue |

## The brightness caveat you must not skip

Every base swatch is normalised to `Y = 0.60` (`pipeline/config.py`,
`BASE_SWATCH_LUMINANCE_Y`). **Swatches show hue, not brightness.** A planet that reflects 2%
of its starlight and one that reflects 40% are rendered at the same lightness.

So *"this planet is dark"* is a claim about the albedo numbers, never about how the swatch
looks — and if you show a swatch while saying a planet is dark, say that the swatch is
normalised. The briefing prints the real `luminance_y` beside it.

## When the tool disagrees with itself

The explanation names the regime's mechanism and then checks the spectrum against it. If they
disagree — a planet filed as cloud-free and dark whose spectrum comes out bright and flat, for
instance — the briefing prints a `⚠ Check this one` line. That is a genuine flag: either the
regime is wrong for that planet or the spectrum is, and it is worth resolving before posting
rather than writing around.

## What you still have to supply

The mechanism is derived; the *sentence* is not. The tool will not write it, by design — a
templated caption is worth nothing, and this is the one part a reader can tell was written by
a person. What the cheat sheet gives you is the confidence that whatever you write is true of
the model, and the numbers to back it.

Two things it cannot tell you and you must add yourself:

- **The wavelength the news is about.** If the result being reported is infrared, it says
  nothing about visible colour. But the stronger claim — *"space telescopes tell us nothing
  about colour"* — is false, and a scientist will say so: optical secondary-eclipse photometry
  from TESS, CHEOPS and Kepler constrains geometric albedo inside those optical bandpasses,
  roughly 0.6–0.8 µm. <!-- factcheck: ignore --> Get the boundary right or don't raise it.
- **Which assumption you trust least.** Cloud state, metallicity and phase angle are assumed
  for every modelled planet, and the briefing lists which. Naming one is the difference
  between a claim and an honest claim.
