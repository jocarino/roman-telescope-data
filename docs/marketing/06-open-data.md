# Open the dataset

**Status:** not started · **Effort:** low · **Payoff:** medium — and it unblocks two other things · **Hub:** [Marketing plan](./README.md)

## The bet

"The modelled visible colours of 5,700 exoplanets" is a dataset that does not otherwise exist.
Publishing it costs almost nothing — the file is already generated and already released — but
it reaches a crowd no other channel here touches: data people, notebook writers, generative
artists, students looking for a project. Every derivative they build is a link back, and unlike
a social post, a dataset keeps being discovered for years through the host's own search.

**Correction to that "already released", though.** The file goes out with *no licence at all*: no
`LICENSE` in the repo, no rights field in the JSON header, no rights statement on the GitHub
release. The default is all-rights-reserved, so nobody may legally reuse it today. This doc is
therefore not "mirror an open file to three platforms" — it is *make the file open, then deposit it
once, properly*. See [reviews/06-open-data-review.md](./reviews/06-open-data-review.md).

The strategic part is the DOI. A citable record turns "a website's claim" into "a published
source", which is the gate on [04-wikimedia.md](./04-wikimedia.md) and a large part of what
makes a scientist comfortable engaging in
[13-credit-the-scientists.md](./13-credit-the-scientists.md).

## Where to publish

**Zenodo — do this one first.** Free, CERN-run, permanent, and it mints a DOI. It's also the
only one that makes the data *citable*, which is the whole strategic point. This is a one-evening
job with the longest tail of anything in this plan. Two details that decide whether it works:

- **Do NOT rely on the GitHub–Zenodo integration.** It archives the *repo tarball*, and
  `data/planets.json` is gitignored (`.gitignore:15`) — the automatic archive would contain no
  data at all. Upload the release asset by hand.
- **Concept DOI vs version DOI.** Zenodo mints a persistent identifier per version, linked to all
  other versions, plus a concept DOI that always resolves to the latest. Cite the *version* DOI
  wherever a claim must be checkable against a fixed file; use the concept DOI for "the dataset"
  in general. Keep one Zenodo version per `data-*` release tag so the two numbering schemes line up.

**A domain repository would be better — and neither is open to us.** VizieR/CDS requires the data
to be tied to a refereed-journal publication; the NASA Exoplanet Archive's contributed-data route
ingests parameters from refereed papers, not third-party derived colour tables. So Zenodo is the
right answer, not the lazy one. The upgrade path, if this ever justifies it, is a short data paper
(*Astronomy & Computing* or PSJ), which would unlock VizieR — RNAAS would not, it isn't refereed.

**Hugging Face Datasets.** Worth it, but *conditional*: HF's value is the dataset viewer and its
Croissant metadata export, and both need a flat tabular file. As a 90 MB JSON blob this is a dead
upload. Do it after the Parquet/CSV derivative exists, not before.

**Kaggle Datasets — downgrade this.** The audience is competition- and notebook-driven, and a
static astronomical table with no prediction target tends to get bookmarked and abandoned. It also
carries no DOI and no way to express per-source terms. Better use of the same evening: put a
schema.org `Dataset` JSON-LD block on the site, which feeds Google Dataset Search — a strictly
larger and more durable discovery surface, built from metadata the Zenodo record needs anyway.

**GitHub Releases** — already happening (`release-data.sh`, `data/RELEASE`). Keep it as the
canonical source; the others mirror it.

Skip data.world and the rest. Diminishing returns.

## What to package

The bar for a dataset being *used* rather than downloaded-and-abandoned is a good README. It
should include:

- **A data dictionary.** Every field, its units, its provenance, and its uncertainty. The
  provenance flags (`model` / `simulated-cgi` / `measured-cgi` / `microlensing`) are the most
  important column in the file and the easiest to misuse — document them hard.
- **The method in five sentences**, with links to the sources it's built on. Consistent with the
  credits page from [13-credit-the-scientists.md](./13-credit-the-scientists.md).
- **The honesty statement, prominently.** Someone will plot these colours as though they were
  observations. Make that mistake as hard as you can. Note that there is currently **no per-record
  caveat field** to lean on — the only `caveats` in the schema is `Habitability.caveats`. So the
  record-level work has to be built: a generated `caveat` string per planet, a `derivation` block on
  each colour (`kind: modelled | measurement-derived`, `is_observation: false` for every record in
  the file, anchors included), `provenance_counts` in the header, and `modelled_hex` rather than
  `base_hex` — column names are the only documentation that survives `pd.read_parquet()`.
- **A licence: CC BY 4.0 — but scoped.** Apply it to *your derived output* (colours, spectra,
  palettes, instrument views), not to the whole file: `params.*`, `host_star.*`, `sky.*` and
  `discovery.*` are NASA Exoplanet Archive values passed through unchanged, and you can't
  CC-license data you don't hold rights in. Ship a per-source terms table instead of one blanket
  claim. Two hard prerequisites: the Archive's acknowledgement sentence must be live first (see
  [13](./13-credit-the-scientists.md) — this is a **blocker**, not a cross-reference), and the
  Cahoy 2010 grid's terms are still unverified, so keep `data/cahoy_grid/` **out of the deposit**
  and ask Roman SSC (`roman-help@ipac.caltech.edu`) whether the download carries any.
- **A machine-readable schema, not just prose.** `PlanetsFile.model_json_schema()` emits JSON Schema
  straight from the pydantic models — one line at build time. Publish it as `/schema/v5.json`,
  reference it via `$schema` in the file, and the data dictionary falls out of docstrings you have
  already written. Document the four things that are currently unreadable from outside:
  `spectrum.values` (units), the `grid` ID (380–780 nm at 5 nm, 81 samples), `srgb`/`xyz` (colour
  space and white point), and `luminance_y` (**normalised for display**, not physical brightness).
- **A flat tabular derivative.** `planets.parquet` + `planets.csv`, one row per planet. A single
  ~90 MB JSON blob is unpreviewable everywhere and is what makes the HF mirror pointless.
- **External identifiers.** `id` is a local slug; nothing in the file joins to anything else — no
  Archive `pl_name` as a key, no SIMBAD/Gaia/TIC host ID, no bibcode per source. This is the
  single biggest barrier to anyone combining the data with another catalogue.
- **A worked example.** Ten lines of Python that loads it and prints a palette. The difference
  between a dataset people use and one they don't is usually those ten lines.

Versioning: the data already has a schema version and a release tag. Carry both into the
dataset record so a citation points at a specific state of the world, not a moving target. Note
that neither identifies the *upstream* snapshot, which is the thing that actually moves —
`pscomppars` is a living table, so also record the TAP query, its timestamp and the git SHA in the
file header. (`PIPELINE_VERSION = "0.1.0"` is hard-coded and never bumped; don't rely on it.)

## The one thing that makes this more than housekeeping

Zenodo timestamps a record permanently. That's the mechanism behind the pre-registered
predictions play in [15-roman-launch.md](./15-roman-launch.md) — publishing the site's
predicted colours for Roman's targets *before* launch, with a DOI, so they can be checked
afterwards. That's a real scientific gesture and a guaranteed follow-up story, and it needs
this doc's infrastructure to exist first. If nothing else in this file happens, do the Zenodo
record for that reason alone.

Two conditions for the pre-registration to actually count: cite the **version** DOI, not the
concept DOI (only the version DOI guarantees the files didn't change), and the record must be
**public** — a restricted deposit's timestamp proves nothing to anyone.

## Timing

**One dependency, and it's hard:** [13-credit-the-scientists.md](./13-credit-the-scientists.md).
Depositing under CC BY while the Archive acknowledgement and the Payne et al. attribution are still
missing makes the existing breach worse, not neutral. After that, anytime — a good candidate for an
evening when you don't feel like writing copy. Ideally before [09-show-hn.md](./09-show-hn.md),
because "the dataset is on Zenodo under CC BY" is a sentence that plays very well with that
audience, and long before [15-roman-launch.md](./15-roman-launch.md) needs it.

## How we'll know it worked

- Zenodo/HF/Kaggle download counts — vanity, but a floor.
- **Derivative works.** The real metric. Search occasionally for the dataset name and for
  distinctive field names; every notebook, blog post or toy that turns up is worth more than a
  thousand downloads.
- **Citations.** Long shot, high value. If the DOI ever gets cited in a paper, that single event
  unlocks [04-wikimedia.md](./04-wikimedia.md) and changes how every scientist email in
  [13-credit-the-scientists.md](./13-credit-the-scientists.md) reads.
- Referrals from the dataset hosts, tagged where the platform allows a URL —
  see [99-tracking.md](./99-tracking.md).

## Risks

- **Misuse.** Someone will present modelled colours as observed ones, possibly in a way that
  embarrasses the project. Cannot be prevented, only mitigated — put the caveat everywhere,
  including inside the records.
- **Upstream licence terms.** Verify before republishing. This is the one part of this doc that
  needs care rather than speed. Where it stands after the review: the NASA Exoplanet Archive
  publishes no explicit data licence (its obligation is the acknowledgement sentence, not a
  restriction), Karkoschka 1998 is public domain via NASA PDS, and Payne et al. 2026 is CC BY 4.0 —
  not share-alike, so a CC BY 4.0 release is compatible provided attribution, a licence link and a
  note of changes travel with it. The **one open question is the Cahoy 2010 grid**: 305 CSVs
  redistributed in `data/cahoy_grid/` with no licence note and no terms page found upstream. Keep
  them out of the deposit until Roman SSC confirms.
- **Maintenance.** A dataset that's three schema versions behind the site looks worse than none.
  Either automate the mirror from the release, or state plainly that a given record is a
  snapshot of a specific release.

## Links

- [README.md](./README.md) — the hub
- [reviews/06-open-data-review.md](./reviews/06-open-data-review.md) — data-librarian review: the
  CC BY ruling with sources, the FAIR gaps, and the repository ruling
- [05-machine-readable.md](./05-machine-readable.md) — the same data as a live API surface
- [15-roman-launch.md](./15-roman-launch.md) — the pre-registered predictions depend on the DOI
- [04-wikimedia.md](./04-wikimedia.md) — a DOI is the gate that unlocks it
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — licence audit before publishing
- [09-show-hn.md](./09-show-hn.md) — a good detail to have ready on launch day
- [99-tracking.md](./99-tracking.md)
