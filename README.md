# Exoplanet Palette

The colour scheme of every known exoplanet, derived from physics.

Each planet's visible colour is computed from its reflected-light spectrum
(geometric albedo × host-star spectrum) via CIE 1931 colour matching, then presented as a
designer palette. Every planet is shown two ways: its **true colour** (full model
spectrum) and **as Roman would see it** (reconstructed from the four Roman Coronagraph
bands, both computed at quadrature — a coronagraph never sees full phase) — the signature
feature is how much colour identity survives that filter set.

The production catalog models **5,759 planets** — every confirmed exoplanet in the NASA
Exoplanet Archive that passes the data-completeness gate (6,290 fetched, 531 excluded
because no colour could honestly be derived).

See `CLAUDE.md` for the domain background and the full architecture; plans and runbooks
live in `docs/`.

## Setup

Requires [`uv`](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync                       # create the venv and install deps
```

## Pipeline

```bash
uv run python -m pipeline build                 # real Exoplanet Archive catalog -> data/planets.json
uv run python -m pipeline build --source demo   # the three synthetic archetypes (offline)
uv run python -m pipeline build --limit 1
uv run pytest                                   # sanity gate, swap-seam, batch logic, export
uv run ruff check pipeline web tests
```

`build` prints each planet's true-colour hex, its Roman-view hex, the ΔE2000 between them
(how much colour survives Roman), and the derived palette, then writes `data/planets.json`.

## Web app (static site)

```bash
uv run python -m web.build --out dist           # render gallery + detail pages from planets.json
python3 -m http.server 8799 --directory dist    # preview at http://localhost:8799
```

htmx loads planet-detail fragments into a drawer; Alpine.js drives search / filter / sort and
the true↔Roman toggle; palettes export as hex, CSS variables, or `.ase`. Also on the site: a
colour census of the whole catalog (`/census`), a phase slider with an automatic full
lunar-cycle animation in the EXOSCOPE (per-planet random phases on the gallery), a "Seen in
fiction" overlay, and clean extensionless URLs. No backend, no build toolchain beyond Python.
`web.build` streams one planet at a time, so rendering all 5,759 pages takes ~7 s locally
(`dist/` ≈ 477 MB; the runtime gallery index ≈ 2.5 MB).

### Jargon and the glossary

Every technical word on the site is defined once, in `data/glossary.json`, and used in two
places from that one source:

- **In place.** Templates wrap a term in the `g()` macro (`web/templates/macros.html`):
  `{{ g('albedo-spectrum', 'albedo spectrum') }}`. It renders a 1-bit dither underline
  (one pixel on, one off — texture rather than a rule), and `web/static/glossary.js` shows the plain-English definition on
  hover, tap or keyboard focus. Events are delegated, so terms inside htmx fragments work too.
  Use `g()` for **terms**; keep the `[i]` info buttons for **controls** (knobs, view switches).
- **All together.** `/glossary` lists every term grouped by topic, searchable and deep-linkable
  (`/glossary#quadrature`). It is deliberately **not linked from the nav** — you reach it by URL,
  or by hovering a marked term.

`tests/test_glossary.py` fails if a template marks a term the glossary doesn't define, so the
two can't drift. Only the short tooltip text ships to every page (`glossary.terms.<build>.js`,
~14 KB); the long entries live on the glossary page.

### Previewing several worktrees at once (`tools/exohub.py`)

When two or more Claude Code sessions each serve their own `dist/`, it's easy to lose track of
which port is which worktree. `exohub` fixes that — stdlib-only, no deps:

```bash
python3 tools/exohub.py serve --build   # serve THIS worktree on its stable port
python3 tools/exohub.py dash            # live table: port -> worktree -> URL
python3 tools/exohub.py ports           # the stable port each worktree gets
python3 tools/exohub.py mprocs          # one labelled pane per worktree, in mprocs
```

- **Stable ports.** `main` always gets `8799`; every other worktree hashes its branch name to a
  fixed slot in `8800–8889`, so a given worktree keeps the same port run to run.
- **A branch badge on every page.** `serve` stamps a small `▟ <worktree> :<port>` badge (bottom-left,
  a different accent per worktree) into each served page, so the *browser tab itself* tells you
  which worktree you're looking at. Click it to hide.
- **`dash`** scans listening ports and maps each back to its worktree by the server's working
  directory, so it also identifies servers started the old way (`python -m http.server`); those
  show `⚠ off-slot` since they aren't on the stable port.
- **`mprocs`** writes a machine-specific `mprocs.yaml` (gitignored) and launches
  [mprocs](https://github.com/pvolok/mprocs) with a `dash` pane plus one `serve` pane per worktree.

## Deploy (Dokploy / any static host)

Multi-stage `Dockerfile`: a Python stage renders the site from `data/planets.json`, an
nginx stage serves it. `nginx.conf` handles clean URLs and `.ase` downloads. On Dokploy:
Application → connect the repo → Build Type `Dockerfile` → domain + container port 80 +
HTTPS → enable the auto-deploy webhook (if the repo is private, add build arg
`GH_TOKEN=<read token>`).

**The data artifact is NOT in git** (a 6k-planet build is ~90 MB): each pipeline run's
`planets.json` is published as a GitHub Release asset, and the committed one-line
`data/RELEASE` names the tag. Clean builds download it (`scripts/fetch_data.py`); local
checkouts with the file on disk use it as-is. A data refresh is:

```bash
uv run python -m pipeline build --bulk N     # regenerate data/planets.json
scripts/release-data.sh                      # upload as a release, update data/RELEASE
git add data/RELEASE && git commit && git push   # webhook redeploys from the new tag
```

```bash
docker build -t exoplanet-palette .             # reproduce the deploy image locally
docker run -p 8080:80 exoplanet-palette         # serve at http://localhost:8080
```

### Milestone-1 sanity gate

The three archetypes (synthetic albedo × Sun blackbody) land where the physics says they
should — enforced by `tests/test_sanity_gate.py`:

| Archetype | True colour | Reads as |
| --- | --- | --- |
| Cloudy Jupiter analog | `#d1cac6` (bright, warm) | warm off-white / cream |
| Deep-methane Neptune | `#b2d1da` (blue-green) | blue-green |
| Cloud-free hot Jupiter | saturated blue, `lumY≈0.07` | dark deep-blue (cobalt) |

## Architecture (v1)

- **`pipeline/`** — Python. Turns planet params into a reflected-flux curve on a fixed
  380–780 nm / 5 nm grid, converts it to a colour + palette, integrates it through the
  Roman CGI bands, reconstructs a colour from just those bands, and emits
  `data/planets.json`. The albedo source is behind a `SpectrumProvider` protocol; a router
  picks the best available engine per planet — the parametric engine (4,439 planets), the
  Cahoy 2010 grid (1,320), or PICASO (selected targets, via a committed spectrum cache).
  See `docs/spectrum-engines.md`.
- **The swap seam** (`pipeline/emit/build.py` → `pipeline/fetch/targets.py`): if a real
  measured file `data/cgi_measured/{id}.roman-cgi.json` exists it replaces the simulated
  band samples with zero downstream change; the planet's provenance flips
  `simulated`→`measured` automatically. Empty until Roman reports; the full ingestion
  procedure is `docs/roman-measured-data.md`.
- **The habitable-zone lens** (`pipeline/habitable.py`, rendered by `web/hz.py`): every
  planet is placed against its star's liquid-water zone using the Kopparapu et al. 2014
  climate limits, from the host star's Teff + radius and the orbital distance alone — no
  atmosphere is assumed, and none has been measured. Emitted as `habitability` on each
  record (zone, surface class, insolation, zone edges in AU, and the caveats that must be
  shown with any verdict). Drives the gallery's "Liquid water" filter (deep-linkable as
  `/?hz=water`), the card badge, and the orbit diagram on each planet page.
- **`web/`** — Jinja2 static-site generator + htmx + Alpine.js, a pure static consumer of
  `planets.json` (no colour maths client-side). Renders a gallery, per-planet detail pages,
  and htmx drawer fragments into `dist/`.

### Conventions

- We do **not** white-balance to the host star, so a grey planet around the warm Sun reads
  cream. The swatch `hex` is a colour identity at a fixed display luminance
  (`BASE_SWATCH_LUMINANCE_Y = 0.6`) so low-albedo worlds don't render near-black; the true
  brightness is reported separately as `luminance_y` (planet luminance relative to a
  perfect-white planet under the same star).
- Colours are computed with the `colour-science` package; the science is honest — every
  colour records its model assumptions and reconstruction confidence.
