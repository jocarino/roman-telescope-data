# Open the dataset

**Status:** not started · **Effort:** low · **Payoff:** medium — and it unblocks two other things · **Hub:** [Marketing plan](./README.md)

## The bet

"The modelled visible colours of 5,700 exoplanets" is a dataset that does not otherwise exist.
Publishing it costs almost nothing — the file is already generated and already released — but
it reaches a crowd no other channel here touches: data people, notebook writers, generative
artists, students looking for a project. Every derivative they build is a link back, and unlike
a social post, a dataset keeps being discovered for years through the host's own search.

The strategic part is the DOI. A citable record turns "a website's claim" into "a published
source", which is the gate on [04-wikimedia.md](./04-wikimedia.md) and a large part of what
makes a scientist comfortable engaging in
[13-credit-the-scientists.md](./13-credit-the-scientists.md).

## Where to publish

**Zenodo — do this one first.** Free, CERN-run, permanent, and it mints a DOI. It's also the
only one that makes the data *citable*, which is the whole strategic point. Connect the GitHub
repo so each release archives automatically. This is a one-evening job with the longest tail of
anything in this plan.

**Hugging Face Datasets.** Fastest-growing discovery surface for anything data-shaped, good
search, a built-in preview, and the audience skews toward people who will actually build
something. Cheap to mirror.

**Kaggle Datasets.** Different audience again — students and notebook-writers. Kaggle rewards a
well-written data dictionary and an example notebook far more than it rewards the data itself,
so write one short notebook ("colour the catalogue, plot the hue distribution") and it does the
promotion for you.

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
  observations. Make that mistake as hard as you can: say it in the README, and keep the
  caveat field in the records themselves.
- **A licence: CC BY 4.0.** Permissive enough that people use it, attributed enough that the
  credit travels. Note where upstream licences constrain redistribution — check this against
  the audit in [13-credit-the-scientists.md](./13-credit-the-scientists.md) before publishing,
  since some inputs carry their own terms.
- **A worked example.** Ten lines of Python that loads it and prints a palette. The difference
  between a dataset people use and one they don't is usually those ten lines.

Versioning: the data already has a schema version and a release tag. Carry both into the
dataset record so a citation points at a specific state of the world, not a moving target.

## The one thing that makes this more than housekeeping

Zenodo timestamps a record permanently. That's the mechanism behind the pre-registered
predictions play in [15-roman-launch.md](./15-roman-launch.md) — publishing the site's
predicted colours for Roman's targets *before* launch, with a DOI, so they can be checked
afterwards. That's a real scientific gesture and a guaranteed follow-up story, and it needs
this doc's infrastructure to exist first. If nothing else in this file happens, do the Zenodo
record for that reason alone.

## Timing

Anytime — it has no dependencies. Good candidate for an evening when you don't feel like
writing copy. Ideally before [09-show-hn.md](./09-show-hn.md), because "the dataset is on
Zenodo under CC BY" is a sentence that plays very well with that audience, and long before
[15-roman-launch.md](./15-roman-launch.md) needs it.

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
  needs care rather than speed.
- **Maintenance.** A dataset that's three schema versions behind the site looks worse than none.
  Either automate the mirror from the release, or state plainly that a given record is a
  snapshot of a specific release.

## Links

- [README.md](./README.md) — the hub
- [05-machine-readable.md](./05-machine-readable.md) — the same data as a live API surface
- [15-roman-launch.md](./15-roman-launch.md) — the pre-registered predictions depend on the DOI
- [04-wikimedia.md](./04-wikimedia.md) — a DOI is the gate that unlocks it
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — licence audit before publishing
- [09-show-hn.md](./09-show-hn.md) — a good detail to have ready on launch day
- [99-tracking.md](./99-tracking.md)
