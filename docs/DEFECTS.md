# Defects found by the marketing review

Everything here was found while writing and reviewing [`docs/marketing/`](./marketing/) — sixteen
reviewers reading the plans found problems in the **project**, not the plans. None of it is
marketing work; it's a fix list.

Each item says what's wrong, where, how it was verified, and what it blocks. Items marked
**check** are things only you can confirm (deploy environment, third-party terms).

Grouped by what happens if you ship without fixing it. Ordered within each group by effort.
**Numbers are stable** — a fixed item moves to [Resolved](#resolved) and its number is not
reused, so a reference to "defect 6" means the same thing next month.

Item 1 carries a [background section](#background--what-these-numbers-actually-mean) explaining
the coronagraph concepts from scratch — read it before touching the band configuration or writing
anything public about Roman.

---

## P0 — we are currently saying something untrue

### 1. The Roman CGI band configuration was wrong — code fixed, release pending
**Where:** `pipeline/config.py` (the `ROMAN_CGI` band tuple and the comment block above it)
**Blocks:** [09 Show HN](./marketing/09-show-hn.md), [11 Bluesky](./marketing/11-bluesky-mastodon.md), [02 press kit](./marketing/02-press-kit.md), [15 Roman](./marketing/15-roman-launch.md), [13 credits](./marketing/13-credit-the-scientists.md) — all of them repeated the figure.

We shipped four bands: `575/10%`, `660/6%`, `730/6%`, `835/15%`. The flight configuration is
three supported bands, so every "as Roman would see it" swatch — the signature feature — was
computed through the wrong filter set. The code is now correct; only the data release is
outstanding (last checkbox below).

- [x] Drop `cgi-660` from the supported set
- [x] `cgi-730`: 6% → **15%**
- [x] `cgi-835` @ 15% → **`cgi-825` @ 10%**
- [x] **Fix the spec everywhere it's written down, or it regresses.** Done across 28 files —
      `CLAUDE.md` (the project instructions encoded the error, so a future session would have
      restored it), `README.md`, `docs/roman-measured-data.md`, the pipeline docstrings, the
      `tests/` fixtures, and the user-visible copy: `gallery.html` (including the band chips,
      which were four coloured squares and are now three), `how.html`'s bandpass diagram
      (rectangles re-derived from the plot's own nm→x mapping), `macros.html`, `census.html`,
      `roman.html`, `peek.html`, `data/glossary.json` and `data/tours.json`.
- [x] `tests/test_solar_system.py` asserted `len(samples) == 4` — the one place genuinely
      hard-coded to a band count, despite `config.py` claiming nothing was. Now asserts against
      `len(ROMAN_CGI.bands)` so it cannot go stale again.
- [ ] **Re-emit the catalogue and publish a data release.** The remaining step, and it is
      *yours*: `data/planets.json` is gitignored and ships via GitHub release, so publishing is
      an outward-facing action. **Until it runs, the site renders three-band copy over
      four-band numbers.** Roughly: `pipeline build --bulk 10000`, `scripts/release-data.sh`,
      then update `data/RELEASE`. Compute is quick — a full rebuild took a few minutes, not the
      20–30 min first estimated here.

      ⚠️ **Trap for the next session in this worktree.** `data/planets.json` on disk is already
      the re-emitted three-band build (5,773 planets), but `data/RELEASE` still pins
      `data-20260727-1038` — the four-band release of 5,764. **Running `scripts/fetch_data.py`
      silently reverts you to four-band data**, and the site will then render three-band copy
      over four-band numbers again with nothing to warn you. Either publish the release or
      re-run the build after any fetch.

The glossary term keeps its id `roman-4-band` deliberately — it is a URL anchor and appears in
three `seeAlso` lists; only the display text changed. Rename it only if you'll update the anchors.

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

---

#### Background — what these numbers actually mean

*Written for someone who hasn't read the coronagraph literature. Nothing here is assumed.*

**The problem Roman's coronagraph is solving.** A star is roughly a **billion** times brighter
than a mature Jupiter orbiting it in reflected light. Putting both in one image is like
photographing a firefly next to a lighthouse from a mile away. A **coronagraph** is the optical
trick that makes it possible: a set of masks inside the instrument that cancel the star's light
before it reaches the detector, while letting light from a slightly different direction through.
The measure of success is the **flux ratio** (also called **contrast**) it can reach — planet
brightness ÷ star brightness. Roman's Coronagraph Instrument (CGI) is a *technology
demonstration*: its job is to prove the technique works in space, not to survey planets.

**How close to the star it can look.** The relevant unit is **λ/D** — wavelength divided by
telescope diameter — which is the natural angular scale of diffraction, the fundamental blur
that any telescope imposes. For Roman (D = 2.4 m) at 575 nm, λ/D ≈ 0.05 arcseconds. No
coronagraph can see a planet arbitrarily close to its star; the closest it can work is called the
**inner working angle**. Roman's formal requirement is stated at 6–9 λ/D, i.e. roughly 0.3–0.44
arcseconds. This is why a planet can be famous and still be unobservable — GJ 1214 b orbits at
about a *thousandth* of an arcsecond as seen from Earth, so it's not marginal, it's four orders
of magnitude inside the reach. Angular separation, not fame, decides.

**What "575/10%" means.** A **bandpass** (or band, or filter) is a piece of glass that transmits
only a range of wavelengths and blocks the rest. It's specified by a **centre wavelength** and a
**fractional bandwidth** — the width as a percentage of the centre. So:

| Band | Written as | Actually spans | Where that is |
|---|---|---|---|
| 1 | 575 nm, 10% | 546–604 nm | green-yellow, near the eye's peak sensitivity |
| 2 | 660 nm, 15% | 611–709 nm | orange-red, eye still responds well |
| 3 | 730 nm, 15% | 675–785 nm | deep red, eye response falling off fast |
| 4 | 825 nm, 10% | 784–866 nm | **near-infrared — the eye sees nothing here** |

Our pipeline models each of these as a **top-hat**: 100% transmission inside the range, 0%
outside, a perfect rectangle. Real filters aren't rectangles — transmission rises, plateaus, and
falls with sloped shoulders, so people quote the **FWHM** ("full width at half maximum"), the
width measured where transmission has dropped to half its peak. That's the difference behind the
~2% disagreement noted above: the Primer quotes the *design* width, Bailey and Zellem quote the
*as-built measured* FWHM of the actual hardware. Both are correct answers to slightly different
questions. Top-hats are a defensible v1 approximation; just say that's what they are.

**Two different coronagraphs, not one.** CGI carries two architectures, and they are not
interchangeable:
- **Hybrid Lyot Coronagraph (HLC)** — a mask in the focal plane blocks the star's image, and a
  second stop in the pupil plane blocks the diffracted light that leaks around it. Narrow field
  of view, best raw contrast.
- **Shaped Pupil Coronagraph (SPC)** — instead of blocking the star, the telescope's pupil is
  reshaped so diffraction redistributes starlight *away* from a chosen region. Wider field, and
  it's the mode used for spectroscopy.

This is why the specification reads "Band 1 **with the hybrid Lyot**" — a band and a coronagraph
together define an observing mode. The same filter used with a different mask is a different mode
with different performance.

**"Formally supported" vs "best effort" — these are contract words, not forecasts.** Every NASA
mission has **Level-1 requirements**: the things it must demonstrate to be declared a success.
CGI's single L1 requirement is to image a point source at a flux ratio of at least 10⁻⁷, at
6–9 λ/D, around a star as bright as V = 5, in a 10% band centred below 600 nm. Everything else —
the other bands, polarimetry, spectroscopy — is listed as **best effort**, meaning *the hardware
is there and the team intends to use it, but the mission isn't contractually obliged to deliver
it.*

Two ways to misread this, and the reviewing astronomer flagged both:
- **Too generous:** the requirement guarantees no per-planet result at all. It's one
  demonstration on one astrophysical point source, which needn't even be a planet — a known
  stellar companion used as a test target satisfies it. Writing "one guaranteed number *per
  planet*" smuggles in a promise nobody made.
- **Too harsh:** "best effort" is *not* a probability estimate. The instrument completed
  ground testing in Bands 1, 3 and 4; there are standing working groups on observation planning,
  polarimetry and data reduction; and the Primer itself anticipates optical spectra of up to two
  exoplanets. Writing best-effort as "probably won't happen" is the mirror image of the hype
  we're correcting, and the people who spent a decade on those modes will read it as a sneer.

**Why the hardware for Band 2 exists but the band doesn't count.** The filters live on the
**CFAM** — Colour Filter Assembly Mechanism — a physical wheel that rotates a chosen filter into
the light path. All four filters are on that wheel, and the spectrometer even carries a second
**Amici prism** (a prism arrangement that spreads light into a spectrum without deflecting the
beam off-axis) for Band 2. What's missing is *ground testing*: it was never characterised before
launch, so it can't be an officially supported mode. Hence the precise phrasing — **installed but
untested**, not absent. Saying "not in the flight configuration" to someone who worked on that
wheel is the kind of error that ends a conversation.

**What "R ~ 50 spectroscopy" buys.** **Resolving power** R = λ/Δλ is how finely an instrument can
split wavelengths. R ~ 50 at 730 nm means resolution elements about 15 nm wide, so across the
109 nm of Band 3 you get roughly seven independent points. That is a coarse shape, not a spectrum
with absorption lines in it — enough to see a broad methane depression, not enough to identify
much.

**Why any of this changes our colours.** Our "as Roman would see it" pipeline takes the modelled
reflected-light spectrum, integrates it through each bandpass to get one number per band, then
reconstructs a colour from those few samples via the CIE colour-matching functions. So the band
set *is* the algorithm. Three consequences of the correction, and the third is the one to be
ready for:

1. **We lose a mid-visible sample.** Dropping 660 nm removes a band sitting where the eye still
   responds strongly. That's real colour information gone.
2. **Band 4 was never doing much and now does nothing directly.** At 825 nm the CIE
   colour-matching functions are effectively zero — human vision stops around 780 nm — so a
   near-infrared photometric point contributes almost nothing to a perceived colour. It still
   shapes the interpolated curve; it just doesn't colour it. Our old 835/15% band overlapped the
   visible by a sliver; 825/10% doesn't overlap at all.
3. **The colours get *better*, not worse — measured, and the opposite of what this doc first
   predicted.** An earlier version of this section reasoned from the band count that ΔE2000
   (our "how much colour identity survives Roman" number, where ~1 unit is a just-noticeable
   difference) would rise. It falls. Measured over the **whole catalogue** — the released
   four-band build against the re-emitted three-band one, joined by planet id:

   | | ΔE mean |
   |---|---|
   | old 4-band (wrong) | 17.96 |
   | corrected 3-band | **16.76** |

   **5,363 of 5,764 planets improved**, 401 got worse, and **4,424 swatches changed colour**.
   The best improvement was −6.3 (Kepler-632 b, ΔE 11.1 → 4.8); the worst regression in the
   entire catalogue was **+1.0** (HD 3167 d), so the fix is close to strictly better.

   *(An earlier revision of this section quoted a 247-planet sample — 221/247, mean 18.48 →
   17.31. Same conclusion, weaker evidence; the full-catalogue numbers supersede it.)*

   The likely mechanism — offered as a hypothesis, not a result — is that the win isn't the band
   count, it's **Band 3 widening from 6% to 15%**. The old 730/6% anchor was a 44 nm slit, and
   the old top anchor at 835/15% integrated 772–898 nm — mostly near-infrared, where albedo can
   diverge sharply from the visible red, yet it still dragged the interpolated curve across
   730–780 nm, which *is* visible. The corrected 730/15% band spans 675–785 nm, so the red end
   of human vision is now anchored by a value that actually represents it. That gain outweighs
   losing Band 2's anchor.

   **So the honest headline is not "a real filter set costs you more than you'd guess."** It's
   better than that, and more useful: *we had the instrument wrong, we fixed it, and the answer
   moved — here is the number, in both directions.* Do not reuse the "costs you more" framing
   that earlier drafts of the marketing docs were built on; it is not what the data says.

**One term used throughout, in case it's unfamiliar.** **Geometric albedo** is the fraction of
incident light a planet reflects straight back toward the observer, wavelength by wavelength.
It's the input to everything above: albedo spectrum × host-star spectrum = reflected light, and
that's what both the eye and Roman are sampling. It is *modelled* here, never measured — which is
the reason the honesty rule exists in the first place.

---

### 3. Three licence notices we are required to ship and don't — **fixed**
**Blocks:** [13 credits](./marketing/13-credit-the-scientists.md), and any CC-licensed release downstream.

All three are binding licence terms, not courtesies. Ten minutes total.

- [x] **Alpine.js (MIT)** — notice restored at the top of `web/static/vendor/alpine.min.js`
      (v3.14.8, `Copyright (c) 2019-2025 Caleb Porzio and contributors` + the full permission
      notice). Verified the file still parses.
- [x] **Silkscreen (SIL OFL 1.1 §2)** — canonical `OFL.txt` fetched from the upstream
      googlefonts/silkscreen repo and shipped **twice**: `web/static/fonts/` (served, so
      `/static/fonts/OFL.txt` goes out with the WOFF2) and `web/assets/fonts/` (the build-time
      TrueType copy the OG card renderer uses). Upstream's copyright line is
      *"Copyright 2001 The Silkscreen Project Authors"*, not the designer's name the README
      previously used alone — both now recorded.
- [x] **Payne et al. 2026 (CC BY 4.0, [Zenodo 17470005](https://zenodo.org/records/17470005))** —
      the `/how` citation now carries all five things §3(a)(1) asks for: named creators, the
      copyright notice, a link to the licence, a pointer to the warranty disclaimer (§5), and a
      hyperlink to the licensed material itself, plus the DOI and a statement of what we changed
      (interpolated to our 5 nm grid, otherwise unmodified). `data/measured_albedo/README.md`
      matches.

### 4. The project states no licence for its own output — **fixed**
**Where:** repo root — no `LICENSE`, no `CITATION.cff` (`find -iname 'LICENSE*'` → zero hits)
**Blocks:** [06 open data](./marketing/06-open-data.md) (can't deposit), [04 Wikimedia](./marketing/04-wikimedia.md), [02 press kit](./marketing/02-press-kit.md), [05 machine-readable](./marketing/05-machine-readable.md).

Default is all-rights-reserved, so `planets.json` **is not open today** and nobody may legally
reuse it — while four marketing docs already promise CC BY 4.0.

- [x] **`LICENSE` — MIT for the code**, with an explicit pointer saying it covers code only.
      MIT is a real choice, not a default: it's the most permissive option, it matches the
      ecosystem already vendored here (Alpine is MIT), and it imposes nothing on reusers.
      Swap to Apache-2.0 if you want the patent grant, or to a copyleft licence if you'd
      rather derivatives stayed open — it's a one-file change and nobody has relied on it yet.
- [x] **`LICENSE-DATA` — CC BY 4.0 for what we derive**, plus the two-layer explanation, a
      per-source terms table, the verbatim Archive acknowledgement, and the Cahoy open
      question. The attribution we ask for is *"Exoplanet Palette (jocarino), CC BY 4.0"* —
      and the word **"modelled"**, which matters more to this project than the credit does.
- [x] **`CITATION.cff`** — CFF 1.2.0, with the five upstream papers as `references` so a
      citing tool surfaces them too. ⚠️ The author is the git handle `jocarino`, not a real
      name: I wasn't going to guess your surname into a public citation file. Replace it when
      you're ready to be cited by it — the file has a comment saying so.
- [x] **`rights` + `sources` in the `planets.json` header**, generated from the new
      `pipeline/rights.py` (7 sources, the two field layers, the acknowledgement, the warranty
      disclaimer, and the honesty statement). A licence in a README is one nobody who
      downloaded the JSON ever sees. `pipeline/rights.py` is also the single source of truth a
      credits page can render from — see item 11.

**Licence ruling** from [reviews/06-open-data-review.md](./marketing/reviews/06-open-data-review.md):
the file is **two rights layers**. Your derived output (`true_colour`, `spectrum`, `palette`,
`instrument_views`, `phase_colours`, `sun_swap`, `habitability`) is cleanly CC BY 4.0. The
republished Archive fields (`params.*`, `host_star.*`, `sky.*`, `discovery.*`) are **not yours to
license** — state terms per source rather than blanket-claiming. Republishing them is low-risk
(no explicit Archive licence; facts uncopyrightable under *Feist*; and no EU sui generis right
attaches since the maker is US and you're in the EEA — while *your* EEA-made database does
attract one, which is what gives your CC BY grant teeth).

- [ ] **check — the Cahoy 2010 grid, and this is more live than it first looked.** The 305
      CSVs from `roman.ipac.caltech.edu` are **committed to the public repo** (`git ls-files
      data/cahoy_grid | wc -l` → 305), so we are redistributing them *now*, not only at deposit
      time. Deriving colours from published model output is uncontroversial; redistributing the
      files is the separate act we haven't cleared. Either ask `roman-help@ipac.caltech.edu`
      whether the archive carries terms, or stop shipping them in-repo and fetch at build time
      the way `planets.json` already does. Documented in `LICENSE-DATA` §5. The release path is
      already clear — `scripts/release-data.sh` publishes only `planets.json`.

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
- [ ] **Emit the instrument band set into the header too.** The 2026-08-03 band correction
      changed every `instrument_views` colour and ΔE without changing the record *shape*, so
      `SCHEMA_VERSION` stayed at 5 and a consumer pinned to v5 silently received `cgi-825`
      where it used to get `cgi-660` and `cgi-835`. A `bands` block in the header makes that
      self-describing instead of invisible. Recorded as a comment in `pipeline/config.py` for
      now, which is not the same thing.
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

## Resolved

Kept rather than deleted, so the record of what was wrong survives and the numbering stays stable.

### 2. Analytics have never recorded anything — **fixed, verified 2026-08-03**
**Was:** the PostHog project taxonomy contained only built-ins. Either `POSTHOG_KEY` (a
`Dockerfile` `ARG`) was unset on the Dokploy build, or *"Cookieless server hash mode"* was off in
project settings — in which case every event is dropped **silently, with no error**, which is the
failure mode `analytics.js` warns about.

**Now:** the taxonomy carries `planet_viewed`, `palette_copied`, `roman_view_toggled`,
`light_source_swapped` and `phase_changed`, alongside `$pageview` and `$web_vitals`. Ingestion is
working. (`exo_pipeline_selftest` and `exo_probe_no_optin` are also present — presumably the
probes used to diagnose it.)

**Worth keeping in mind:** because the failure is silent, a sudden zero is indistinguishable from
a quiet week. If the numbers ever look impossibly low after a launch, check the key and the
cookieless setting *before* concluding the launch failed. And two blind spots remain open as
[item 15](#15-two-blind-spots-in-event-tracking) — tour completions and hold-to-peek still fire
nothing, so those specific metrics are still fiction.

---

## Suggested order

**Evening 1 — stop being wrong.** Items 1 (band config + re-emit), 3 (three licence notices),
4 (`LICENSE` + `CITATION.cff`), 10 (email in the footer). Clears every binding breach and the one
factual error in the signature feature.

**Evening 2 — finish turning the lights on.** Items 7 (`Disallow: /fragments/`), 15 (the two
missing events), 16 (UTM check). Analytics now ingest; these close the remaining blind spots.

**Evening 3 — data hygiene.** Items 5 (catalogue refresh + cadence), 12 (self-describing header),
13 (Zenodo trap). Unblocks the dataset deposit.

**A weekend — the link graph.** Items 6, 8, 9, plus the 14 colour-family hubs. The slowest payoff
and the largest one; start it early.

**Whenever.** Items 11 (credits page, though `CITATION.cff` lands in evening 1), 14, 15, 17.
