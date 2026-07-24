# Scaling plan: 20 → 200 → ~1,000 → the broad catalog

**Status: COMPLETE (2026-07-24).** The full catalog is live in production: **5,759 planets**
(full archive pull: 6,290 fetched, 531 excluded by the completeness gate). Final numbers are
recorded in the Phase 3 completion section below; the rest of the doc is the staged path that
got there.

The gallery began as a deliberately curated set of 20 well-characterised planets. Scaling toward
the ~6,000 known exoplanets was not "more of the same": most planets are only partially
characterised, so the pipeline must (a) refuse to invent colours it can't justify, (b) fall back
to archetype assumptions *transparently*, and (c) survive the front-end load.

## Phase 1 — data-layer foundations (DONE)

Implemented so the machinery is ready before we widen the input set:

- **Completeness gate** (`pipeline/catalog.completeness_gate`) — a planet is modelled only if it
  has a *size* (radius, or a mass we can class by) and a *temperature* (measured, or computable
  from star + orbit). Below that there is nothing to anchor an archetype to, so it is excluded
  and logged rather than guessed. Excluded planets are printed at build time.
- **Per-field data provenance** (`ParamSources`) — every displayed value is tagged `measured`
  (a real NASA Archive datum), `computed` (derived from star + orbit, e.g. equilibrium temp), or
  `assumed` (archetype default — cloud state, metallicity, phase, or a missing radius/host-star
  temperature). Shown as coloured tags on the planet data card. This is the honesty mechanism:
  we show which numbers are real, not a made-up quality score.
- **Distance from Earth** (`sy_dist`) — fetched, stored, shown, and a `Sort: nearest Earth` axis.
- **Incremental record cache** (`pipeline/emit/cache.py`) — each planet's record is cached by a
  hash of its inputs + pipeline/schema versions; a re-run recomputes only what changed. This is
  what makes 200+ (and any PICASO planets) rebuild in seconds instead of from scratch.

At 20 curated planets the gate excludes none (they are well-characterised by design); it exists
for what comes next.

## Phase 2 — the 200-planet pilot (DONE)

Goal was to exercise the gate, fallbacks, provenance display, and new axes at a scale that
surfaces the real problems, *without* committing to a full front-end rebuild blind.

1. **Bulk fetch — DONE.** `fetch_bulk` / `catalog_bulk` pull the nearest well-characterised
   planets (`select top N … where sy_dist is not null and (pl_rade or pl_bmasse) … order by
   sy_dist`), merged with the always-pinned `CURATED_NAMES` and de-duplicated. CLI: `pipeline
   build --bulk N`. The ADQL is a deliberately *loose* pre-filter so the gate does the real work.
2. **Gate at scale — DONE.** `--bulk 200` fetches 220 (200 nearest + 20 curated), the gate
   excludes **15** (11 microlensing lenses with no host star, 4 with no derivable temperature),
   keeping **205**. Exclusions are summarised by reason at build time. Honest ratio, gate earns
   its keep.
3. **Planet-type classification — DONE.** `pipeline/classify.py` buckets each planet (rocky /
   super-Earth / Neptune-like / gas-giant / hot-Jupiter) by radius, mass fallback, and a
   hot/cool giant split by temperature. Exposed as a gallery **type filter**. At 205 the spread
   is even: neptune 55, super-earth 50, rocky 46, hot-jupiter 27, gas-giant 27.
4. **Front-end survival — MEASURED; heavy rebuild DEFERRED to Phase 3.** The premise ("the
   all-live-WebGL grid will melt at 200") turned out false. Measured at 205 planets: **708 ms**
   full load, **26 ms** to render all 205 cards (0.13 ms/card), **27 MB** heap, 193 KB page /
   72 KB inlined index. The renderer uses one shared WebGL context drawn to per-card 2D canvases,
   so there is no context-count wall. Virtualization, pre-computed swatch PNGs, and a fetched
   JSON index are therefore **premature at this scale** — they earn their keep at Phase 3
   (thousands), where the inlined index and per-card draw actually start to hurt. Recorded here
   rather than built speculatively.
5. **Perf budget — MEASURED (above).** Re-measure before Phase 3; the ceiling to watch is the
   inlined `window.PLANETS` (grows linearly) and total card-draw time on load.

### Also shipped in Phase 2
- **Colour families now genuinely varied** at scale (white 70, blue 49, teal 46, orange 39,
  green 1) — validating the colour filter, which at 19 planets was ~⅔ blue.
- Spectrum engines spread across the set (≈parametric 158 / cahoy 40 / picaso 7); no `#0000ff`
  clipping artifacts.
- At this phase the committed `data/planets.json` was the 205-planet pilot set (the file was
  still small enough to commit then; it is release-hosted now).

### Phase 2.5 (DONE)
- **Distance-band filter** — buckets (≤25 / 25–100 / 100–500 / >500 pc) computed in JS from the
  indexed `dist`. At 205: 13 / 27 / 65 / 100.
- **Discovery-method filter** — present-only, most-common first (Transit 168, RV 29, Imaging 7,
  TTV 1). Fixed the `ima → Imaging` label along the way.
- **Provenance filter decluttered** — now lists only provenances present in the data, and
  auto-hides entirely when only one exists (future-proof: it returns when Roman-measured lands).

## Phase 3 — broad catalog (DONE)

Real archive scale at the time of the pilot: ~6,300 confirmed planets, of which ~91% pass the
completeness gate. Pre-generating detail pages + fragments for all of those looked impractical
to commit and deploy, so Phase 3 split into "make the front-end scale to any N" and "how big a
set we actually ship". Both halves are now resolved: the front-end scales, `dist/` is never
committed (built at deploy), and the data artifact moved out of git to GitHub Releases — see
the completion section below.

- **Scaled data + honest count — DONE.** `--bulk 1000` built a **956-planet** interim catalog
  (nearest gated + curated pins). The gallery states the count honestly: *"Modelling N of the
  ~6,300 known exoplanets…"* (`KNOWN_TOTAL_APPROX` in `web/build.py`.) At 956,
  `data/planets.json` was 9.6 MB (then committed); `dist/` (gitignored, built at deploy) was
  ~43 MB.
- **Front-end rebuild — DONE.** The gallery no longer inlines the index or server-renders every
  card. Instead: build writes `dist/planets.index.<build>.json`; the gallery **fetches** it, then
  renders cards **incrementally** from JS (60/batch, infinite-scroll via a sentinel
  IntersectionObserver) and **draws each planet lazily** on a rAF-throttled scroll pass (only
  in-viewport, not-yet-drawn cards). Long-press hold-to-peek and hover-spin both still work on
  the JS-generated cards. (Rebased onto the parallel mobile-UI branch: their sticky toolbar,
  hold-to-peek, and accent themes are the base; the scale layer was re-applied on top.)

  Measured at 956, current approach → new:
  | metric            | before (inlined + all cards) | after (fetched + incremental) |
  |-------------------|------------------------------|-------------------------------|
  | index.html        | 890 KB                       | **11 KB** (+322 KB fetched index) |
  | full load         | 3.9 s                        | **0.5 s**                     |
  | cards in DOM      | 956                          | **60** (a batch)              |
  | DOM nodes         | 6,832                        | **770**                       |
  | JS heap           | 44 MB                        | **29 MB**                     |

- **Incremental builds** — already in place (`emit/cache.py`); a 1000-planet rebuild is seconds.

### Phase 3 completion (2026-07-24) — final numbers
- **How big to ship — RESOLVED: everything.** The full archive pull is deployed: **6,290
  fetched, 531 excluded** by the gate (288 no host-star Teff, 229 no computable temperature,
  14 stellar-remnant hosts) → **5,759 planets live**. Engines: 4,439 parametric, 1,320 Cahoy,
  PICASO for selected targets. 1 microlensing planet (TCP J05074264+2447555 b), 3
  simulated-cgi targets.
- **The "impractical to commit and deploy" problem dissolved**, in two moves:
  - `data/planets.json` (~82 MB) is no longer committed — it is a GitHub Release asset
    published by `scripts/release-data.sh`; the committed one-line `data/RELEASE` names the
    tag and clean builds fetch it via `scripts/fetch_data.py` (no token needed, public repo).
    The Dockerfile fetches the release before rendering; Dokploy builds it on a push webhook.
  - `web.build` streams one planet at a time: all 5,759 pages render in ~7 s locally, peak
    RSS ~780 MB (dominated by the parsed dataset). `dist/` ≈ 477 MB (gitignored, built at
    deploy); the runtime gallery index ≈ 2.5 MB.
- **Type/metallicity archetype grid** so colour varies by planet *class*, not temperature alone
  (currently metallicity is a single assumed value). Still open.
- **Prebuilt/served search** — still client-side over the fetched index at 5,759; revisit only
  if it degrades.

## Settled decisions

- **Unknown host star (e.g. OGLE microlensing) — EXCLUDE.** The illuminant *is* the colour, so a
  made-up star produces a made-up colour with no point in showing it. The gate now requires a
  real host-star temperature; planets without one are dropped (and logged). This drops the OGLE
  microlensing example from the curated set; the microlensing badge/banner code remains for
  planets that *do* have a characterised host (exactly one in the full catalog:
  TCP J05074264+2447555 b).
- **Missing radius on giants — keep `n/a`, don't fabricate.** The model uses a generic default
  internally for routing only; radius barely affects reflected-light colour, and inventing a
  displayed value would add nothing.
- **Stellar-remnant hosts (> 12,000 K) — EXCLUDE.** A host that hot is a hot subdwarf or white
  dwarf — the cinder of a dead star, UV-dominated, usually in an eclipse-timing binary with a
  disputed circumbinary planet. A reflected *visible* colour is meaningless there. The 12,000 K
  cut sits above every genuine hot main-sequence star (hottest A/B in the set ≈ 9,200 K), so it
  drops only the remnants (NSVS 14256825, 2MASS J19383260, DP Leo, NN Ser, …).
- **Metallicity on rocky worlds — `n/a`, not the giant relation.** The mass–metallicity relation
  is a giant-planet relation; rocky worlds have no H/He envelope, so it's meaningless and unused
  for their (grey) colour. Parametric leaves metallicity `None` for rocky planets.
