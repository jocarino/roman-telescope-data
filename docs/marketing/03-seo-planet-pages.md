# SEO on the planet pages — the compounding one

**Status:** not started — **own session, it's a code change** · **Effort:** one focused session · **Payoff:** high, slow · **Hub:** [Marketing plan](./README.md)

## The bet

~5,700 planet pages already exist. People type *"what does Kepler-186f look like"* and
*"what colour is HD 189733b"* into a search box every day, and right now the page that answers
that better than anything on the internet isn't phrased in those words. Fixing the phrasing is
a template change. Unlike every other channel here, this one keeps paying with no ongoing
effort, and it's the only one that still works when you get bored of posting.

Slow: expect months, not days. Start it early precisely because it's slow.

## What already exists (checked in the repo)

`web/meta.py` is further along than a typical project — don't rebuild it:

- Per-page `<title>`, `description`, Open Graph and Twitter tags, generated from the record so
  they can't go stale against the data.
- `sitemap.xml` and `robots.txt`, both emitted from the same module.
- Per-planet OG images at `/og/<id>.png`.
- Absolute URLs gated behind `--base-url` / `SITE_BASE_URL`; **the sitemap is skipped entirely
  when no base URL is configured.**

So this session is mostly *wording and structure*, plus one deployment check.

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

Keep titles under ~60 characters where possible so they don't truncate. Note the tension: the
question form is better for search, the hex form is better for the design audience who search
colours. Pick one, don't alternate.

**3. Make the first visible sentence answer the question directly.** The `<h1>` and the opening
line should state the planet, its modelled colour, and the one-clause reason, before any
interface. Search engines reward the direct answer; so do humans who bounced in from a search.

**4. Add JSON-LD structured data.** `CreativeWork` / `Dataset` per planet page, plus
`ImageObject` for the render, plus `BreadcrumbList`. This is also the foundation of
[05-machine-readable.md](./05-machine-readable.md) — do them in the same session, they share
the plumbing.

**5. Internal linking.** Every planet page should link to a handful of genuinely related planets
(same colour family, same host-star type, nearest neighbour in the sky, next stop on any tour
it appears in). Isolated pages don't get crawled deeply; a well-linked graph does. This is also
the single biggest lever on the "opens a second page" metric that every other doc here judges
itself by.

**6. Decide on the reverse colour index (`/color/4a6ea9`).** Big potential: designers search hex
codes constantly and there is almost no competition for "which planet is this colour". Real
risk: thousands of near-identical generated pages is precisely the pattern search engines
penalise as doorway content. **The honest verdict: only build it if each page is genuinely
useful** — the nearest planet *plus* a real palette, the colour's name, near-matches, and a
reason to stay. If it would be a thin lookup, don't. Consider quantising coarsely (a few hundred
pages, not 16 million) as the safe version.

**7. Check what the gallery does to crawlers.** The gallery is Alpine-driven and detail
fragments load via htmx. Confirm every planet page is reachable by a plain `<a href>` from a
static page — if the only route in is JavaScript, most of the catalogue is effectively invisible
regardless of the sitemap.

**8. Page speed on the planet pages.** Already largely handled by the shared-assets work, but
verify the planet page specifically: crawl budget across 5,700 pages is real, and slow pages get
crawled less.

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

- **Thin generated pages.** The reverse colour index is the live danger. Read item 6 twice.
- **Titles that read as spam.** "What colour is X? BEST exoplanet colours" is how you lose the
  trust the whole project is built on. Plain and true.
- **Over-optimising.** This is a two-evening job with a long payoff, not a permanent project.
  Do the list, ship it, leave it alone for three months.

## Links

- [README.md](./README.md) — the hub
- [05-machine-readable.md](./05-machine-readable.md) — same session, shares the JSON-LD plumbing
- [01-newsjacking.md](./01-newsjacking.md) — dated news notes on planet pages feed this
- [09-show-hn.md](./09-show-hn.md) — do this first, so the inbound links land well
- [15-roman-launch.md](./15-roman-launch.md) — the terms to own, months ahead
- [06-open-data.md](./06-open-data.md) — external links from dataset hosts help here
- [99-tracking.md](./99-tracking.md) — how to read the search numbers
