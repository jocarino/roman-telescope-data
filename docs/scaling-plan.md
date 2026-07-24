# Scaling plan: 20 → 200 → ~1,000 → the broad catalog

The gallery is a deliberately curated set of 20 well-characterised planets. Scaling toward the
~6,000 known exoplanets is not "more of the same": most planets are only partially characterised,
so the pipeline must (a) refuse to invent colours it can't justify, (b) fall back to archetype
assumptions *transparently*, and (c) survive the front-end load. This doc records what is already
built and the staged path to a broad catalog.

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
- The committed `data/planets.json` is the 205-planet pilot set. Regenerate with
  `uv run python -m pipeline build --bulk 200`.

### Phase 2.5 (DONE)
- **Distance-band filter** — buckets (≤25 / 25–100 / 100–500 / >500 pc) computed in JS from the
  indexed `dist`. At 205: 13 / 27 / 65 / 100.
- **Discovery-method filter** — present-only, most-common first (Transit 168, RV 29, Imaging 7,
  TTV 1). Fixed the `ima → Imaging` label along the way.
- **Provenance filter decluttered** — now lists only provenances present in the data, and
  auto-hides entirely when only one exists (future-proof: it returns when Roman-measured lands).

## Phase 3 — broad catalog (IN PROGRESS)

Real archive scale (measured): **6,324** confirmed planets, of which **~5,785 (91%)** pass the
completeness gate. Pre-generating detail pages + fragments for all of those is ~230 MB of static
HTML — impractical to commit and deploy. So Phase 3 splits into "make the front-end scale to any
N" (done) and "how big a set we actually ship" (a deployment cap, not a pipeline limit).

- **Scaled data + honest count — DONE.** `--bulk 1000` builds a **956-planet** catalog (nearest
  gated + curated pins). The gallery states it honestly: *"Modelling 956 of the ~6,300 known
  exoplanets — the nearest that pass our data-completeness gate."* (`KNOWN_TOTAL_APPROX` in
  `web/build.py`.) `data/planets.json` at 956 is 9.6 MB (committed); `dist/` (gitignored, built
  at deploy) is ~43 MB.
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

### Still open (Phase 3 remainder)
- **How big to ship.** 956 is a deployable default; the pipeline handles any N. Going to the full
  ~5,785 needs a lighter per-planet detail footprint (or client-rendered detail) to keep `dist`
  sane — decide before widening.
- **Type/metallicity archetype grid** so colour varies by planet *class*, not temperature alone
  (currently metallicity is a single assumed value). Not yet done.
- **Prebuilt/served search** — not needed at 956 (client filter over the fetched index is instant);
  revisit past a few thousand.

## Settled decisions

- **Unknown host star (e.g. OGLE microlensing) — EXCLUDE.** The illuminant *is* the colour, so a
  made-up star produces a made-up colour with no point in showing it. The gate now requires a
  real host-star temperature; planets without one are dropped (and logged). This drops the OGLE
  microlensing example from the curated set; the microlensing badge/banner code remains for any
  future planet that *does* have a characterised host.
- **Missing radius on giants — keep `n/a`, don't fabricate.** The model uses a generic default
  internally for routing only; radius barely affects reflected-light colour, and inventing a
  displayed value would add nothing.
