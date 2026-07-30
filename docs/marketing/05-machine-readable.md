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

One correction to the framing, though, because it changes how to judge this doc: **this is not a
traffic play.** Every AI chatbot combined sends about 0.29% of the search referrals Google does.
What the machine-readable surface buys is that when an assistant *does* answer "what colour is
Kepler-186f", the answer is ours and it still says *modelled*. Judge it on that, not on visits.

## What to build, ranked

**1. A markdown twin of every page.** `/planet/hd-189733-b.md` alongside the `.html`. Clean
prose, the numbers in a small table, the honesty caveat, no navigation chrome. Trivial to
generate — you already have the record and the description logic in `web/meta.py`. This is the
single highest-value item: it's what every crawler, scraper and agent would rather read, and it
guarantees they parse the caveat instead of losing it in markup.

Two things make the difference between twins that get read and twins that sit there unfetched.
Emit `<link rel="alternate" type="text/markdown" href="…">` in the HTML `<head>`, and list the
`.md` URLs in `sitemap.xml`. Content negotiation (`Accept: text/markdown`) is worth supporting
if nginx makes it easy, but don't rely on it: coding agents send that header, production
crawlers do not — discovery in practice happens via the alternate link and the `.md` suffix.

**2. Stable identifiers on every record.** The one thing that decides whether an outside system
can *use* this data rather than merely read it: can it tell that our `HD 189733 b` is its
`HD189733b`? Carry the NASA Exoplanet Archive `pl_name` verbatim, the host star's Gaia DR3 and
SIMBAD identifiers, and `sameAs` links to Wikidata where a QID exists. An afternoon's work, and
it is worth more than items 5–7 put together. Machine-parseable licensing belongs here too:
a `license` URL (`https://creativecommons.org/licenses/by/4.0/`) in the JSON-LD *and* in every
JSON payload — a licence stated only in prose is a licence no machine can honour.

**3. A static JSON API.** `/api/planets.json` (the index) and `/api/planet/<id>.json` (the
record) — literally files on disk, no backend, served by the same nginx. Version it (`/api/v1/`)
so you can change your mind later. Keep unit-suffixed key names (`radius_r_earth`,
`equilibrium_temp_k`) exactly as the pipeline has them: there is no standard unit code for Earth
radii, so the key name *is* the unit contract. Pin the payload to the `data-YYYYMMDD-HHMM`
release tag it was built from, since `data/planets.json` is not committed and the two will
otherwise diverge silently. Document it on the press/credits page. This is what anyone building
a toy on top of your data will use, and every toy is a link back — see
[06-open-data.md](./06-open-data.md), which is the same data with a different distribution.

**4. JSON-LD on every page — but only the types anything consumes.** `Dataset` per planet (this
is what Google Dataset Search reads), `BreadcrumbList` for structure, and `ImageObject` with
`license`, `creditText` and `acquireLicensePage` on the renders — that last set is the one
licence signal Google actually surfaces, and this is an image-heavy site. `CreativeWork`,
`Observation`, `measurementTechnique` and `marginOfError` are valid markup with no consumers;
emit them only because extractors lift whole JSON objects, never expecting a product to read
them. Shared with the SEO session — do them together.

**5. Decide your robots policy deliberately, and allow.** The "everyone is blocking" story is
overstated: as of Q1 2026 `GPTBot` appears in about 5.5% of `robots.txt` disallow rules,
`CCBot` 5.1%, `ClaudeBot` 4.9%. The mass-block is mostly Cloudflare's managed-`robots.txt`
default, not a publisher trend. For a project whose goal is for the honest answer to be the one
that spreads, **blocking is self-defeating** — you'd be opting out of the channel this whole doc
is about.

Three details matter more than the allow/block call itself:

- `ChatGPT-User`, `Claude-User` and `Perplexity-User` are **user-triggered fetchers**, not
  crawlers — they fire when a person pastes our URL into an assistant. Never block those,
  whatever you decide about training crawlers. That's the best experience this site can produce.
- `Google-Extended` **does not affect AI Overviews** (those are served from the ordinary
  Googlebot index) and never fetches anything itself. It's a training/grounding token only.
- Bandwidth is a non-issue for text and a real one for images: ~5,800 markdown twins at ~2 KB is
  ~12 MB for a full crawl. The number to watch is `/og/`. Cache-control there, not everywhere.

State the CC BY licence and the required attribution in `robots.txt`, `/llms.txt` and the JSON
payloads. Make it an explicit decision written down in `web/meta.py`, not an accident.

**6. `/llms.txt`.** The proposed convention for telling a model what a site is and where its
canonical content lives. Be clear-eyed: no major AI company — OpenAI, Google, Anthropic, Meta,
Mistral — has committed to reading it, and log studies of hundreds of millions of AI-bot
requests find it fetched a few hundred times; crawlers do not probe for it. Its real users are
coding assistants pointed at documentation sites. Still worth fifteen minutes, because it costs
fifteen minutes: what the project is, the honesty rule stated plainly, the data licence, links
to the key entry points. Don't build `/llms-full.txt` until something asks for it.

**7. An MCP server — as a local stdio wrapper, not a hosted service.** *"Add the exoplanet
colour tool to your assistant"* is a genuinely novel thing to exist, and the tool surface is
small: look up a planet, get its colour and palette, search by colour, compare true vs Roman.
But the registries list 20,000+ servers with no meaningful discovery, so a listing is not a
distribution channel, and a hosted server turns a zero-maintenance static site into something
with uptime obligations. If you want the headline, ship a ~100-line `npx` stdio server that
wraps the static JSON files — no hosting, no SLA, and a good detail for
[09-show-hn.md](./09-show-hn.md). Do not host one.

**8. The human embed widget, still.** Not dead, just demoted. Build it as a *route*, not a
component: `/embed/<id>.html`, a real self-contained page that happens to look right in a small
`<iframe>`, with an "embed this" button on each planet page. Same build, no JS payload, no CORS.
Its value isn't the embeds — there will be few — it's that it hands a blogger a link with our
caveat inside it. Build it if an afternoon is free, not before items 1–4.

## Timing

Same session as [03-seo-planet-pages.md](./03-seo-planet-pages.md) for items 1, 4, 5 and 6 —
they're all `web/meta.py` and the build. Item 3 shortly after. Items 7 and 8 whenever.

Item 2 is the exception: identifiers come from the archive query, so it's a **data-side** change
(`pipeline/`, `data/`) and needs its own session per the worktree split in `CLAUDE.md`. Do it
first anyway — every later item is more valuable once the records are joinable.

Gating everything: **confirm `SITE_BASE_URL` is set on the deploy.** Without it `web/meta.py`
skips `sitemap.xml` entirely, and the sitemap is how the `.md` twins and `/api/*` get found at
all. [03](./03-seo-planet-pages.md) flags the same task; it's five minutes and it blocks the rest.

While you're in `sitemap_xml()`: give each URL its own `<lastmod>` from the data release rather
than one global value, so a recrawl doesn't read as "the whole site changed". `<changefreq>` and
`<priority>` can go — Google ignores both. A small `/api/v1/releases.json` listing the
`data-YYYYMMDD-HHMM` tags is the cheapest possible change feed.

Do this *before* [09-show-hn.md](./09-show-hn.md) if you can: "there's a JSON API and an
`llms.txt`" is precisely the detail that HN's audience likes, and someone will build something
with it in the thread.

## How we'll know it worked

This one is genuinely trackable, which is unusual for an SEO-shaped effort — but calibrate the
expectations first, or the numbers will read as failure. Across Cloudflare Radar in May 2026,
Google sent **87.6%** of all search referrals and *every AI chatbot combined* sent **0.29%**.
This is not a traffic channel. It is a channel for being right in the answer.

- **Caveat survival rate — the primary metric.** Every quarter, ask five assistants "what colour
  is HD 189733 b" and score whether the answer keeps the qualifier (modelled / computed / not
  photographed) and whether we're cited. That is the actual objective of this document, and
  unlike everything else on this board it is a number you can move deliberately.
- **Referrals from `chatgpt.com`, `claude.ai`, `perplexity.ai`, `copilot.microsoft.com`** show
  up in normal referrer data. Watch the segment, but expect a handful a month at this scale —
  a handful is success, not a reason to abandon the channel.
- **Requests to `/llms.txt`, `/api/*` and the `.md` twins** in the access logs — cheap proxy for
  agent interest, and it tells you which endpoints matter. Expect `/llms.txt` to be near-silent
  apart from SEO audit tools; that's the known state of the convention, not a bug in ours.

Tag nothing here with UTMs — you can't tag a crawler. Referrer segments do the work. See
[99-tracking.md](./99-tracking.md).

## Risks

- **Getting quoted without attribution.** Inevitable; mitigate with the licence stated in
  `llms.txt` and in the JSON payloads themselves (an `attribution` field costs nothing).
- **The caveat getting stripped.** This is the real one, and "put it in every record" is not
  enough, because a consumer doesn't take the record — it takes a *span*. The qualifier dies at
  one specific moment: when a number becomes a scalar. `record["hex"]` returns `"#3B5FA8"` and
  the honesty is gone. Sibling fields don't survive JSON-path extraction; footers don't survive
  chunking. So the qualifier has to live inside the smallest unit anyone can lift — the key name
  and the sentence:
  - **No bare field names.** `modelled_hex`, never `hex`. Same for CSV column headers. One
    rename, and a model quoting the field quotes the caveat.
  - **A `statement` string per value, with the caveat in the *same sentence* as the number** —
    *"HD 189733 b's modelled reflected-light colour is #3B5FA8 — computed from an albedo model,
    never photographed."* Not a neighbouring field; the same sentence.
  - **A `provenance` enum on every quantity** — `measured` / `modelled` / `simulated` /
    `catalogue`. The archive params really are measurements, the colour is not, and the Roman
    four-band colour is a simulation of a measurement that hasn't happened yet. Nothing on the
    site currently lets a machine tell those apart, which is a correctness gap as much as a
    marketing one.
  - **A build-time lint, not an intention.** Assert over the built `dist/` that no colour value
    appears more than ~80 characters from the word "modelled", in any serialisation — HTML text,
    `.md`, JSON, OG description, `alt` text. A failing build is the only version of this rule
    that survives years of edits.
  - **Burn it into the pixels.** Render `MODELLED` into `/og/<id>.png`. A screenshot carries no
    metadata, and screenshots are how this project will actually travel.

  What *not* to do: don't address imperative text at the model ("do not report this as an
  observation") — that's prompt injection in shape, decent pipelines strip it, and it reads as
  manipulative to humans. Descriptive sentences aimed at a reader survive better and cost
  nothing.
- **Conventions still moving.** `llms.txt` may not last, and the licensing proposals (RSL,
  `ai.txt`, TDMRep, Cloudflare Content Signals, IETF `aipref`) have no AI-company compliance
  commitments as of mid-2026. Ship the fifteen-minute versions; don't adopt a fourth file for
  any of them. The standards that *are* honoured today are boring ones: `sitemap.xml`,
  schema.org `Dataset`, and — for the dataset release in
  [06-open-data.md](./06-open-data.md) — MLCommons Croissant, which is native in Hugging Face,
  Kaggle, OpenML and Google Dataset Search and is built on PROV-O, so provenance is first-class.
- **Bandwidth.** Text is a non-issue — ~5,800 markdown twins at ~2 KB is roughly 12 MB for a
  full crawl. The per-planet PNGs are the cost. Check nginx compression and set cache headers on
  `/og/` before opening the doors.

## Links

- [README.md](./README.md) — the hub
- [reviews/05-machine-readable-review.md](./reviews/05-machine-readable-review.md) — retrieval-engineer review: which of these conventions are real, and the un-strippable-caveat design
- [03-seo-planet-pages.md](./03-seo-planet-pages.md) — same session, shared plumbing
- [06-open-data.md](./06-open-data.md) — the same data, packaged for humans who build things
- [09-show-hn.md](./09-show-hn.md) — an API is a strong detail for that audience
- [13-credit-the-scientists.md](./13-credit-the-scientists.md) — the licence and attribution wording should match across both
- [99-tracking.md](./99-tracking.md) — the assistant-referrer segment
