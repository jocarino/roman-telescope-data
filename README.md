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
uv run python -m web.build --out dist --no-og   # …skipping the share cards (faster iteration)
python3 -m http.server 8799 --directory dist    # preview at http://localhost:8799
```

Long-pressing a gallery card peeks its detail fragment; Alpine.js drives search / filter / sort and
the true↔Roman toggle; palettes export as hex, CSS variables, or `.ase`. Also on the site: a
colour census of the whole catalog (`/census`), the Roman target board (`/roman` — see below),
a phase slider with an automatic full
lunar-cycle animation in the EXOSCOPE (per-planet random phases on the gallery), a "Seen in
fiction" overlay, and clean extensionless URLs. No backend, no build toolchain beyond Python.
`web.build` streams one planet at a time, so rendering all 5,764 pages takes ~13 s locally,
plus ~1 min for the share cards across cores (`dist/` ≈ 0.56 GB, of which the cards are
~165 MB; the runtime gallery index ≈ 2.5 MB).

### Sharing: Open Graph cards, sitemap, robots

The product is a picture, so a shared link has to unfurl as one. Every page carries its own
title, description, `og:*` and `twitter:*` tags (`web/meta.py`), and every planet gets a
1200×630 PNG card at `/og/<id>.png` (`web/og.py`) showing its lit disc, five-stop ramp and
base hex — the same render the page shows, because the card's disc is a numpy port of the
classic path of the WebGL shader in `web/static/planet-render.js`. The two are pinned against
each other in `tests/test_og_card.py`; if you change that shader's classic path, change the
port with it. Descriptions are generated from each record, never written by hand, and keep
the site's honesty rule — a microlensing planet's card says its light is never isolable.

`sitemap.xml` and `robots.txt` are emitted too. This matters more than usual here: the gallery
grid is client-rendered from a fetched index, so a crawler that only follows links sees ~150
planets out of 5,764.

**The canonical origin is a build input**, since the repo can't know it:

```bash
uv run python -m web.build --out dist --base-url https://your-domain    # or $SITE_BASE_URL
```

Without it the share tags still emit with root-relative paths (which most unfurlers resolve),
and `sitemap.xml` is skipped rather than published full of invalid relative URLs. The
`Dockerfile` takes it as the `SITE_BASE_URL` build arg — **set it on the deploy host**, or
production ships relative `og:image` URLs and no sitemap.

### Visitor analytics (PostHog, off by default)

The questions worth asking here aren't "how many hits" — they're *does anyone flip the Roman
switch, does the phase slider get dragged, which of the 5,764 worlds do people actually open,
and do the Roman colours get copied as often as the true ones*. Those are events, so the site
uses PostHog rather than a pageview counter.

**Nothing is emitted unless the build is given a key.** `--posthog-key` (or `$POSTHOG_KEY`)
gates the whole thing at render time: no key, no snippet, no `analytics.js`, no requests. That
is deliberate and load-bearing — every worktree serves its own `dist/` on its own port and the
mobile harness reloads pages in an iframe all day, and none of that should be indistinguishable
from a real visitor in the dashboard. `tests/test_analytics_build.py` asserts the absence as
hard as the presence.

```bash
uv run python -m web.build --out dist                      # analytics off — every local build
uv run python -m web.build --out dist --posthog-key phc_…  # what the deploy does
```

The `Dockerfile` takes it as the `POSTHOG_KEY` build arg; set it on the deploy host beside
`SITE_BASE_URL`. The token is a *project* token (`phc_…`) — public and write-only, meant to
ship in the page. Never put a personal API key there. `--posthog-api-host` /
`--posthog-assets-host` default to the EU cloud; override for US (`us.i` / `us-assets.i`).

What the install does and doesn't do (`web/static/analytics.js`):

- **Cookieless** (`cookieless_mode: "always"`), so there is no cookie to consent to and no
  banner on a site with no accounts and nothing to personalise. The honest cost: PostHog
  rotates its identifying salt daily, so one person visiting on two days counts as two —
  **visitor totals read high and retention is meaningless**. Pageview and event counts, which
  is what we ask about, are unaffected. This requires **"Cookieless server hash mode" to be ON**
  in the PostHog project (Project settings → Web analytics); without it events are dropped.
- **No autocapture, no session replay, no surveys, no heatmaps.** A DOM firehose answers none
  of the questions above and costs far more events.
- A fixed vocabulary: `$pageview`, `planet_viewed` (id + name), `roman_view_toggled`,
  `palette_copied` (format + which colour was on screen), `palette_downloaded`,
  `light_source_swapped`, `phase_changed` (debounced — a drag is one event, not forty),
  `peek_opened` (planet + view + `pointer`, so hold-to-peek can be told apart on touch from
  mouse), and the guided-tour funnel: `tour_started` (`tour_id`, `stops`, `entry_stop`),
  `tour_stop_viewed` (`stop`) and `tour_completed` (`stops_seen`). A tour page's pageview says
  someone opened a walk; only those three say whether anyone finished it — and `peek_opened`
  is the only signal at all from a gesture that fetches a fragment and never navigates.

Call sites use `window.exoTrack && window.exoTrack(…)`, the same guard as `window.exoToast`,
so an unkeyed build (or an ad blocker, which removes PostHog routinely) changes nothing about
how the page behaves. Adding an event is one guarded line at the call site plus a line in the
list above; keep the names readable a year out.

### The Roman target board (`/roman`)

The namesake page: the shortlist of exoplanets Roman's coronagraph could plausibly catch in
reflected light, each with the three-band colour we predict **and an empty slot beside it for
the colour Roman measures**. Plus a live countdown to launch (30 Aug 2026).

- **Words** are curated in `data/roman-targets.json`; **planet data** is re-joined against the
  current `planets.json` on every build (`pipeline/roman_board.py`), exactly like guided tours.
  Nothing is frozen, so the board cannot go stale as the catalog changes.
- **The join is by explicit `catalog_id`, never by slugging the published name.** The names do
  not always match ours — the literature's `pi Men b` is `HD 39091 b` (`hd-39091-b`) here. This <!-- factcheck: ignore -->
  is the alias problem `docs/roman-measured-data.md` flags for ingestion day, solved up front.
- **Targets we have no colour for stay on the board** as visibly empty rows saying why, rather
  than being dropped — an honest gap beats a tidy list.
- The eligible list is Table 4 of [Carrión-González et al. (2021)](https://arxiv.org/abs/2104.04296);
  26/10/3 planets qualify under its optimistic/intermediate/pessimistic scenarios. Per-planet
  access probabilities are deliberately **not** transcribed — the board computes the maximum
  angular separation itself (`1000·a/d` mas) from data every record already carries.
- **The slots fill themselves.** A slot flips from predicted to measured off the record's own
  `measured-cgi` provenance, which the swap seam sets the moment a real photometry file lands.
  Drop the file, rebuild — no edit to the template, the resolver, or the curated JSON.

### Real surface maps for the five anchors (`web/textures.py`)

Every planet's render draws its light-and-dark pattern schematically, because for an exoplanet
any pattern would be invention. The five solar-system anchors are the exception — we have flown
past them and mapped them — so their pages offer a third position on the **Source** knob:
*Modelled → Real map → Telescope*. In real-map mode the globe samples an actual equirectangular
map, so Jupiter gets its Great Red Spot, Earth its continents, Neptune its Great Dark Spot,
Uranus the blankness Voyager 2 really found, and Saturn its rings.

**On by default.** The five anchors open on their real map — on the gallery cards (the table
is inlined into `gallery.html` from `surface_maps_js()`) and on the planet page, so clicking a
card doesn't swap the picture out from under you. Turning the knob to *Modelled* is remembered,
so anyone who prefers the schematic globe keeps it. Cards with a map are also dealt from the
lit end of the phase range: past ~55° the crescent has eaten the geography.

**The colour claim does not change.** The shader multiplies every texel by
(derived colour ÷ the map's own mean), so the rescaled map averages to exactly the hex computed
from the spectrum. The morphology is real; the colour is still physics. `SurfaceMap.mean` in
`web/textures.py` is that divisor, and `tests/test_surface_maps.py` re-measures it against the
shipped file — regenerate a map without updating its mean and the suite fails rather than
letting the planet quietly render in the wrong colour.

To (re)fetch and prepare the maps — they are committed under `web/static/tex/`, ~230 KB total,
so this is only needed when changing a source:

```bash
python3 tools/prep_textures.py --out web/static/tex   # downloads, resizes, prints the means
```

Paste the printed means into `web/textures.py`. Sources are NASA (Blue Marble, public domain)
and Solar System Scope (CC BY 4.0); each map carries its own credit, licence and a plain-English
description of what it actually is, all shown on the page in real-map mode. This is curated at
**site-build time**, like the host-star lamp — adding a map needs no `planets.json` re-release.

### Jargon and the glossary

Every technical word on the site is defined once, in `data/glossary.json`, and used in two
places from that one source:

- **In place.** Templates wrap a term in the `g()` macro (`web/templates/macros.html`):
  `{{ g('albedo-spectrum', 'albedo spectrum') }}`. It renders a subtle pixel-dotted
  underline, and `web/static/glossary.js` shows the plain-English definition on
  hover, tap or keyboard focus. Events are delegated, so terms inside fetched peek fragments work too.
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
`GH_TOKEN=<read token>`). **Also add build arg `SITE_BASE_URL=https://<your domain>`** — see
"Sharing" above; without it the deploy has no sitemap and relative `og:image` URLs. Add
`POSTHOG_KEY=phc_…` too if you want visitor analytics — see "Visitor analytics" above; the
deploy is the only build that should ever carry it.

**Mount a volume at `/var/log/site`** (Dokploy: Application → Advanced → Volumes) or the
access log is thrown away on every deploy — see "The access log" below.

**The data artifact is NOT in git** (a 6k-planet build is ~90 MB): each pipeline run's
`planets.json` is published as a GitHub Release asset, and the committed one-line
`data/RELEASE` names the tag. Clean builds download it (`scripts/fetch_data.py`); local
checkouts with the file on disk use it as-is. A data refresh is:

```bash
uv run python -m pipeline build --bulk N     # regenerate data/planets.json
scripts/release-data.sh                      # upload as a release, update data/RELEASE
git add data/RELEASE && git commit && git push   # webhook redeploys from the new tag
```

### The access log

PostHog is JavaScript, and the audience this project most wants to count — crawlers, and the
assistants that quote the site — never runs JavaScript. A request line is the only evidence
that GPTBot fetched `/llms.txt` or that something pulled a JSON record. So nginx writes one:

```
2026-08-05T16:43:38+00:00 203.0.113.0 "GET /llms.txt HTTP/1.1" 200 5 "-" "GPTBot/1.2 (+https://openai.com/gptbot)" 0.000
```

Two details make it worth having. **The address comes from `X-Forwarded-For`, not
`$remote_addr`** — behind Dokploy's Traefik the latter is the proxy, identical on every line.
And **it is truncated to the network** (IPv4 /24, IPv6 /64): the log answers "was this a bot
and what did it fetch", never "who was this", and a truncated address still groups one noisy
crawler into one line-item.

It goes to two sinks: `/dev/stdout`, so `docker logs` and the Dokploy log pane work as
before, and `/var/log/site/access.log`, which is the durable one **only if that directory is a
mounted volume**. Without the mount nginx still writes the file, but it lives in the container
and dies with it on the next deploy. Not `/var/log/nginx`: the official image symlinks
`access.log` there to `/dev/stdout`, so a file written to that path would quietly go back to
the container log — `tests/test_nginx_log.py` guards that trap and the rest of the format.

Nothing in the image rotates it (~200 bytes a request); rotate on the host. Reading it:

```bash
awk -F'"' '{print $6}' access.log | sort | uniq -c | sort -rn | head   # user-agents by volume
grep -c '"GET /llms.txt' access.log                              # agent-facing endpoints
```

### Keeping it current (`pipeline drift`)

You don't have to remember any of that. `.github/workflows/catalogue.yml` probes the Archive
through Thursday (when new confirmations are published) and on Friday morning, and opens a pull
request when there is something to rebuild for. Nothing publishes itself: the release is created
as a **draft** and the `data/RELEASE` bump arrives as a PR, so merging stays the human step.

```bash
uv run python -m pipeline drift                       # has the Archive moved since the last release?
uv run python -m pipeline drift --baseline m.json     # …compared to a specific manifest
uv run python -m pipeline drift --emit-manifest data/manifest.json
uv run python -m pipeline drift --diff-against prev/planets.json   # what actually changed colour
```

Three things about it are deliberate and easy to break:

- **It fingerprints, it doesn't count.** `pscomppars` is a *composite* table that continuously
  re-derives each planet's best-available parameters, so a revision rewrites a row while the row
  count sits still. The probe sums the columns the pipeline consumes, so additions, removals and
  revisions all move it — for the same single query a bare count would have cost.
- **The gated set is defined once.** `catalog.GATE_CLAUSES` carries each completeness requirement
  as both a Python predicate *and* its ADQL equivalent, and `gate_adql()` composes the remote
  query from it. A hand-written mirror of the gate is how an earlier attempt concluded the
  catalogue was "560 planets behind" when the difference was the gate correctly excluding planets
  with no measurable host star. Don't retype it; `tests/test_drift.py` guards this.
- **The baseline is the last release, so there's no state to keep.** `manifest.json` ships beside
  `planets.json`, which means once a release is published the probe goes quiet by itself.
  `scripts/release-data.sh` writes it too, so a manual release doesn't break the chain.

`pipeline build` reuses `data/cache/records` for planets whose inputs are unchanged, so a refresh
only recomputes what moved. That cache keys on the **full** instrument definition, not just its
id — changing a bandpass centre or width changes every record's `instrument_views`, and keying on
`roman-cgi` alone would have served the old filter set out of cache with no error. Anything the
key doesn't cover (measured band samples, static observation data) still needs `--no-cache`.

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

### Checking the prose (`tools/factcheck.py`)

The catalogue is checked by tests; the *writing about* the catalogue was not, and that is where
this project's worst errors have been. A draft said a planet rendered near-black when its shipped
swatch is `#2fa1ff`; another listed a brown dwarf as a Roman target; a third quoted a planet count
the data had moved past. Each one contradicted something already sitting in the repo.

```bash
uv run python tools/factcheck.py docs README.md          # the public docs
uv run python tools/factcheck.py ../notes --repo .       # any prose, against this repo
uv run python tools/factcheck.py --json docs             # for CI
```

It treats the source tree and `planets.json` as the ground truth and reports where prose disagrees:
a **path or `CONSTANT` that doesn't exist** (with the file it probably moved to), an **object not in
the catalogue** (or catalogued under a different label, so a reader's search fails), a **colour word
that contradicts the planet's own swatch**, a **count** that has drifted, and — the one case it
cannot decide — a **measurement stated with no citation, limit or hedge beside it**, listed so a
human settles it deliberately. Exit status is 1 if any error survives.

Two rules keep it usable. It is deliberately quiet about honest English: "about 5,700 worlds" is
rounding, not error, and a hedged or wished-for colour is not a claim. And it never re-implements
what the pipeline already knows — it imports `catalog._display_name` and `colour.family` rather
than keeping a second copy of them, and says so when it can't (`uv run` matters here). Suppress a
line with `<!-- factcheck: ignore -->`, a file with `<!-- factcheck: off -->`; use them when a
sentence quotes an error on purpose. `tests/test_factcheck.py` pins one case per mistake actually
published, so a fix that stops catching one fails the suite.

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
- **`web/`** — Jinja2 static-site generator + Alpine.js, a pure static consumer of
  `planets.json` (no colour maths client-side). Renders a gallery, per-planet detail pages,
  and the long-press peek fragments into `dist/`.

### Conventions

- We do **not** white-balance to the host star, so a grey planet around the warm Sun reads
  cream. The swatch `hex` is a colour identity at a fixed display luminance
  (`BASE_SWATCH_LUMINANCE_Y = 0.6`) so low-albedo worlds don't render near-black; the true
  brightness is reported separately as `luminance_y` (planet luminance relative to a
  perfect-white planet under the same star).
- Colours are computed with the `colour-science` package; the science is honest — every
  colour records its model assumptions and reconstruction confidence.
