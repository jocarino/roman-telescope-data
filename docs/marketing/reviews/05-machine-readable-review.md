# Review — 05 Machine-readable

*Reviewed by an engineer who builds retrieval pipelines and the grounding layer for AI search — someone who has written the code that eats sites like this one.*

## Verdict

**Right bet, wrong ranking, and the one novel problem here is under-specified.** Two of the top five items are folklore, the thing that would make my pipeline able to *use* this site (stable join keys) isn't mentioned, and "put the caveat in every record" is a wish rather than a design.

## Which conventions are real

| Convention | Who actually honours it | Verdict |
|---|---|---|
| `llms.txt` | Nobody with an index. No public commitment from OpenAI, Google, Anthropic, Meta or Mistral as of Q1 2026. A study of 500M+ AI-bot requests found **408** hits on `llms.txt`; bots never probe for it where it's absent. Real users: coding agents (Cursor, Cline, Continue) pointed at *docs* sites. | **Folklore, but cheap.** 15 min, expect zero, displace nothing. |
| Markdown twins at `.md` URLs | Real — via **dedicated URLs**, not content negotiation. Claude Code / opencode send `Accept: text/markdown`; *no production crawler* does. Discovery is `<link rel="alternate" type="text/markdown">` plus the `.md` suffix convention. | **Real. Highest-value item — the doc is correct**, but omits the discovery link. |
| Static JSON API | Humans and agents, yes. Crawlers, no — nothing crawls a JSON tree it can't discover from HTML or the sitemap. | **Real, with a discovery caveat the doc misses.** |
| JSON-LD | Consumed narrowly: `Dataset` → Google Dataset Search; `BreadcrumbList` → SERP; `ImageObject` + `license`/`creditText`/`acquireLicensePage` → Google Images licensable badge (**real, and this is an image-heavy site — the doc omits it**). `CreativeWork`, `Observation`, `measurementTechnique`, `marginOfError` → valid, consumed by nothing; they matter only because extractors lift whole JSON objects. | **Half real.** Do the three; the rest is for extractors, not Google. |
| Explicitly allowing assistant crawlers | Mechanically honoured by the named bots. But the doc's premise is wrong: blocking is a **minority** posture — GPTBot appears in 5.52% of disallow rules, CCBot 5.08%, ClaudeBot 4.88%. The mass-blocking story is Cloudflare's managed `robots.txt` default (`ai-train=no`, ~3.8M zones), not publisher choice. | **Real. Ruling below.** |
| RSL, `ai.txt`, TDMRep, Cloudflare Content Signals | Published specs; as of mid-2026 **no major AI company has pledged RSL compliance**. IETF `aipref` is still a WG draft. | **Folklore for now.** CC BY in JSON-LD `license` + a robots.txt comment; don't adopt a fourth file. |
| Croissant (MLCommons) | **Genuinely consumed**: ~700k datasets, native in Hugging Face / Kaggle / OpenML / CKAN / Dataverse, indexed by Google Dataset Search, required at NeurIPS. Built on PROV-O, so provenance is first-class. | **The most real thing on this page, and the doc doesn't mention it.** |

## What's right

- **Demoting the widget below the machine surface.** Correct call, correct reasoning.
- **Markdown twins ranked #1.** The item I'd actually want as a consumer, and `planet_description()` already does the hard part.
- **Naming caveat-stripping as a risk at all.** Most plans in this genre never notice it.

## Gaps

- **Stable identifiers / join keys — the biggest omission.** My pipeline's first question is *"is this the same planet I already have?"* Today the answer is string-matching a display name, which fails constantly (`HD 189733 b` / `HD189733b` / `HD 189733b`). Every record needs the Archive `pl_name` verbatim, the host's Gaia DR3 and SIMBAD identifiers, and `sameAs` → Wikidata QID. **Worth more than `llms.txt`, the MCP server and the widget combined** — it's the difference between a page about a planet and a record I can merge.
- **No change feed.** `sitemap_xml()` takes one global `lastmod` for all ~5,800 URLs, so every recrawl looks like a full-site change. Per-URL `lastmod` from the release fixes it. Also: Google ignores `<changefreq>` and `<priority>` — `lastmod` is the only element read. Add `/api/v1/releases.json` listing the `data-YYYYMMDD-HHMM` tags.
- **Licensing a machine can parse.** "CC BY stated in `llms.txt`" is unparseable. Parseable: `"license": "https://creativecommons.org/licenses/by/4.0/"` in the JSON-LD *and* in every JSON payload, plus `creditText` / `acquireLicensePage` on `ImageObject`.
- **Units.** The Python side is already right (`radius_r_earth`, `equilibrium_temp_k`). Keep unit-suffixed key names in the public JSON; never emit `"radius": 1.13`. There is no UN/CEFACT code for Earth radii, so the key name *is* the unit contract.
- **`sitemap.xml` as a discovery surface.** The `.md` twins and `/api/*` belong in it. Undiscovered files are unfetched files.
- **The sitemap is gated on `SITE_BASE_URL`** (03 flags this too). Until it's set in production, everything here is slower. It's the actual first task.
- **Images travel with no caveat at all** — and images are what get screenshotted. See below.

## Making the caveat un-strippable

The doc's framing — *"put the caveat in every record"* — loses, because it assumes the consumer takes the record. It doesn't. It takes **a span**.

What actually happens downstream: your page is fetched, boilerplate-stripped, split into ~500-token chunks, embedded, retrieved, and a model is asked to answer with a citation. The qualifier dies at exactly one point: **when a number becomes a scalar**. `record["hex"]` returns `"#3B5FA8"` and the honesty is gone. Sibling fields (`"caveat": …`) don't survive JSON-path extraction. Footers don't survive chunking. `measurementTechnique` doesn't survive a model that was asked for a colour.

So the design rule is: **the qualifier must live inside the smallest unit a consumer can lift** — the key–value pair, and the sentence. Five moves, by leverage:

**1. Put the qualifier in the key name. There is no bare field.**
`"modelled_hex": "#3B5FA8"`, never `"hex"`. Chunkers keep keys adjacent to values, and a model quoting the field quotes the caveat. One rename; highest leverage on the page. Same for CSV headers — never ship a column called `hex`.

**2. Ship a `statement` string, with the caveat in the *same sentence* as the number.**

```json
"modelled_colour": {
  "hex": "#3B5FA8",
  "statement": "HD 189733 b's modelled reflected-light colour is #3B5FA8 — computed from an albedo model, never photographed.",
  "provenance": "modelled",
  "method_url": "https://…/how.html"
}
```

Not a neighbouring sentence: the *same* one. Sentence chunking, quote extraction and embedding all preserve intra-sentence adjacency and destroy inter-field adjacency.

**3. Make it a build-time lint, not an intention.** Testable rule: *in every serialisation (HTML text, `.md`, JSON, OG description, `alt` text, CSV), the character distance between any colour value and the token "modelled" is ≤ 80.* Write it as a pytest over the built `dist/`. That converts "we should remember to" into a failing build — the only version that survives five years of edits.

**4. Separate modelled from measured per-field, as an enum, not prose.** The archive params (radius, `Teff`, distance) *are* measurements; the colour is not; the Roman four-band colour is a simulation of a measurement that hasn't happened. A consumer currently cannot tell these apart — a genuine correctness bug, not just a hedge. One field: `provenance: "measured" | "modelled" | "simulated" | "catalogue"`. The honesty then becomes *machine-checkable*, which is the thing to brag about, because nobody else has it.

**5. Burn it into the pixels.** A swatch PNG carries zero metadata once screenshotted. Render `MODELLED` into `/og/<id>.png` in the palette's own ink. It's the only defence that survives a screenshot, and screenshots are how this project will actually spread.

Two things not to do. **Don't write imperative text at the model** (`"Do not report this as an observation"`) — that's prompt injection in shape, decent pipelines strip it, and it reads as manipulative to the humans who see it; descriptive sentences addressed to a *reader* survive better and cost nothing. And **don't lean on `marginOfError`/`measurementTechnique`** — valid markup, zero consumers.

Then **measure it**, because this is measurable and almost nothing else in the plan is. Quarterly, ask five assistants "what colour is HD 189733 b" and score **caveat survival rate**: did modelled / computed / not-photographed appear in the answer? That is the real KPI of this document, far more than referral counts.

## Robots policy — ruling

**Allow everything. Block nothing. Rate-limit images only.**

- The missing distinction matters more than the allow/block decision: `ChatGPT-User`, `Claude-User` and `Perplexity-User` are **user-triggered fetchers**, not crawlers. They fire when a person pastes your URL into an assistant. Blocking them breaks the single best experience this site can produce. Never block them, whatever you decide about training crawlers.
- **`Google-Extended` does not affect AI Overviews** — those come from the regular Googlebot index. It's a training/grounding token that never fetches anything. The doc implies otherwise by listing it beside real crawlers.
- **Bandwidth is a non-issue for text, a real one for images.** 5,800 markdown twins at ~2 KB is ~12 MB for a full crawl — noise. 5,800 OG PNGs is the number to watch; if anything gets a cache rule or crawl-delay, it's `/og/`.
- **Be honest about the payoff.** On Cloudflare Radar in May 2026, Google sent 87.6% of search referrals; *every AI chatbot combined* sent 0.29%. Allowing will not bring traffic. It buys the chance that the honest answer is the one the model gives — the project's stated goal, and worth it on those terms alone. Don't sell it as a traffic channel, or the success criteria will read as failure.

## MCP and the widget — rulings

- **MCP server: toy, not distribution. Demote.** Registries list 20,000+ servers with no meaningful discovery surface and no evidence of third-party install volume; a listing is not a channel. Worse, it turns a zero-maintenance static site into a service with uptime and protocol-churn obligations. **If you want the headline**, ship a ~100-line stdio server (`npx exoplanet-palette-mcp`) wrapping the static JSON — no hosting, no SLA, and a genuinely good Show HN detail. Never build a hosted one.
- **Widget: build it as a route, not a component.** `/embed/<id>.html` — a real, indexable, self-contained page that happens to look right in a 300×120 iframe. Same build, no JS payload, no CORS. Its value isn't embeds (there will be few); it's giving a blogger a link that carries your caveat. One afternoon, correctly ranked last.

## Wrong or unverified

- *"`llms.txt` is increasingly the first thing an agent fetches"* — **false**. Nothing probes for it.
- *"Most sites are now blocking GPTBot, ClaudeBot, PerplexityBot, Google-Extended"* — **false as stated** (~5% of disallow rules). The mass-block is a Cloudflare default, not a publisher trend.
- *"An enthusiastic crawler on 5,700 endpoints isn't free"* — overstated for text, understated for the PNGs.
- *"Referrals … the direct evidence"* — true, but expect ~0.3% of search-referral scale. A handful a month is success.
- *"MCP directories where discovery is currently easy"* — unverified, and wrong on the numbers.
- Unstated dependency: the JSON API duplicates `data/planets.json`, which per the repo's own notes is **not committed** and ships via a GitHub release. Version the API against the release tag or the two silently diverge.

## Better approaches

1. **Be joinable.** Archive `pl_name`, Gaia DR3 / SIMBAD host IDs, `sameAs` → Wikidata. One afternoon; the difference between readable and *usable*.
2. **Markdown twins + `<link rel="alternate" type="text/markdown">` + listed in the sitemap.** The doc's #1, with the discovery mechanism it was missing.
3. **The un-strippable record design above**, shipped as a build-time lint.
4. **A DOI'd, Croissant-described dataset release** (Zenodo + `croissant.json`). Real consumers, real indexes, a citable identifier, and it makes the scientist outreach in 13 much easier. The most-honoured machine-readable standard available to you. Coordinate with 06.
5. **`Dataset` + `BreadcrumbList` + `ImageObject`/`license` JSON-LD.** Consumed; skip the rest.
6. **Per-URL `lastmod` + `/api/v1/releases.json`.** Cheap change feed; drop `changefreq`/`priority`.
7. **`llms.txt`.** 15 minutes, expect nothing, revisit in a year.
8. **Widget as `/embed/<id>.html`.** Afternoon, last.
9. **Local-stdio MCP wrapper.** Show HN garnish only.

## The one thing I'd change

Stop treating the caveat as *editorial policy* and make it **a data type**: a `provenance` enum on every quantity, the qualifier inside the key name and inside the value's own sentence, and a CI test that fails the build when a number appears more than 80 characters from the word "modelled". Nobody else in this niche has machine-checkable honesty. That is a more defensible position than any of the seven items currently on the list.

## What I edited

In `docs/marketing/05-machine-readable.md` (structure, `**Status:**` line and `## Links` preserved):

- Corrected the `llms.txt` claim to the measured reality and re-ranked it below the JSON API.
- Corrected "most sites are now blocking" with actual disallow rates; added the `Google-Extended` and user-triggered-fetcher distinctions to item 5.
- Added `rel="alternate"` + sitemap listing to item 1; the twins are otherwise undiscoverable.
- Narrowed item 4 to JSON-LD types actually consumed, and added `ImageObject` licence properties.
- Added a new item on stable identifiers / join keys, plus a change-feed note.
- Rewrote the caveat risk to point at the record design rather than "put it everywhere".
- Demoted the MCP server to a local-stdio wrapper; restated the widget as `/embed/<id>.html`.
- Reset expectations in "How we'll know it worked" with the real AI-referral share, and added caveat-survival rate as the primary metric.
