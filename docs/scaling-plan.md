# Scaling plan: 20 → 200 → the broad catalog

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

## Phase 2 — the 200-planet pilot (next)

Goal: exercise the gate, fallbacks, provenance display, and new axes at a scale that surfaces the
real problems, *without* committing to the full front-end rebuild blind.

1. **Bulk fetch.** Replace the name-list query with a broad `pscomppars` pull (default parameter
   set, `WHERE` the completeness columns are non-null), paginated and cached. Keep `CURATED_NAMES`
   as a pinned always-include set. Add `--limit N` / a query flag to the build CLI.
2. **Run the gate at scale.** Log the keep/exclude ratio — this is the real test of the gate
   thresholds. Expect a meaningful fraction excluded; that is the honest outcome, not a bug.
3. **Planet-type classification.** Derive a size/temperature class (rocky / super-Earth / Neptune /
   Jupiter / hot-Jupiter) on the record, for a new **type** filter — the axis that actually makes
   a big gallery explorable.
4. **Front-end survival at 200.** The current all-live-WebGL grid will not scale:
   - **Grid virtualization** — render only visible cards.
   - **Pre-computed static swatch images** at build time (one tiny PNG per planet); live WebGL only
     on hover and on the detail page.
   - Move the inlined `window.PLANETS` index to a **fetched JSON**.
   - **New filters:** type, distance band, discovery method/year, host-star type. Deprioritise the
     provenance filter (≈all "model" at scale).
5. **Perf budget.** Measure page weight and first render; set a ceiling before widening further.

## Phase 3 — broad catalog (toward the full set)

- Whole-archive pull behind the gate; a large fraction will be excluded — surface the count so
  "modelled N of M known planets" is stated honestly.
- Client-side search may need a prebuilt index or server-side search once the set is large.
- A small type/metallicity archetype grid so colours vary by planet class, not temperature alone.
- Incremental builds are essential here (already in place).

## Open decisions (flagged, not yet settled)

- **Unknown host star (e.g. OGLE microlensing).** Currently kept with the host-star temperature
  `assumed` (Sun-like fallback) and tagged as such. Microlensing lenses are usually cooler M
  dwarfs, so the Sun-like assumption is a stretch. Options: exclude these, or assume an M-dwarf
  temperature for microlensing lenses. Revisit at Phase 2.
- **Missing radius on giants.** Shown as `n/a`; the model uses a generic default internally for
  routing. We could instead display an assumed giant radius, tagged `assumed`, for completeness.
