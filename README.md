# Exoplanet Palette

The colour scheme of every known exoplanet, derived from physics.

Each planet's visible colour is computed from its reflected-light spectrum
(geometric albedo × host-star spectrum) via CIE 1931 colour matching, then presented as a
designer palette. Every planet is shown two ways: its **true colour** (full model
spectrum) and **as Roman would see it** (reconstructed from the four Roman Coronagraph
bands) — the signature feature is how much colour identity survives that filter set.

See `CLAUDE.md` for the domain background and the full architecture; the working plan is in
`PLAN.md`.

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
the true↔Roman toggle; palettes export as hex, CSS variables, or `.ase`. No backend, no build
toolchain beyond Python.

## Deploy (Dokploy / any static host)

Multi-stage `Dockerfile`: a Python stage renders the site from the committed
`data/planets.json`, an nginx stage serves it. `nginx.conf` handles clean URLs and `.ase`
downloads. On Dokploy: Application → connect the repo → Build Type `Dockerfile` → domain +
container port 80 + HTTPS → enable the auto-deploy webhook. A data refresh is just a new
`data/planets.json` committed and pushed.

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
  `data/planets.json`. The albedo source is behind a `SpectrumProvider` protocol: v1 uses a
  parametric **synthetic** provider (`pipeline/spectrum/synthetic.py`); the Cahoy 2010 grid
  and PICASO slot in later without touching anything downstream.
- **The swap seam** (`pipeline/emit/build.py` → `pipeline/fetch/targets.py`): if a real
  measured file `data/cgi_measured/{id}.roman-cgi.json` exists it replaces the simulated
  band samples with zero downstream change; the planet's provenance flips
  `simulated`→`measured` automatically. Empty at v1.
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
