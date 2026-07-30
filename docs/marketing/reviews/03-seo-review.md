# Review — 03 SEO on the planet pages

*Reviewed by a technical SEO, ten years on programmatic sites, two of them lost 80% of their traffic to a single update.*

## Verdict

Directionally right, factually incomplete, and aimed at the wrong half of the opportunity — the
doc optimises words on pages that no crawler can reach, while the actual blocker (an orphaned
link graph and a sitemap that may not exist in production) is items 1 and 7 of eight.

## What the code actually does

Every claim in "What already exists" checks out: `web/meta.py` emits per-page title, description,
OG/Twitter, `sitemap.xml`, `robots.txt`, `/og/<id>.png`, and the sitemap really is skipped when
`base_url` is empty (`web/build.py:855`). Beyond that:

- **The title lives in two places** — `meta.py:150` and `templates/planet.html:3`, which
  hard-codes the same string for the `<title>` tag; `tests/test_meta.py` asserts they agree. Any
  rewrite touches both files or the build goes red.
- **Planet pages are effectively not crawlable — this is the doc's open question, answered.**
  The gallery grid ships empty (`gallery.html:412`); cards are anchors built in JS
  (`app.js:615`), first batch 60 of a 150-planet boot slice, the rest appended by an
  IntersectionObserver on scroll. Googlebot renders JS but does not scroll. The only *static*
  `<a href>` into `/planet/` are: 7 tour pages at ≤10 stops (`tour.html:103`), the 25 `/roman`
  slots (`roman.html:140`), one on `/how`, the noindexed 404, and the same-system sibling strip
  (`macros.html:264`). Order of **100–200 planet pages sit in the crawlable link graph; the other
  ~97% are orphans**, discoverable only from a sitemap that exists only if `SITE_BASE_URL` was
  passed to the Docker build (`Dockerfile:40`).
- **Canonical and internal links disagree on URL form.** `base.html:14` canonicalises to
  `/planet/<id>.html`; every internal link is extensionless `/planet/<id>`; nginx `try_files`
  serves both 200 with no redirect. So every internal link points at a non-canonical duplicate —
  same for `/tours/<id>`, and `census.js:72` uses `.html` while `app.js:615` doesn't.
- **Index-bloat hazard the doc misses.** The build writes ~5,700 `dist/fragments/peek/<id>.html` —
  headless fragments, no `<head>`, no canonical, no `noindex` — served publicly, with `robots.txt`
  at `Allow: /`. Referenced via `data-peek` not `href`, so not link-followed, but Chrome-fetched
  URLs do get discovered. One robots line.
- **No JSON-LD anywhere.** The planet page has one heading — an `<h1>` with the bare planet name
  (`macros.html:214`) — and zero `<h2>`s. The 5,700 OG PNGs are never rendered as an `<img>` on
  the page and appear in no image sitemap.

## What's right

- "Don't rebuild `meta.py`" — correct. The description generator is good and already solved the
  duplicate-description trap (all seven TRAPPIST-1 planets shipping one sentence). Leave it.
- Item 5, internal linking. The most correct sentence in the doc, buried at #5 behind four
  things that matter less.
- Refusing to green-light the colour index without a quality bar.

## Gaps

1. **The orphan graph is the whole problem and it isn't framed as one.** A zero-authority domain
   with 5,700 sitemap-only URLs gets a fraction crawled and less indexed; "Discovered – currently
   not indexed" is the default outcome. Sitemaps aid discovery, they do not confer crawl
   priority — links do. Nothing in items 2–4 or 8 matters until a planet page is two hops from
   the homepage.
2. **`SITE_BASE_URL` gates more than the sitemap.** Without it, `canonical` and `og:url` go
   root-relative too. Relative canonicals are legal, but combined with the `.html`/extensionless
   split there is zero explicit signal about which URL form is real. Fix: pick extensionless
   everywhere — `try_files` already serves it — and change `meta.py`'s paths to match.
3. **Nobody has decided what *not* to index.** Thousands of records are three facts and a swatch —
   unknown type, no mass, no distance — precisely the pages a scaled-content assessment lands on.
   `PageMeta` already carries `noindex` and `in_sitemap` (`meta.py:63–67`); the predicate is ~5
   lines. 2,000 confident pages beat 5,700 of which most are filler.
4. **`Disallow: /fragments/`** is missing. Trivial, and the cheapest bloat prevention here.
5. **JSON-LD is scoped wrong.** `Dataset`/`CreativeWork` will not produce a rich result for this
   content; the 2026 value is being parsed cleanly by AI answer surfaces. Minimal version once,
   then stop; `BreadcrumbList` with no breadcrumb UI is pure ceremony.
6. **Image search is the unclaimed channel.** 5,700 distinct renders with honest generated alt
   text is a real asset, and image results are the surface AI Overviews have eaten least.

## Cargo cult to cut

- **"Search engines match the query's words."** That is 2015. Titles are a modest CTR lever and a
  weak relevance signal, and Google rewrites a large share of them anyway. Rewrite once — name,
  colour word, hex — then never think about it again. Do *not* run two patterns. And "under ~60
  characters" is a SERP pixel-width display rule, not a ranking rule.
- **Sitemap `priority` / `changefreq`.** Google has ignored both for years. `meta.py` emits them
  harmlessly; don't treat `priority="0.6"` as a lever and don't tune them.
- **Item 8, page speed for crawl budget.** 5,700 URLs is a small site; the constraint is link
  depth. Core Web Vitals in 2026 are a tiebreaker between otherwise comparable pages, and this
  site isn't in the consideration set at all. (Response time affects crawl *rate*; LCP doesn't.)
- **"Do it before Show HN so links land on well-structured pages."** Links accrue to the domain,
  not the title tag. Right sequencing, wrong reason: the real one is not spending a one-shot
  traffic spike on a site whose sitemap doesn't exist.

## The reverse colour index — ruling

**Kill it.** Not "only if each page is useful" — kill the page-per-hex form outright. Three
reasons, in order of severity. (1) The demand isn't real: designers pick colours in
pickers, and when they do type a hex into Google they want a converter, which Google answers
inline — hex-code SERPs are a known junk surface ("why does searching a random hex return car
dealers" exists because nothing legitimate targets those strings). (2) It is, definitionally,
template-with-variable-substitution over data you already have — the exact pattern named in
Google's scaled-content-abuse enforcement, where the March 2026 update took offenders down
60–90%. (3) The downside isn't "the pages don't rank", it's a site-wide quality judgement on a
domain whose entire asset is being trusted. You cannot buy that back.

**Build instead, in this order:**

- **The tool, not the index.** *One* URL — a hex input / picker folded into the gallery or a
  single `/colour` page — finding the nearest planets client-side against the index you already
  ship. Useful, shareable, zero doorway risk, and it is the "paste a hex" hook the README parked.
- **Fourteen family hubs, if you want indexable colour pages.** Exactly the 14 buckets already in
  `colour_family()`: `/colour/azure`, `/colour/near-black`, and so on. Each must carry: the real
  count, 100–200 words on the *physics* of why planets land in that band (methane, sodium, cloud
  decks — the site already knows this), the top ~24 planets as **static `<a href>` anchors** with
  their numbers, the family palette, and links to the two adjacent families. Fourteen — not
  4,096, not 16 million. They double as the internal-linking hubs the site is missing, which is
  why they're worth building even if they never rank.

## Wrong or unverified

- "People type *what colour is HD 189733b* every day" — for that planet, yes, and the SERP is
  NASA, Hubble press and 2013 news coverage. You will not outrank NASA on the one planet whose
  colour was measured. For the other ~5,690 names volume is functionally zero: maybe 20 planets
  with real interest and a long flat tail of none.
- "Hex-code searches are a real volume opportunity" — unverified in the doc, and false as far as
  the evidence goes. See the ruling.
- **The premise needs restating for 2026.** These are informational, question-shaped, long-tail
  queries — the class most affected by AI Overviews. 2026 measurements put position-one CTR on
  AI-Overview queries near 1.6% (from 7.6%), zero-click medians near 80%. Not worthless — the
  corpus is what gets you cited in those answers, and image and design-intent queries are far
  less affected. But "rank for the question" is no longer the payoff; "be the source the answer
  is built from" is, which pushes value toward
  [05-machine-readable.md](../05-machine-readable.md) and away from title copy.

## Better approaches

1. **The plumbing pass — half an evening.** Confirm `SITE_BASE_URL` is set on the Dokploy build
   (if it isn't, nothing else counts). Add `Disallow: /fragments/`. Make canonical, sitemap and
   every internal link agree on the extensionless form. Boring, gating, one sitting.
2. **The link graph — one evening.** A static "nearby in colour" block of 6–8 anchors on every
   planet page (computed at build from the index you already have), plus the 14 family hubs.
   Converts ~5,500 orphans into a connected graph two hops from the homepage. This is the doc's
   item 5 done properly, and it subsumes the colour index entirely.
3. **Decide what not to index — one evening.** A data-completeness predicate driving `noindex,
   follow` + sitemap exclusion. The strongest defence available against the failure mode to fear.
4. **Structure for extraction — one evening.** `<h1>` stays the name; add one direct answer
   sentence under it (the doc's item 3, right for AI answers rather than rankings); `<h2>`s on
   the existing sections; minimal JSON-LD. Then stop.
5. **Image search — one evening.** The planet's render as a real `<img>` with the alt text
   `meta.py` already generates, plus image entries in the sitemap.
6. **Twenty hand-written planet pages — ongoing.** The famous names, 150 words each of something
   NASA doesn't say. This is where the writing effort belongs, not in the template.

## The one thing I'd change

Stop treating 5,700 pages as 5,700 keyword targets. Nobody searches TOI-4562 c. The corpus's job
is structure and citability, not head-term coverage: build the link graph, index the ~2,000 pages
that carry real data, and spend the writing budget on the twenty planets that have demand.

## What I edited

In `docs/marketing/03-seo-planet-pages.md`: answered item 7 with the crawl-graph finding instead
of leaving it a question; noted the title is defined in two files and covered by a test; added
the canonical/URL-form mismatch and the `/fragments/` robots gap; replaced the item-6 hedge with
the kill ruling and the 14-hub alternative; corrected the crawl-budget framing in item 8; added
item 9 (what not to index); added the AI-Overviews caveat to "The bet"; corrected the
title-rewrite reasoning; linked this review from the Status line and `## Links`. No code touched.
