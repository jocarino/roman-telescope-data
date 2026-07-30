# SEO on the planet pages — the compounding one

**Status:** not started — **own session, it's a code change** · **Effort:** one focused session · **Payoff:** high, slow · **Hub:** [Marketing plan](./README.md)

> **Reviewed** — see [reviews/03-seo-review.md](./reviews/03-seo-review.md). The review answers
> item 7 (planet pages are effectively *not* crawlable today), kills the reverse colour index,
> and re-ranks the list: the link graph is the blocker, not the wording.

## The bet

~5,700 planet pages already exist. People type *"what does Kepler-186f look like"* and
*"what colour is HD 189733b"* into a search box every day, and right now the page that answers
that better than anything on the internet isn't phrased in those words. Fixing the phrasing is
a template change. Unlike every other channel here, this one keeps paying with no ongoing
effort, and it's the only one that still works when you get bored of posting.

Slow: expect months, not days. Start it early precisely because it's slow.

**One correction to the bet, 2026.** These are informational, question-shaped, long-tail queries —
the class most affected by AI Overviews (2026 measurements: position-one CTR on AI-Overview
queries around 1.6%, down from 7.6%; zero-click medians near 80%). Ranking for the question is no
longer the payoff. Being the source the answer is built from is — which shifts weight toward
[05-machine-readable.md](./05-machine-readable.md) and toward image results, and away from title
copy. Also: for the handful of planets with real query volume the SERP is NASA and Hubble press,
and for the other ~5,690 names the volume is functionally zero. The corpus is worth having for
structure and citability, not for head-term coverage.

## What already exists (checked in the repo)

`web/meta.py` is further along than a typical project — don't rebuild it:

- Per-page `<title>`, `description`, Open Graph and Twitter tags, generated from the record so
  they can't go stale against the data.
- `sitemap.xml` and `robots.txt`, both emitted from the same module.
- Per-planet OG images at `/og/<id>.png`.
- Absolute URLs gated behind `--base-url` / `SITE_BASE_URL`; **the sitemap is skipped entirely
  when no base URL is configured.**

Three things the audit found that this list did not account for:

- **The `<title>` is defined twice** — `meta.py:150` *and* `templates/planet.html:3`, with
  `tests/test_meta.py` asserting they agree. A rewrite touches both files or the build goes red.
- **Canonical and internal links disagree on URL form.** `base.html:14` canonicalises to
  `/planet/<id>.html`; every internal link is extensionless `/planet/<id>`; nginx `try_files`
  serves both 200 with no redirect. Every internal link points at a non-canonical duplicate.
  Pick extensionless everywhere and change `meta.py`'s paths to match.
- **~5,700 `/fragments/peek/<id>.html` are served publicly** with no `<head>`, no canonical and
  no `noindex`, and `robots.txt` is `Allow: /` with nothing disallowed. Add
  `Disallow: /fragments/`.

So this session is *plumbing and link structure* first, wording second.

## What to do

**1. Verify `SITE_BASE_URL` is actually set on the deploy.** If it isn't, there is no sitemap
in production and everything below is much slower to take effect. Check this first — it's a
five-minute task that gates the rest.

**2. Rewrite the planet-page title to be the question people type.** Today it's
`f"{rec.name} · {SITE_NAME}"` — accurate, invisible. Search engines match the query's words.
Candidate patterns, decide in-session:
- `What colour is HD 189733 b? · Exoplanet Palette`
- `HD 189733 b — modelled colour #3B5FA8 · Exoplanet Palette`
- A hybrid: question form for planets with recognisable names, name-first for catalogue
  designations nobody searches conversationally.

Keep titles under ~60 characters where possible so they don't truncate — that is a SERP
display rule, not a ranking one. Correction to the reasoning above: "search engines match the
query's words" is out of date; titles are a modest CTR lever and a weak relevance signal, and
Google rewrites a large share of them anyway. So pick one pattern (name, colour word, hex),
change it once in both files, and never think about it again — do not run two patterns or
A/B it.

**3. Make the first visible sentence answer the question directly.** The `<h1>` and the opening
line should state the planet, its modelled colour, and the one-clause reason, before any
interface. Search engines reward the direct answer; so do humans who bounced in from a search.

**4. Add JSON-LD structured data** — minimally. `CreativeWork` / `Dataset` will not produce a
rich result for this content; the 2026 value is being parsed cleanly by AI answer surfaces, so do
one small block and stop. `BreadcrumbList` with no breadcrumb UI on the page is ceremony. Also
worth more than the JSON-LD: the planet page currently has one `<h1>` (the bare name) and **zero
`<h2>`s** — give the existing sections real headings. This is also the foundation of
[05-machine-readable.md](./05-machine-readable.md) — do them in the same session, they share
the plumbing.

**5. Internal linking.** Every planet page should link to a handful of genuinely related planets
(same colour family, same host-star type, nearest neighbour in the sky, next stop on any tour
it appears in). Isolated pages don't get crawled deeply; a well-linked graph does. This is also
the single biggest lever on the "opens a second page" metric that every other doc here judges
itself by.

**6. The reverse colour index (`/color/4a6ea9`) — decided: don't build it.** The hex-search
demand was assumed, not verified, and does not hold up; a page per hex is
template-with-variable-substitution over data we already have, which is the exact pattern the
2026 scaled-content enforcement targets; and the downside is a site-wide quality judgement on a
domain whose only asset is being trusted. Build instead: **(a)** the *tool* — one URL, a hex
input or picker that finds the nearest planets client-side against the index we already ship;
**(b)** if we want indexable colour pages, exactly the **14 family hubs** already in
`colour_family()` (`/colour/azure`, `/colour/near-black`, …), each with the real count, 100–200
words on the physics of that band, the top ~24 planets as static anchors, the family palette, and
links to adjacent families. Fourteen — not 4,096. Full reasoning in
[reviews/03-seo-review.md](./reviews/03-seo-review.md).

**7. The gallery is invisible to crawlers — confirmed, and this is the blocker.** The grid ships
empty (`gallery.html:412`); cards are anchors built in JS (`app.js:615`), 60 at a time, the rest
appended by an IntersectionObserver on scroll — and Googlebot renders but does not scroll. Static
`<a href>` into `/planet/` exist only on the 7 tour pages (≤10 stops each), the 25 `/roman`
slots, one link on `/how`, and the same-system sibling strip. **Order of 100–200 planet pages sit
in the crawlable link graph; the other ~97% are orphans**, discoverable only from a sitemap that
exists only if `SITE_BASE_URL` was passed to the Docker build. Fix by building the link graph
(item 5 + the 14 hubs), not by tuning the sitemap.

**8. Page speed — skip it as an SEO item.** 5,700 URLs is a small site; crawl budget is not the
constraint, link depth is. Core Web Vitals remain a tiebreaker between otherwise comparable
pages, and this site's problem is not being in the consideration set at all.

**9. Decide what *not* to index.** Thousands of records are three facts and a swatch — no mass,
no distance, unknown type. Those are the pages a scaled-content assessment lands on. `PageMeta`
already carries `noindex` and `in_sitemap` (`meta.py:63–67`); a data-completeness predicate is a
few lines. 2,000 confident pages beat 5,700 of which most are filler.

## Copy — title and description patterns to draft in-session

Descriptions are already generated from the record and read well; the main change is making the
first clause the answer, not the classification. Aim for: *"HD 189733 b is a hot Jupiter
orbiting an orange dwarf 64 light-years away. Its modelled reflected-light colour is a deep
azure, #3B5FA8 — sodium absorption eats the yellow. Modelled, not photographed."*

Keep the honesty clause in the description. It differentiates the snippet, and it's the reason
anyone trusts the click.

## Timing

Before Show HN ([09-show-hn.md](./09-show-hn.md)) — an HN front page produces a burst of
inbound links, and links are worth far more pointing at pages that are already structured
correctly. Also before [15-roman-launch.md](./15-roman-launch.md), by many months, because
ranking for "what will Roman see" is not a thing you can do in launch week.

## How we'll know it worked

Organic search entries per week, and the ratio of planet-page entries to homepage entries — a
healthy long tail means most arrivals land deep, not on the front page. Watch it monthly, not
daily; nothing here shows up inside two weeks. See [99-tracking.md](./99-tracking.md).

## Risks

- **Thin generated pages.** The reverse colour index was the live danger; item 6 now kills it.
  The remaining exposure is the thinnest few thousand planet records themselves — hence item 9.
- **Titles that read as spam.** "What colour is X? BEST exoplanet colours" is how you lose the
  trust the whole project is built on. Plain and true.
- **Over-optimising.** This is a two-evening job with a long payoff, not a permanent project.
  Do the list, ship it, leave it alone for three months.

## Links

- [reviews/03-seo-review.md](./reviews/03-seo-review.md) — the audit this doc was corrected from
- [README.md](./README.md) — the hub
- [05-machine-readable.md](./05-machine-readable.md) — same session, shares the JSON-LD plumbing
- [01-newsjacking.md](./01-newsjacking.md) — dated news notes on planet pages feed this
- [09-show-hn.md](./09-show-hn.md) — do this first, so the inbound links land well
- [15-roman-launch.md](./15-roman-launch.md) — the terms to own, months ahead
- [06-open-data.md](./06-open-data.md) — external links from dataset hosts help here
- [99-tracking.md](./99-tracking.md) — how to read the search numbers
