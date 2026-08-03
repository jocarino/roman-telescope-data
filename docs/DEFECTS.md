# Defects found by the marketing review

Everything here was found while writing and reviewing [`docs/marketing/`](./marketing/) — sixteen
reviewers reading the plans found problems in the **project**, not the plans. None of it is
marketing work; it's a fix list.

Each item says what's wrong, where, how it was verified, and what it blocks. Items marked
**check** are things only you can confirm (deploy environment, third-party terms).

Grouped by what happens if you ship without fixing it. Ordered within each group by effort.

---

## P0 — we are currently saying something untrue

### 1. The Roman CGI band configuration is wrong
**Where:** `pipeline/config.py:83–86` (and the stale comment above it at `:76–77`)
**Blocks:** [09 Show HN](./marketing/09-show-hn.md), [11 Bluesky](./marketing/11-bluesky-mastodon.md), [02 press kit](./marketing/02-press-kit.md), [15 Roman](./marketing/15-roman-launch.md), [13 credits](./marketing/13-credit-the-scientists.md) — all of them repeat the figure.

We ship four bands: `575/10%`, `660/6%`, `730/6%`, `835/15%`. The flight configuration is three
supported bands. Every "as Roman would see it" swatch — the signature feature — is computed
through the wrong filter set.

- [ ] Drop `cgi-660` from the supported set
- [ ] `cgi-730`: 6% → **15%**
- [ ] `cgi-835` @ 15% → **`cgi-825` @ 10%**
- [ ] Re-emit the catalogue
- [ ] **Fix the spec everywhere it's written down, or it regresses.** The wrong numbers are also
      in `CLAUDE.md:39–40` (so the project instructions themselves encode the error) and in the
      example payload in `docs/roman-measured-data.md:25–26`.

**Verified against** the [Roman Coronagraph Primer, CPP, 8 Jan 2025](https://roman.ipac.caltech.edu/docs/RomanCoronagraphPrimer_Current.pdf), p.5, quoted verbatim in [reviews/15-roman-review.md](./marketing/reviews/15-roman-review.md).

Two things to get right in the wording, because they're what a CGI person would catch:

- **660 nm is not "absent from the flight configuration".** The CFAM wheel physically carries
  λ1 575/10%, λ2 660/15%, λ3 730/15%, λ4 825/10%, and the spectrometer holds a second Amici prism
  for Band 2. The correct statement is Bailey et al. 2021: *"Band 2 spectroscopy hardware will be
  installed, but will not be tested on the ground; hence, it is not an officially supported
  observing mode."* Same code change, defensible sentence.
- **`835 nm` and `6%` appear in no primary source.** They are our errors, not stale citations.
  Say that plainly if you write about it — it's the more honest disclosure.

**Decide and document:** sources disagree ~2% on widths — the Primer gives Band 3 = 15% / Band 4 =
10% (nominal filter spec); Bailey et al. 2021 gives FWHM 122 nm @ 730 nm (16.7%) and 94 nm @
825 nm (11.4%); Zellem et al. 2022 says 17% / 12% (as-built). Worth well under 1 ΔE, but cite
which you used.

### 2. Analytics have never recorded anything
**Where:** `Dockerfile` `ARG POSTHOG_KEY`, PostHog project settings
**Blocks:** [99 tracking](./marketing/99-tracking.md), and any judgement about any channel.

The PostHog project taxonomy contains only built-ins — no `planet_viewed`, no `palette_copied`,
no `roman_view_toggled`. There is no partial failure mode here, only zero.

- [ ] **check** — is `POSTHOG_KEY` actually set on the Dokploy build?
- [ ] **check** — is *"Cookieless server hash mode"* enabled in project settings? If it's off,
      every event is dropped **silently, with no error**. `analytics.js` warns about exactly this.

Fix this before Phase 1 or the launch teaches you nothing.

### 3. Three licence notices we are required to ship and don't
**Blocks:** [13 credits](./marketing/13-credit-the-scientists.md), and any CC-licensed release downstream.

All three are binding licence terms, not courtesies. Ten minutes total.

- [ ] **Alpine.js (MIT)** — notice stripped, not merely absent. Restore
      `Copyright © 2019-2025 Caleb Porzio and contributors` + the permission notice.
- [ ] **Silkscreen (SIL OFL 1.1 §2)** — ship `OFL.txt` beside the woff2. The condition does
      require it.
- [ ] **Payne et al. 2026 (CC BY 4.0, [Zenodo 17470005](https://zenodo.org/records/17470005))** —
      we redistribute it verbatim in `data/measured_albedo/` and give the visitor a name and a
      licence label only. §3(a)(1) also requires a copyright notice, a notice referring to the
      licence, a notice referring to the disclaimer of warranties, and **a URI or hyperlink to
      the licensed material**. This is the one real breach involving someone's *data*.

### 4. The project states no licence for its own output
**Where:** repo root — no `LICENSE`, no `CITATION.cff` (`find -iname 'LICENSE*'` → zero hits)
**Blocks:** [06 open data](./marketing/06-open-data.md) (can't deposit), [04 Wikimedia](./marketing/04-wikimedia.md), [02 press kit](./marketing/02-press-kit.md), [05 machine-readable](./marketing/05-machine-readable.md).

Default is all-rights-reserved, so `planets.json` **is not open today** and nobody may legally
reuse it — while four marketing docs already promise CC BY 4.0.

- [ ] `LICENSE` for the code (pick one) **and** a separate explicit line for the data and renders.
      A mixed repo needs both.
- [ ] `CITATION.cff` — scientists check for this file; it signals you know the norms.
- [ ] A `rights` + `sources` block in the `planets.json` header (currently only `schema_version`,
      `grid`, `generated_at`, `planets`).

**Licence ruling** from [reviews/06-open-data-review.md](./marketing/reviews/06-open-data-review.md):
the file is **two rights layers**. Your derived output (`true_colour`, `spectrum`, `palette`,
`instrument_views`, `phase_colours`, `sun_swap`, `habitability`) is cleanly CC BY 4.0. The
republished Archive fields (`params.*`, `host_star.*`, `sky.*`, `discovery.*`) are **not yours to
license** — state terms per source rather than blanket-claiming. Republishing them is low-risk
(no explicit Archive licence; facts uncopyrightable under *Feist*; and no EU sui generis right
attaches since the maker is US and you're in the EEA — while *your* EEA-made database does
attract one, which is what gives your CC BY grant teeth).

- [ ] **check** — the Cahoy 2010 grid. `data/cahoy_grid/` redistributes 305 CSVs from
      `roman.ipac.caltech.edu` with no licence note and no locatable terms page. Deriving colours
      from it is safe either way; *redistributing* it is a different act. Either ask
      `roman-help@ipac.caltech.edu`, or keep the CSVs out of any deposit and ship a pointer.

### 5. The catalogue is ~560 planets behind
**Where:** release `data-20260727-1038`
**Blocks:** [01 newsjacking](./marketing/01-newsjacking.md) — the commonest story is "new planet
discovered", which is precisely the one we cannot answer.

`pscomppars` holds 6,324; the site ships 5,764. New confirmations are missing by construction.

- [ ] Refresh, and set a cadence (the Archive publishes new confirmations on **Thursdays**)
- [ ] Note: `rowupdate` does **not** exist on `pscomppars` — that TAP query returns `ORA-00904`.
      Whatever staleness check you build, don't build it on that column.

---

## P1 — structural: the site is harder to find and to cite than it should be

### 6. About 97% of planet pages are orphans
**Where:** `web/templates/gallery.html:412`, `web/static/app.js:615`
**Blocks:** [03 SEO](./marketing/03-seo-planet-pages.md), and it caps every "opens a second page" metric.

The grid ships empty; cards are anchors built in JS, 60 at a time, the rest appended by an
`IntersectionObserver` on scroll — and Googlebot renders but does not scroll. Static `<a href>`
into `/planet/` exist only on the 7 tour pages, the 25 `/roman` slots, one link on `/how`, and the
sibling strip. Order of 100–200 pages are in the crawlable link graph.

- [ ] Build the link graph: related-planet links on every planet page (same colour family, same
      host-star type, nearest neighbour in the sky, next tour stop)
- [ ] Add the 14 colour-family hub pages from the existing `colour_family()` (`/colour/azure`, …)
      as static index pages
- [ ] **check** — is `SITE_BASE_URL` set on the Dokploy build? If not there is **no sitemap in
      production at all**, and the sitemap is currently the only route to those pages.

### 7. ~5,700 peek fragments are publicly indexable
**Where:** `/fragments/peek/<id>.html`, `robots.txt`
- [ ] Add `Disallow: /fragments/` — `robots.txt` is currently `Allow: /` with nothing disallowed.
      The fragments have no `<head>`, no canonical and no `noindex`.

### 8. Canonical and internal links disagree on URL form
**Where:** `web/templates/base.html:14` vs every internal link
- [ ] `base.html` canonicalises to `/planet/<id>.html`; internal links are extensionless
      `/planet/<id>`; nginx `try_files` serves both 200 with no redirect. Every internal link
      points at a non-canonical duplicate. Pick extensionless everywhere and change `meta.py`'s
      paths to match.

### 9. The `<title>` is defined twice
**Where:** `web/meta.py:150` and `web/templates/planet.html:3`
- [ ] `tests/test_meta.py` asserts they agree, so any rewrite must touch both files or the build
      goes red. Worth collapsing to one source before the SEO session.

### 10. There is no way to contact you
**Blocks:** [02 press kit](./marketing/02-press-kit.md), [12 newsletters](./marketing/12-design-newsletters.md), [15 Roman](./marketing/15-roman-launch.md).
- [ ] Put an email address in the footer. Five minutes, and today a journalist on deadline
      genuinely cannot reach you.

### 11. Scientific inputs are uncredited
**Blocks:** [13 credits](./marketing/13-credit-the-scientists.md) — and emailing any of these people before it's fixed is worse than not emailing.

Images and surface maps are credited exemplarily (`pipeline/observations.py`, `web/textures.py`
carry `credit` / `license` / `source_url` and render them). The science inputs are not.

- [ ] **NASA Exoplanet Archive** — required acknowledgement, verbatim: *"This research has made
      use of the NASA Exoplanet Archive, which is operated by the California Institute of
      Technology, under contract with the National Aeronautics and Space Administration under the
      Exoplanet Exploration Program."* Cite **Christiansen et al. (2025)**, *PSJ*,
      doi:10.3847/PSJ/ade3c2 (supersedes Akeson et al. 2013).
- [ ] **CDS / VizieR catalogue VI/42** — redistributed verbatim and powering every sky panel;
      missed by the first audit entirely. Requested wording plus original-author citation.
- [ ] **PICASO** — Batalha et al. 2019, *ApJ* 878, 70.
- [ ] **`colour-science`** — BSD-3-Clause; cite Zenodo 10.5281/zenodo.17837391.
- [ ] **Cahoy et al. 2010**, **Karkoschka 1998**, **Thorngren 2016** — courtesy, and the point of
      the project.
- [ ] Roman bandpass source — currently uncited. Cite the Primer, and say which width convention
      you used (see item 1).

Two structural notes worth taking: build `CITATION.cff` and a machine-readable `credits.json`
*first* and render the HTML page from them; and tie it to a test that asserts every `provenance` /
`spectrum_source` value the pipeline emits has a matching credits entry, so a new engine cannot
ship uncredited. Attribution files rot otherwise.

---

## P2 — data and instrumentation hygiene

### 12. `planets.json` doesn't describe itself
- [ ] Header carries no rights, citation or source list (`pipeline/emit/writer.py`)
- [ ] Three unrelated version numbers — `SCHEMA_VERSION = 5`, `PIPELINE_VERSION = "0.1.0"`
      (hard-coded in `pipeline/config.py`, never bumped), and the release tag — and **none
      identifies the upstream snapshot.** `pscomppars` is a living table, so two releases a month
      apart aren't comparable and nothing says so. Record the TAP query, its timestamp and the git
      SHA in the header.

### 13. The Zenodo GitHub integration would archive no data
- [ ] Zenodo's GitHub integration archives the **repo tarball**, and `data/planets.json` is
      gitignored (`.gitignore:14`) — so the automatic archive would contain no data. Upload the
      asset manually.

### 14. nginx keeps no durable access log
- [ ] `nginx.conf` sets no `access_log`, so it goes to container stdout and dies with the
      container. [05 machine-readable](./marketing/05-machine-readable.md) promises to measure
      `/llms.txt` and `/api/*` hits from it. Ship logs somewhere or drop the claim.

### 15. Two blind spots in event tracking
- [ ] `web/static/tours.js` contains **zero** tracking calls — you can see a tour started and
      nothing after, so "tour completions" is currently fiction.
- [ ] Hold-to-peek is a `fetch` of a static fragment: no navigation, no pageview, no event. It's a
      phone gesture, so the site is blindest exactly where mobile-heavy channels land. A
      `peek_opened` event closes the biggest gap on the site.

### 16. UTMs may be stripped before PostHog loads
- [ ] `web/static/sky.js:691` and `web/static/app.js:1187` call
      `history.replaceState(..., location.pathname)`. PostHog loads via the async stub, so on
      `/sky` and `/compare` the UTM can be gone before capture — and `/sky.html?planet=<id>` is
      the deep link the plan most wants shared. Five-minute network-tab check; fix is to preserve
      `utm_*` in those two calls.
- [ ] Separately, add a `history.replaceState` that strips `utm_*` **after** the pageview fires, so
      a URL copied from the address bar and re-shared doesn't misattribute the new audience to the
      old channel.

### 17. `nginx.conf`'s `gzip_proxied any` is load-bearing
- [ ] Not currently broken — but if it regresses behind Traefik, every gallery visitor pulls a
      ~2.8 MB uncompressed index instead of ~0.5 MB. Worth a comment in the file so nobody
      "tidies" it away before a traffic spike.

---

## P3 — facts we got wrong in our own drafts

Already corrected in the marketing docs; listed because they're the class of error this project
can least afford, and because two of them are *about our own code*.

- **WASP-12b's albedo** was stated as a measurement in a video script; Bell et al. published it as
  an **upper limit** — in the reveal frame, on the honesty project.
- **TrES-2 b** was described as rendering near-black, but `pipeline/config.py` sets
  `BASE_SWATCH_LUMINANCE_Y = 0.60` and normalises every base swatch to the same luminance. The
  honesty account would have been caught contradicting its own repo by anyone who clicked.
- **HIP 71618 B** was listed as a Roman prediction target; it is a ~60–65 M_Jup, 2700 K brown
  dwarf, so a reflected-light colour for it is a category error.
- A **"47 UMa in the Data Challenge"** claim referred to a *fictitious* injected system.
- **The five solar-system anchors** are Earth, Jupiter, Saturn, Uranus, Neptune — not Mars
  (`pipeline/solar_system.py`).
- **`_CGI_TARGETS`** already exists in `pipeline/catalog.py` (`47 UMa b`, `47 UMa c`, `ups And d`, `upsilon And d`)
  — take Roman exemplars from that set rather than picking a planet by hand.

## Documentation provenance

- The verbatim subreddit rule quotes in [10-reddit.md](./marketing/10-reddit.md) **cannot be
  re-verified programmatically** — Reddit now 403s unauthenticated requests to `about.json` and
  `about/rules.json`. One reviewer did retrieve rules through a working Redlib mirror, so it isn't
  impossible, but for a project whose position is honesty about provenance, screenshot each rules
  page into `docs/marketing/evidence/` before posting to that sub.
- Question to answer before Show HN: **how many of the 5,764 planets have a measured radius?**
  `pipeline/catalog.py` already tags Teq provenance `measured` / `computed` / `assumed`, so the
  counts are one query away. Walking into that thread without the number is the likeliest way to
  lose it on the merits.

---

## Suggested order

**Evening 1 — stop being wrong.** Items 1 (band config + re-emit), 3 (three licence notices),
4 (`LICENSE` + `CITATION.cff`), 10 (email in the footer). Clears every binding breach and the one
factual error in the signature feature.

**Evening 2 — turn the lights on.** Item 2 (analytics), 7 (`Disallow: /fragments/`), 16 (UTM
check). Now you can measure whatever you do next.

**Evening 3 — data hygiene.** Items 5 (catalogue refresh + cadence), 12 (self-describing header),
13 (Zenodo trap). Unblocks the dataset deposit.

**A weekend — the link graph.** Items 6, 8, 9, plus the 14 colour-family hubs. The slowest payoff
and the largest one; start it early.

**Whenever.** Items 11 (credits page, though `CITATION.cff` lands in evening 1), 14, 15, 17.
