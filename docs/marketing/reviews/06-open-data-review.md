# Review — 06 Open the dataset

*Reviewed by a research data librarian (research data management / FAIR), 2026-07-30.*

## Verdict

**Right instinct, wrong order** — the doc plans where to mirror a file that is not yet legally open, not
self-describing, and not citable, and all three are upstream of the deposit.

## Can we actually license this CC BY?

**Ruling: yes, CC BY 4.0 is defensible — but only over the layer you made, and after two fixes.** The
file is not one work; it is two layers with different rights, and the doc licenses them as one.

**Layer 1, your derived output** (`true_colour`, `spectrum`, `palette`, `instrument_views`,
`phase_colours`, `sun_swap`, `habitability`): your code, your model choices, and no input imposes
share-alike or non-commercial terms. CC BY 4.0 is clean. **Layer 2, republished upstream facts**
(`params.*`, `host_star.*`, `sky.*`, `discovery.*` — NASA Exoplanet Archive `pscomppars` values passed
through unchanged): **you don't own these and can't CC-license them.** Claiming CC BY over the whole file
asserts rights you don't hold. That is the specific error the doc walks into.

Why republication is nonetheless low-risk:

- The Archive publishes **no explicit data licence**. Its acknowledgement page states the required ack
  sentence and the Christiansen et al. (2025) citation, and is silent on redistribution; re3data records its
  data licence as *"other"* (NASA's image-use policy), access *"open"*. "No stated licence" ≠ public domain —
  so state terms per source rather than blanket-claiming.
- The values are facts from refereed literature. In US law facts carry no copyright (*Feist*); compilations
  are protected only in original selection/arrangement, which you aren't copying.
- Under EU law — you are in Portugal, so this is what binds you — the sui generis database right subsists only
  where the maker is an EEA national/resident/body. Caltech/NASA is neither and no reciprocity agreement
  exists, so **the Archive's database has no sui generis protection against you.** Conversely *your* database,
  made in the EEA, does attract it — which is why your CC BY grant has teeth, since CC 4.0 licenses sui generis
  rights on the same terms as copyright.

The live Archive obligation is the **acknowledgement**, which per [13](../13-credit-the-scientists.md) appears
nowhere in the repo — making 13 a hard blocker here, not a cross-reference.

**Payne et al. 2026** (Zenodo 17470005, CC BY 4.0; redistributed verbatim in `data/measured_albedo/`):
CC BY is not share-alike, so adaptations may be released under CC BY 4.0 — compatible. The obligation is
attribution + licence link + indication of changes, currently unmet on the site. **Karkoschka 1998** via
NASA PDS: public domain, no obstacle.

**The one genuine "go check X": the Cahoy 2010 grid.** `data/cahoy_grid/` redistributes 305 CSVs with no
licence note, from `roman.ipac.caltech.edu`; I found no terms page (the sims page 404s). Model outputs by
US authors are facts — safe to *derive* from either way — but **redistributing the grid is a different act
from deriving colours**. Two checks: (1) ask Roman SSC (`roman-help@ipac.caltech.edu`, already a doc-13
contact) whether the tgz carries terms; (2) meanwhile **keep the Cahoy CSVs out of the deposit** — deposit
your own output plus a pointer, and the question disappears.

**Sources:** [Archive acknowledgement](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html) ·
[re3data r3d100010524](https://www.re3data.org/repository/r3d100010524) ·
[Directive 96/9/EC](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:31996L0009) ·
[CC FAQ](https://creativecommons.org/faq/) · `data/measured_albedo/README.md`

## What's missing for this to be usable

- **Findable / accessible.** No `LICENSE`, no `CITATION.cff` (`find -iname 'LICENSE*'` → zero hits), and no
  schema.org `Dataset` JSON-LD on the site — which is what feeds Google Dataset Search, a larger and more
  durable surface than Kaggle, from metadata you'd write for Zenodo anyway. A downloaded `planets.json` says
  nothing about its origin: the header is only `schema_version`, `grid`, `generated_at`, `planets`
  (`pipeline/emit/writer.py`) — no rights statement, no citation, no source list.
- **Interoperable — the worst gap.** `id` is a local slug and nothing carries an external identifier: no Archive
  `pl_name` kept as a key, no SIMBAD/Gaia/TIC host ID, no bibcode or DOI per source. Users can't join this to any
  other astronomical table. The project has already been bitten internally — the Roman board had to join by
  explicit `catalog_id` because names don't slug-match.
- **Reusable.** Three unrelated version numbers: `SCHEMA_VERSION = 5`, `PIPELINE_VERSION = "0.1.0"` (hard-coded
  in `pipeline/config.py`, never bumped — not a version in any useful sense), and the tag `data-20260727-1038`.
  None identifies the *upstream snapshot*: `pscomppars` is a living table, so two releases a month apart aren't
  comparable and nothing says so. Record the TAP query, its timestamp and the git SHA in the header.
- **Units and vocabularies.** Better than most deposits: field names carry units (`teff_k`,
  `radius_r_earth`, `semi_major_axis_au`, `center_nm`) and the enums are genuine controlled vocabularies
  (`Provenance`, `DataSource`, `ColourMethod`, `Confidence`, `HabitableZoneClass`, `SurfaceClass`). But they
  exist only in Python docstrings, and four things are undocumented and misreadable: `spectrum.values`
  (geometric albedo? dimensionless?); `grid: "cie-vis-380-780-5"` (380–780 nm at 5 nm, 81 samples — a code
  comment only); `srgb`/`xyz` (no white point, transfer function or colour space stated); and `luminance_y`,
  which per CLAUDE.md is **normalised for display** — read as physical brightness it is simply wrong, and
  nothing warns you.
- **Machine-readable schema + format.** `PlanetsFile.model_json_schema()` emits JSON Schema from the pydantic
  models you already wrote: one line at build time, published as `/schema/v5.json` and referenced via
  `$schema`, and the data dictionary falls out of the docstrings for free. Separately, one ~90 MB JSON blob is
  hostile and unpreviewable — a flat `planets.parquet` + `.csv` (one row per planet) is what users want.

## Describing modelled vs measured

The doc says "keep the caveat field in the records themselves". **There is no such field** — only
`Habitability.caveats`. Fix that before it becomes a plan.

The deeper problem: `provenance` is one enum per *record*, but a record mixes registers. A solar-system
anchor is `measured-albedo` — yet its illuminant is modelled and its colour computed. No swatch in this
file is a photometric observation of a planet's colour, and record-level flags can't express that.
`ParamSources` already does the right thing per-parameter for inputs; extend the pattern to outputs.

1. **`derivation` block on every colour object**: `{kind: "modelled" | "measurement-derived",
   albedo_source, illuminant_source, is_observation: false}`. `is_observation` is `false` for every record,
   anchors included. A constant-false field sounds silly; it's the field a downstream filter looks for, and
   its constancy *is* the honest answer.
2. **Rename so a careless join can't launder it.** `base_hex` reads like a fact; `modelled_hex` reads like what
   it is. Column names are the only documentation that survives `pd.read_parquet()` — a stronger misuse control
   than any README. Keep and extend the `assumed_*` prefix, which is already correct.
3. **A generated per-record `caveat` string**: "Colour modelled from an archetype albedo spectrum (parametric
   engine); no spectrum of this planet has been measured." ~5,700 rows, no copy to write, and it travels into
   every derivative that prints a row. Plus **`provenance_counts` in the file header**, so composition is
   visible before parsing.
4. **Lead the data dictionary with `model-microlensing` + `is_light_isolable: false`.** No light from those
   planets ever reaches Earth — the strongest honesty signal in the schema and the best worked example.
5. **Uncertainty is absent everywhere** except `BandSampleModel.uncertainty`. A colour with no error bar invites
   over-reading. Ideally a ΔE spread from varying assumed cloud state/metallicity; if that's out of scope, say so
   *in the field description* rather than leaving it silently absent.

## Repository choice — ruling

**Zenodo, and for the right reason.** The domain repositories are closed to this dataset today. **VizieR / CDS**
requires that "the data are related to a publication in a refereed journal, either as tables or catalogues actually
published, or as a paper describing the data and their context"
([CDS FAIR-journey guide](https://cds-astro.github.io/a-FAIR-journey-for-astronomical-data/aio.html),
[VizieR submit](https://vizier.iucaa.in/vizier/submit.htx)) — no paper, not eligible. The **NASA Exoplanet
Archive**'s contributed-data route is the same shape: it ingests parameters from refereed papers, not third-party
derived colour tables (confirm via the helpdesk; don't plan around it). **Harvard Dataverse** needs no publication
and has better variable-level metadata, but weaker recognition in astronomy — not worth splitting a solo
maintainer's effort. The upgrade path is real, though: a short data paper (*Astronomy & Computing*, or PSJ) turns
this into a catalogue in the astronomical record and unlocks VizieR. RNAAS would **not** qualify — not refereed.

**Hugging Face: conditional yes** — only once the flat Parquet exists, since HF's value is the dataset viewer and
its Croissant export, both of which need tabular data; a 90 MB JSON blob is a dead upload. **Kaggle: noise** —
competition/notebook audience, no prediction target here, no DOI, no way to express per-source terms. Do the
schema.org JSON-LD instead: larger reach, less work.

## Wrong or unverified

- **"keep the caveat field in the records themselves"** — no such field exists.
- **"already generated and already released"** — released with *no licence at all*: no `LICENSE`, no rights field
  in the JSON, no rights statement on the release. Default is all-rights-reserved. The data is not open yet,
  which reframes the whole doc. Relatedly, "a licence: CC BY 4.0" is listed as a README bullet — a rights
  statement belongs in the file header, the repo root and the deposit metadata.
- **"Connect the GitHub repo so each release archives automatically"** — a real trap. Zenodo's GitHub integration
  archives the **repo tarball**, and `data/planets.json` is gitignored (`.gitignore:15`), so the automatic archive
  would contain **no data**. Upload the asset manually.
- **"carry schema version and release tag into the record"** — right but insufficient; neither identifies the
  upstream Archive snapshot, which is the thing that actually varies.
- **Concept DOI vs version DOI never mentioned.** Zenodo mints a new persistent identifier per version "linked to
  all previous and future versions", so "if a researcher cite[s] the specific version, they can be sure the files
  did not change" ([Zenodo docs](https://help.zenodo.org/docs/deposit/manage-versions/)). The pre-registered Roman
  predictions in [15](../15-roman-launch.md) must cite the **version** DOI, and the record must be **public** — a
  restricted record's timestamp proves nothing.
- **Doc 13 is a blocker, not a cross-reference.** Depositing under CC BY while failing the Archive acknowledgement
  and the Payne attribution makes the breach worse, not neutral.

## Better approaches

1. **Make it legally open first.** `LICENSE` (CC BY 4.0 for data *and* a separate code licence — a mixed repo needs
   both), `CITATION.cff`, a `rights` + `sources` block in the JSON header, the Archive acknowledgement. One
   evening. Everything below is worthless without it.
2. **Emit JSON Schema from the pydantic models**, published at `/schema/v5.json` with `$schema` in the file.
   Near-zero work; turns the integer `5` into an actual contract.
3. **Ship the flat tabular derivative** (`planets.parquet` + `.csv`, `modelled_*` naming). Unblocks HF, previews
   and ~90% of real use.
4. **One Zenodo deposit, done properly**: concept DOI + a version DOI per release tag, per-source terms table in
   the description, your output only — no upstream raw files.
5. **schema.org `Dataset` JSON-LD on the site** → Google Dataset Search. Same metadata, bigger reach.
6. **Record the snapshot**: TAP query + query timestamp + git SHA in the header.
7. **HF mirror** once (3) exists. **Drop Kaggle**, or do it last and don't maintain it.
8. **Later: a data paper**, which unlocks VizieR/CDS and rewrites the doc-13 emails.

## The one thing I'd change

Stop treating the licence as a bullet in a README. This dataset currently has **no licence**, so it is not
open — and the doc's framing ("mirror the already-released file to three platforms") hides that. Reframe it
as: *make the file legally and technically re-usable, then deposit once, well.*

## What I edited

In `docs/marketing/06-open-data.md`, preserving structure, the `**Status:**` line and `## Links`: the Zenodo/GitHub
auto-archive trap; the "no licence today" correction; CC BY scoped to the derived layer with the Cahoy check named;
the non-existent "caveat field" claim replaced with the record-level design; the VizieR ruling and Kaggle downgrade;
concept vs version DOI; JSON Schema, flat tabular and external identifiers in "What to package"; doc 13 as a
blocker; a link to this review.
