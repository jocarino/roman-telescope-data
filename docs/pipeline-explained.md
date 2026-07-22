# Exoplanet Palette — the pipeline explained

An end-to-end walkthrough of every data source and pipeline step, with the *why*
behind each and the unfamiliar concepts explained inline. Plan-level view (matches
`CLAUDE.md`), not tied to the current code.

---

## The core idea first

Everything hangs on one sentence: **the colour of a planet is the colour of its
star's light, minus whatever the planet's atmosphere absorbs before reflecting the
rest back at you.**

So to compute a planet's colour you need two things: (1) what the starlight looks
like, and (2) what fraction of each colour the planet reflects. Multiply them
together and you have the light that actually reaches an eye. Everything below is
either *getting those two ingredients* or *turning the result into a hex code*.

---

## Data sources — why each one exists

### ① NASA Exoplanet Archive

**What it is:** a public database of every confirmed exoplanet and its measured
properties — temperature, size, mass, orbit, and facts about its host star.

**Why we need it:** we don't get to observe these planets' colours directly (that's
the whole problem the project exists to solve). Instead we *predict* the colour from
physical parameters. To do that we need the inputs: how hot the planet is, how big,
how far from its star, and what kind of star it orbits. This is the archive's job —
it's the "what are the facts about this planet" source.

**Concepts:**

- **TAP API / `pscomppars` table** — TAP is just a query protocol (you send SQL-like
  queries over HTTP, get tables back). `pscomppars` is one specific table: "Planetary
  Systems Composite Parameters" — the archive's best single-row-per-planet summary,
  stitched from many papers. We use it because it gives one clean record per planet
  instead of one per publication.
- **Equilibrium temperature (Teq)** — the temperature a planet settles at from
  balancing starlight-in against heat-radiated-out. It's a proxy for "how hot,
  therefore what's its atmosphere doing" (hot enough and clouds evaporate, sodium goes
  gaseous, etc.). Teq is sometimes missing in the archive, so you compute it yourself
  from the star's temperature, the planet's distance, and radius — those always
  determine it.

### ② PICASO

**What it is:** NASA's open-source Python package that simulates a planet's
**reflected-light spectrum** from its physical parameters.

**Why we need it:** the archive gives you *parameters* (temperature, gravity,
metallicity), not *what colours the planet reflects*. PICASO is the physics engine
that turns "this planet is this hot, this heavy, has this much methane and these
clouds" into an actual curve of reflectivity-vs-wavelength. It's the heart of the
whole thing.

**Concepts:**

- **Reflected-light spectrum** — a graph: horizontal axis = wavelength (colour),
  vertical axis = what fraction of light the planet bounces back at that colour. A dip
  in the curve at red wavelengths means "this planet absorbs red," which is *why* it
  would look blue-green.
- **Why it's kept out of the web request** — PICASO is slow and needs large reference
  data files. You'd never make a user wait for it. So it runs offline in batch, and
  the website just reads the precomputed answer.

### ③ Cahoy et al. 2010 albedo grids

**What it is:** a set of precomputed reflectivity spectra for Jupiter- and
Neptune-class planets, published in a 2010 paper, covering a range of star-distances,
atmospheric compositions, and cloud states.

**Why we need it:** two reasons. (1) **Fallback** — if PICASO is too slow or fails for
some planet, you can interpolate a spectrum out of this ready-made grid instead.
(2) **Validation** — because it's an independent, peer-reviewed result, you can check
"does my PICASO output roughly match what Cahoy got for a similar planet?" It's the
sanity-check reference. It's also what the Roman mission community uses, so it keeps
the project credible.

**Concept — interpolation:** the grid only has spectra at specific points (e.g. a
planet at exactly 2 AU with exactly 1× metallicity). Your real planet is at 2.3 AU.
Interpolation = estimating the in-between spectrum by blending the nearest grid
points. Cheaper than running the full physics engine.

### ④ Host-star illuminant

**What it is:** the spectrum of the star's light — the light doing the illuminating.

**Why we need it:** this is ingredient (1) from the core idea. The same planet looks
different around a cool red star than around a hot blue-white one, because you can
only reflect colours that are present in the incoming light. A planet can't reflect
blue if its star emits almost no blue.

**Concepts:**

- **Illuminant** — lighting/colour-science term for "the light source shining on a
  thing." Your kitchen looks different under warm bulbs vs daylight; same object,
  different illuminant. The star is the planet's illuminant.
- **Blackbody / effective temperature (Teff)** — a "blackbody" is an idealized glowing
  object whose colour depends *only* on its temperature (cool → red, hot → blue-white,
  the same reason a stove element glows red then orange as it heats). Real stars are
  close enough to this that, for v1, you can approximate a star's whole spectrum from a
  single number, its effective temperature. It's a cheap, decent stand-in. Upgrade
  later to PHOENIX/Kurucz models (detailed simulated star spectra that include the
  actual absorption lines real stars have) if you need more accuracy.

### ⑤ Roman Coronagraph (CGI) bandpasses

**What it is:** the specific colour filters the Roman Space Telescope's coronagraph
will observe through — four narrow visible-light bands centered at 575, 660, 730, and
835 nm.

**Why we need it:** this is the project's signature hook. Roman won't see a planet's
*full* smooth spectrum — it sees only through those four windows. The project asks:
*if you only had those four measurements, how much of the planet's true colour could
you reconstruct?* So you need to know exactly what those four windows are.

**Concepts:**

- **Coronagraph** — an instrument that blocks the star's overwhelming glare (like
  blocking the sun with your thumb) so you can see the absurdly faint planet next to
  it. It's the enabling tech for imaging exoplanets in reflected light at all.
- **Bandpass / top-hat filter** — a filter that lets through only a range of
  wavelengths. "Top-hat" means we model it as a clean rectangle: 100% transmission
  inside the band, 0% outside (the shape looks like a top hat). Real filters have soft
  edges, but a rectangle is a fine v1 approximation.
- **Bandwidth (e.g. "10%")** — how wide the window is relative to its center. A 575 nm
  band at 10% bandwidth spans about ±29 nm around 575. Wider band = more light
  collected but blurrier colour information.

---

## The pipeline — why each step, in order

Think of this as an assembly line. Each step's output is the next step's input.

### Step 1 — Fetch planet + star parameters

**What:** pull the numbers for a planet (and its star) from the archive; cache them to
disk.

**Why:** you can't compute anything without the inputs. Caching matters because the
archive rate-limits (throttles you if you query too fast), and you'll re-run the
pipeline many times during development — hitting a local cached copy is fast and
polite. The Teq-fallback (compute it if it's null) exists because missing data would
otherwise crash the planets that need it most.

### Step 2 — Generate the albedo spectrum A(λ)

**What:** produce the curve of "fraction of light reflected at each wavelength," from
380 to 780 nm.

**Why:** this is ingredient (2) — the planet's own colour fingerprint, before the star
is applied. This is where the physics lives: methane carving out the reds, clouds
brightening everything, sodium eating the yellow.

**Concepts:**

- **λ (lambda)** — the Greek letter physicists use for wavelength. A(λ) just means
  "albedo as a function of wavelength."
- **Geometric albedo** — the specific "fraction reflected" measure used here: how
  bright the planet is at full-face illumination compared to a perfect flat white disk
  of the same size. 0 = pitch black, ~1 = mirror-bright. "Geometric" distinguishes it
  from other albedo definitions; it's the one that corresponds to what you'd *see*.
- **380–780 nm** — the wavelength range of human vision, violet (380) to deep red
  (780). Measured in nanometres. We only compute colour over the range eyes actually
  respond to.
- **Methane bands / Rayleigh scattering / sodium** (the physical knobs):
  - *Methane* absorbs strongly in the red and near-infrared. Remove red from white
    light and you're left with blue-green — that's literally why Neptune and Uranus are
    that colour.
  - *Rayleigh scattering* is the same effect that makes Earth's sky blue: small
    molecules scatter short (blue) wavelengths more than long ones. It tints a clear
    atmosphere blue.
  - *Sodium* absorbs a chunk of yellow-orange. In cloud-free hot Jupiters this darkens
    them and shifts them blue (the real planet HD 189733b was measured deep cobalt blue
    partly for this reason).

### Step 3 — Reflected flux F(λ) = A(λ) × S(λ)

**What:** multiply the planet's albedo A(λ) by the star's spectrum S(λ), wavelength by
wavelength.

**Why:** this is the core idea made literal. A(λ) says "what fraction do you reflect at
each colour," S(λ) says "how much of each colour is even arriving." Their product F(λ)
is the *actual light that leaves the planet toward an observer* — the thing that has a
colour. You must combine both; neither alone is the visible result.

**Concept — flux:** just "amount of light energy." F(λ) is the amount of reflected
light at each wavelength.

### Step 4 — Convolve F(λ) with the CIE colour-matching functions → XYZ

**What:** collapse the whole smooth spectrum down to three numbers, X, Y, Z.

**Why:** a spectrum is dozens of numbers (one per wavelength). But a human eye only has
three types of colour receptor (cones), so *all* colour perception compresses to just
three values. This step converts "physical light" into "what a human visual system
registers." You can't get to a colour without it.

**Concepts:**

- **CIE colour-matching functions (CMFs)** — three curves, standardized in 1931 by
  measuring real people, that encode how strongly each of the three cone types responds
  to each wavelength. They are the mathematical model of human colour vision. ("CIE" is
  the international colour-standards body; "1931 2°" is the specific classic dataset.)
- **Convolve** — here it just means "multiply the spectrum by each curve and add up the
  result." Do it with all three curves and you get three totals.
- **XYZ tristimulus values** — those three totals. "Tristimulus" = three stimuli, one
  per cone-type-ish channel. XYZ is a device-independent, canonical way to name any
  colour a human can see — an intermediate hub that every colour space (sRGB, etc.)
  converts through. **Y specifically is luminance** — the perceived brightness — which
  becomes important in the next steps.
- Use `colour-science`'s `sd_to_XYZ` rather than hand-coding this — because the CMF
  data and integration rules are fiddly and easy to get subtly wrong; a vetted library
  is more trustworthy than a hand-rolled approximation.

### Step 5 — XYZ → linear sRGB → gamma-encode → clamp

**What:** convert the human-vision XYZ into an actual RGB colour your screen can
display, then package it as a hex code.

**Why:** XYZ is abstract; monitors speak RGB. This is the translation to a displayable
colour. Each sub-step handles a real problem:

**Concepts:**

- **sRGB** — the standard RGB colour space that web browsers and most monitors assume.
  The conversion from XYZ is a fixed 3×3 matrix multiply (standardized numbers).
- **Linear vs gamma-encoded** — displays don't respond to signal linearly; a pixel
  value of 128 is *not* half as bright as 255. "Gamma encoding" is the correction curve
  applied so the stored numbers map correctly to perceived brightness. You do the colour
  math in *linear* space (where physics adds up correctly) and gamma-encode only at the
  very end for display. Skip this and colours come out wrong.
- **Clamp** — sRGB can't represent every colour the eye can see (its "gamut" is
  limited). A computed colour might land slightly outside what a screen can show, giving
  an RGB value below 0 or above 1. Clamping forces it back into the valid range. Flag
  when this happens (`out_of_gamut`) so you know the displayed colour is an
  approximation.
- **The brightness gotcha (normalise Y ≈ 0.6)** — most of these planets are genuinely
  dark (they reflect little light), so their honest colour is nearly black — useless as
  a design swatch. The convention is: keep the *chromaticity* (the actual hue/tint) but
  reset the *luminance* (Y) to a fixed pleasant level so every swatch is visible. Report
  true darkness separately as a number, rather than baking it into a near-black swatch.
  This is a deliberate "colour identity vs. true brightness" split.

### Step 6 — Derive the palette

**What:** from the one base colour, generate a small designer-friendly palette: a
5-stop light-to-dark ramp plus a couple of accent colours pulled from interesting
features in the spectrum.

**Why:** the product isn't "one hex per planet," it's a *palette* ("the colour scheme
of every known exoplanet"). A single colour isn't usable for design; a coordinated set
of stops is. The accents are sampled from physically meaningful places in the spectrum
— e.g. the colour right at the edge of a methane absorption band — so the palette stays
*derived from the physics* rather than being arbitrary tints.

**Concept — lightness ramp:** the same hue rendered at 5 brightness levels (like a
paint chip card), which is what makes a colour usable as a design system.

---

## The Roman view (the branch off to the side)

**What:** instead of using the full smooth spectrum, integrate F(λ) through *only*
Roman's four bands → four numbers → interpolate a fake "spectrum" between just those
four points → run *that* through the same CIE steps. Then show "true colour" next to
"as Roman would see it."

**Why:** this is the entire point of the project's Roman hook — quantifying how much of
a planet's colour identity survives when you throw away everything except four filter
measurements. It reuses steps 4–5 exactly (same colour pipeline), which is why the
architecture keeps that colour conversion as one shared codepath.

**Concept — the honesty problem:** Roman's four bands only span 575–835 nm (yellow
through near-infrared). There is *zero* information below 575 nm — the entire blue half
of vision — where many of these planets are actually blue. So the Roman-reconstructed
colour is partly a guess in that region, and the design deliberately marks that guessed
zone rather than pretending it's known.

**Microlensing flag:** some planets were discovered by microlensing (detected purely by
their gravity bending a background star's light) — we never receive *any* light from
the planet itself. So their swatches are honestly labeled "model-only, no light ever
observed."

---

## The whole chain in one line

**Facts (archive) + physics engine (PICASO) → the planet's reflectivity → times the
starlight → collapse to human vision (CIE) → to a screen colour (sRGB) → to a
palette**, with a parallel "what would Roman actually capture" branch running through
the same colour machinery.
