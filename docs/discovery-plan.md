# Plan — Discovery stage (finding your own planets)

Status: **planned, not started.** Sequenced *after* the PICASO/Cahoy spectrum router.
This is a future milestone; nothing here is built yet.

## Context

The app currently colours *confirmed* planets whose parameters the NASA Exoplanet Archive
hands over on a plate (`pl_rade`, `pl_eqt`, `pl_orbsmax`, host-star Teff). A **discovery
stage** would let the project find its *own* candidate planets by mining public light curves
(TESS/Kepler now; Roman Bulge microlensing post-launch — Roman has no proprietary period, so
its data is public on day one). A vetted candidate derives the same three inputs the colour
pipeline needs and drops straight in with a `candidate` flag instead of `confirmed`.

The whole point: **discovery is additive and upstream — it does not touch the colour
pipeline, web, or deploy.** It is a new *parameter source*, peer to the Archive fetch, behind
one shared seam (the same discipline as the `SpectrumProvider` and measured-data swap seams).

## The seam: `ParameterSource`

```
discovery/ ──(light curve → search → vet → derive)──┐
                                                     ├─→ PlanetInput ─→ emit/build.py ─→ colour pipeline
fetch/archive.py ──(TAP lookup)──────────────────────┘        (unchanged)
```

```python
class ParameterSource(Protocol):
    def planets(self) -> list[PlanetInput]: ...   # confirmed OR candidate, same shape
```

Both the Archive and Discovery implement it. Everything downstream is untouched.

## Two new honesty axes (orthogonal to colour `provenance`)

Existing `provenance` = colour data lineage (model / simulated-cgi / measured-cgi /
microlensing). Discovery adds *is this even a real planet, and where did its parameters come
from?*:

- **`confirmation_status`**: `confirmed` | `candidate` | `community-candidate` | `false-positive`
- **`param_source`**: `archive` (measured & published) | `derived` (from a light curve, with uncertainties)
- **`vetting` block**: `fpp` (TRICERATOPS false-positive probability), `sde` (TLS signal
  strength), flag booleans (odd-even consistent, no secondary eclipse, centroid on-target).

UI: a loud **"Candidate · FPP 4%"** badge (like the microlensing "model-only" badge), and a
"How to read this" line: *"Parameters derived from a TESS light curve, not yet confirmed —
radius ±X%, temp ±Y K."*

## Module layout: `pipeline/discovery/`

```
pipeline/discovery/
  lightcurve.py    # LightCurveSource protocol; lightkurve (MAST) + eleanor (FFI) impls
  search.py        # transitleastsquares -> TransitSignal(period, depth, dur, t0, sde)
  vet.py           # TRICERATOPS FPP + heuristic cuts -> Vetting(fpp, disposition, flags)
  derive.py        # transit + stellar params -> PlanetParams (+ uncertainties)
  stars.py         # stellar params (R*, M*, Teff) from TIC/Gaia via lightkurve/catalog
  candidates.py    # orchestrate source->search->vet->derive; implements ParameterSource
  cache/           # light curves + TLS results (heavy; offline only)
```

## Derivation (the three colour-pipeline inputs, with error bars)

```python
def derive_params(signal: TransitSignal, star: StellarParams) -> DerivedParams:
    rp  = star.radius * sqrt(signal.depth)                         # R_earth (depth = (Rp/R*)^2)
    a   = ((G * star.mass * signal.period**2) / (4*pi**2))**(1/3)  # AU (Kepler III)
    teq = star.teff * sqrt(star.radius_au / (2*a)) * (1-A_bond)**0.25
    return DerivedParams(rp, a, teq, sigma=propagate(depth_err, stellar_errs))
```

- The eq-temp formula is **literally `ArchiveRecord.equilibrium_temp_k()` — reuse it.**
- Output is the existing `PlanetParams` pydantic model **plus a `sigma`**. A candidate then
  becomes a `PlanetInput` with a real host-star illuminant and flows into the same
  PICASO/Cahoy/parametric router — closing the loop with the spectrum work.

## Vetting is a first-class GATE (not a step)

The false-positive rate is savage (most transit-search hits are eclipsing binaries or
systematics), so vetting is a hard gate with **logged rejections — never silent truncation**:

```python
def candidates(self) -> list[PlanetInput]:
    out = []
    for tic in self.targets:
        lc  = self.source.get(tic)                 # cached
        sig = search(lc)                           # TLS
        if sig.sde < SDE_MIN:   log_drop(tic, "weak signal"); continue
        vet = triceratops_vet(sig, lc, star)
        if vet.fpp > FPP_MAX:   log_drop(tic, f"FPP {vet.fpp}"); continue
        if not vet.flags_ok():  log_drop(tic, vet.failed_flags()); continue
        if derive_params(sig, star).rp < 3.0:  log_drop(tic, "below 3 R⊕"); continue
        out.append(to_input(sig, star, vet, status="candidate"))
    log_summary(kept=len(out), dropped=...)        # report what was cut
    return out
```

The `< 3 R⊕` cut is the happy accident: the project only wants giants, which are the
deepest, easiest-to-find, lowest-FPP signals.

## Placement & dependencies

- **Offline only** — like PICASO, discovery runs in the batch/CI stage into `planets.json`.
  Light curves (~MB each) and TLS (CPU-heavy) never touch the web build or the VPS.
- **Heavy deps isolated** in a `discovery` optional-extra (`pip install -e '.[discovery]'`),
  exactly like the `picaso` extra: `lightkurve`, `transitleastsquares`, `TRICERATOPS`,
  `eleanor`. Site build stays lean.
- **Caching** at two layers (raw light curves; TLS results), keyed by TIC ID.

## Forward-compat: Roman microlensing is the same seam

Post-launch Bulge anomaly hunting (RMDC26) is *another* `ParameterSource` — a `derive.py`
variant (mass ratio `q` + separation `s` -> planet mass, projected separation; eq-temp poorly
constrained -> null -> existing fallback), same protocol, same downstream. Those planets are
already flagged `is_light_isolable=False`. A sibling module, not a rewrite.

## Build order (when picked up)

1. **Model + seam:** add `confirmation_status`, `param_source`, `vetting` to the schema;
   define `ParameterSource`; make `catalog.py` (Archive) implement it. Wire a `--source
   discovery` path in the CLI. (No science yet — proves the seam with a hand-made candidate.)
2. **Derivation + stars:** `derive.py` (formulas + uncertainty propagation, reusing the
   eq-temp function) and `stars.py` (TIC/Gaia stellar params). Unit-test against a known
   confirmed planet — re-derive its radius/a/Teq from its transit and check they match.
3. **Search:** `lightcurve.py` (lightkurve/eleanor) + `search.py` (transitleastsquares),
   cached. Run on a handful of TIC IDs with known planets as positive controls.
4. **Vetting gate:** `vet.py` (TRICERATOPS FPP + odd-even/secondary/centroid cuts) with
   logged drops. This is most of the real work; do it properly, not as a stub.
5. **UI honesty:** candidate badge, derived-param uncertainty, "How to read this" copy.
6. **(Post-launch) microlensing source** as a sibling `ParameterSource`.

## Verification

- **Derivation:** re-derive params for a known confirmed planet from its light curve; assert
  radius/a/Teq land within uncertainty of the Archive values.
- **Positive controls:** run search+vet on TIC IDs with confirmed planets; they should pass.
- **Negative controls:** run on known eclipsing binaries; they should be *rejected* with a
  logged reason (proves the gate works).
- **End-to-end:** a vetted candidate produces a `PlanetInput`, gets a colour + Roman view +
  palette identical in machinery to a confirmed planet, and renders with a Candidate badge.

## Honest caveats

- **Vetting is most of the work.** A credible discovery stage needs TRICERATOPS wired
  properly — a stub would surface eclipsing binaries as "planets" and violate the project's
  honesty ethic.
- **Larger than the PICASO router** (real MAST downloads, CPU-heavy search, a stats
  dependency). Sequence it *after* the colour-side PICASO/Cahoy work.
- **"Discovered" (archive sense) needs follow-up** you can't do solo; ExoFOP / NASA Exoplanet
  Watch exist to connect amateurs to that. In-app, a find stays `candidate`.

## What's new vs reused

| New | Reused as-is |
|---|---|
| `pipeline/discovery/` (6 small modules) | `PlanetParams`, `PlanetInput`, `HostStar` models |
| `ParameterSource` protocol | `equilibrium_temp_k()` derivation |
| `confirmation_status` + `vetting` fields | the entire colour → Roman → palette pipeline |
| Candidate badge + honesty copy | provenance / badge / "how to read this" UI |
| `discovery` optional-dep extra | the `SpectrumProvider` router (PICASO/Cahoy/parametric) |
