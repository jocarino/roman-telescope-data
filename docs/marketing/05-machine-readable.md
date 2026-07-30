# Machine-readable before human-embeddable

**Status:** not started · **Effort:** medium · **Payoff:** high and rising · **Hub:** [Marketing plan](./README.md)

## The bet

Your instinct here was better than the original idea. An embeddable widget waits for a blogger
to choose to embed it — a handful of times, maybe. Meanwhile a growing share of the question
*"what colour is Kepler-186f"* is now typed into an assistant, not a search box, and the answer
comes from whatever the model can read and cite. Being **the** machine-readable source for
exoplanet colour is a distribution channel that a static site can win outright, because
almost nobody in this niche has structured their data for it.

It's also the cheapest kind of marketing there is: no posting, no pitching, no audience
management. You publish files and they work while you sleep. And unlike the widget, it
compounds with [03-seo-planet-pages.md](./03-seo-planet-pages.md) — same plumbing, same session.

## What to build, ranked

**1. A markdown twin of every page.** `/planet/hd-189733-b.md` alongside the `.html`. Clean
prose, the numbers in a small table, the honesty caveat, no navigation chrome. Trivial to
generate — you already have the record and the description logic in `web/meta.py`. This is the
single highest-value item: it's what every crawler, scraper and agent would rather read, and it
guarantees they parse the caveat instead of losing it in markup.

**2. `/llms.txt`.** The emerging convention for telling a model what a site is and where its
canonical content lives. Small file: what the project is, the honesty rule stated plainly, the
data licence, and links to the key entry points and the full index. Add `/llms-full.txt` with
the whole catalogue in compact form if size allows. Fifteen minutes of work for a file that is
increasingly the first thing an agent fetches.

**3. A static JSON API.** `/api/planets.json` (the index) and `/api/planet/<id>.json` (the
record) — literally files on disk, no backend, served by the same nginx. Version it (`/api/v1/`)
so you can change your mind later. Document it on the press/credits page. This is what anyone
building a toy on top of your data will use, and every toy is a link back — see
[06-open-data.md](./06-open-data.md), which is the same data with a different distribution.

**4. JSON-LD on every page.** `Dataset` / `CreativeWork` per planet, `ImageObject` for the
render, `BreadcrumbList` for structure. Shared with the SEO session — do them together.

**5. Decide your robots policy deliberately, and probably allow.** Most sites are now blocking
`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`. For a project whose goal is for the
honest answer to be the one that spreads, **blocking is self-defeating** — you'd be opting out
of the channel this whole doc is about. Recommend: allow the assistant crawlers explicitly in
`robots.txt`, state the CC BY licence and the required attribution in `/llms.txt`, and keep
blocking only the abusive scrapers. Make it an explicit decision written down in `web/meta.py`,
not an accident.

**6. An MCP server.** *"Add the exoplanet colour tool to your assistant"* is a genuinely novel
thing to exist, it lands in the MCP directories where discovery is currently easy, and the
tool surface is small: look up a planet, get its colour and palette, search by colour, compare
true vs Roman. It's the only item here that's a real project rather than a file, so it goes
last — but it's the one people would actually talk about. Worth doing after the JSON API,
because the API is 90% of it.

**7. The human embed widget, still.** Not dead, just demoted. A one-line `<iframe>` showing a
planet's swatch and colour, with an "embed this" button on each planet page. Cheap, and the few
places that do embed it are exactly the astronomy blogs and teaching pages worth having. Build
it if an afternoon is free, not before items 1–4.

## Timing

Same session as [03-seo-planet-pages.md](./03-seo-planet-pages.md) for items 1, 2, 4 and 5 —
they're all `web/meta.py` and the build. Item 3 shortly after. Items 6 and 7 whenever.

Do this *before* [09-show-hn.md](./09-show-hn.md) if you can: "there's a JSON API and an
`llms.txt`" is precisely the detail that HN's audience likes, and someone will build something
with it in the thread.

## How we'll know it worked

This one is genuinely trackable, which is unusual for an SEO-shaped effort:

- **Referrals from `chatgpt.com`, `claude.ai`, `perplexity.ai`, `copilot.microsoft.com`** show
  up in normal referrer data. Watch that segment; it is the direct evidence that the machine
  channel is returning humans.
- **Requests to `/llms.txt`, `/api/*` and the `.md` twins** in the access logs — cheap proxy for
  agent interest, and it tells you which endpoints matter.
- **Spot-check by asking:** every month or two, ask a few assistants "what colour is
  HD 189733 b" and see whether the answer resembles ours and whether we're cited. Crude, but
  it's the actual objective.

Tag nothing here with UTMs — you can't tag a crawler. Referrer segments do the work. See
[99-tracking.md](./99-tracking.md).

## Risks

- **Getting quoted without attribution.** Inevitable; mitigate with the licence stated in
  `llms.txt` and in the JSON payloads themselves (an `attribution` field costs nothing).
- **The caveat getting stripped.** This is the real one. If an assistant reports our colour as
  fact without "modelled, not photographed", we've made the world slightly worse. Defence: put
  the caveat in *every* record and every markdown twin, not just the page footer — make it
  structurally impossible to take the number without the qualifier.
- **Conventions still moving.** `llms.txt` may not last. It costs fifteen minutes; don't
  over-invest in any single convention.
- **Bandwidth.** Static JSON is cheap, but an enthusiastic crawler on 5,700 endpoints isn't
  free. Check the nginx compression config is doing its job before opening the doors.

## Links

- [README.md](./README.md) — the hub
- [03-seo-planet-pages.md](./03-seo-planet-pages.md) — same session, shared plumbing
- [06-open-data.md](./06-open-data.md) — the same data, packaged for humans who build things
- [09-show-hn.md](./09-show-hn.md) — an API is a strong detail for that audience
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the licence and attribution wording should match across both
- [99-tracking.md](./99-tracking.md) — the assistant-referrer segment
