# Reviews — the adversarial pass, and the persona roster

Each channel doc in `docs/marketing/` was re-evaluated by a reviewer with a deliberately chosen
persona. The reviews live here, one file per doc. **The plans themselves were edited in place**
where a reviewer found a verified factual error or an unambiguous improvement — so the docs are
the current best version, and these files are where the argument and the rejected options live.

Read a review when you're about to *act* on its doc. Don't read them all at once.

---

## The casting rule

The reviewer for each doc is **the person most likely to reject that plan in real life** — not a
generic marketing critic and not a supportive one. A moderator who removes self-promo every day
will find the ban risk in a Reddit plan that no marketer would see. A press officer knows which
missing image spec costs you the story. The point of a persona is not flavour; it's that domain
gatekeepers have failure modes memorised that a generalist has to guess at.

Three properties make a persona work here:

1. **They hold the gate.** They can say no to this exact plan, professionally, and have.
2. **They have seen it fail before.** The value is in the specific failure modes they've watched,
   not in their taste.
3. **They are not hostile to the project.** A pure cynic produces unusable critique. The brief is
   *"you want this to succeed, so attack it now instead of letting reality do it later."*

Where a doc has two distinct audiences with different failure modes, cast two people in one
reviewer (the educators doc is reviewed by a classroom teacher *and* a planetarium officer, and
the review says which one is speaking).

---

## The roster

| Doc | Reviewer persona | Why this one holds the gate |
|---|---|---|
| [01 Newsjacking](../01-newsjacking.md) | **Wire-service breaking-news editor**, 20 years | Decides in a minute what travels, and has killed copy that was fast but wrong — the exact failure mode of a one-hour turnaround |
| [02 Press kit](../02-press-kit.md) | **Science press officer** at an observatory/agency | Has watched their own paragraphs get rewritten and their images cropped; knows which missing spec loses the story |
| [03 SEO](../03-seo-planet-pages.md) | **Technical SEO for large programmatic sites** | Has personally watched a site lose its traffic to a thin-content update — the live risk in 5,700 generated pages |
| [04 Wikimedia](../04-wikimedia.md) | **Wikipedia admin / Commons contributor**, WikiProject Astronomy | Enforces OR and COI policy, and knows where the plan misreads what the policy actually says |
| [05 Machine-readable](../05-machine-readable.md) | **Retrieval / AI-search engineer** — builds the consuming side | Only someone who has written the ingestion code knows which conventions are honoured and which are folklore |
| [06 Open data](../06-open-data.md) | **Research data librarian** (FAIR / RDM) | Derived-data licensing and citability are exactly where enthusiastic deposits go wrong |
| [07 Wallpapers](../07-wallpapers.md) | **Product designer + wallpaper-community power user** | One judges whether anyone keeps it; the other knows why the post gets removed |
| [08 Short video](../08-short-video.md) | **Faceless short-form science creator** who actually ships weekly | Real production economics, not estimated ones — the doc's whole verdict rests on an hours number |
| [09 Show HN](../09-show-hn.md) | **Fifteen-year HN reader with front-paged Show HNs** | The harsh commenter is the actual adversary; better to meet them before the thread |
| [10 Reddit](../10-reddit.md) | **Moderator of a large science subreddit** | Spots a campaign in the first sentence, and knows which rule quote is wrong before it costs a ban |
| [11 Bluesky/Mastodon](../11-bluesky-mastodon.md) | **Working planetary scientist who is an active sci-comm poster** | Sets the community norms this plan has to satisfy; can say what would make them mute or repost |
| [12 Newsletters](../12-design-newsletters.md) | **Curator receiving ~50 pitches a week** | The recipient is the only honest judge of a pitch email |
| [13 Credits](../13-credit-the-scientists.md) | **Research-software citation & ethics specialist** | An audit that *looks* complete is the worst outcome, because it will be acted on |
| [14 Educators](../14-educators.md) | **Secondary physics teacher + planetarium education officer** | Classroom reality kills resources built by enthusiasts; the two lenses fail differently |
| [15 Roman](../15-roman-launch.md) | **Exoplanet astronomer who has read the CGI documentation** | The one doc where being wrong is most damaging, and the only reviewer who can check the instrument claims |
| [99 Tracking](../99-tracking.md) | **Analytics engineer hostile to vanity metrics** | More damage is done by measuring the wrong thing precisely than by not measuring |
| [Hub](../README.md) | **Reviewed last, by the synthesiser** | A portfolio review is only meaningful once the individual verdicts are in — sequencing depends on what survived |

---

## The brief that goes with a persona

A persona alone produces atmosphere. What produces findings is the persona *plus* a fixed brief.
Every reviewer above got the same seven instructions — reuse them if you re-run this:

1. **Read the doc, the hub, and the two or three siblings it links to** — so the critique fits the
   plan instead of fighting it.
2. **Independently verify the doc's factual claims** with search, and *re-derive* anything the doc
   claims to have audited rather than trusting its table. Confidently-stated wrong facts are the
   thing a second pass exists to catch.
3. **Name one section as "the section this review exists for"** — the single hard problem only this
   persona can solve. This is what turns a critique into new work; without it reviewers default to
   listing what's missing.
4. **Attack the verdict, not just the details.** Reviewers are explicitly permitted to overturn the
   doc's conclusion, and asked to argue the strongest opposing case *before* ruling.
5. **Edit the doc directly** for verified corrections and unambiguous improvements; put opinion,
   rejected options and reasoning in the review. Structure, status line and links are preserved.
6. **Say "keep as is" when it's true**, in one line, and move on. Padding costs the author an evening.
7. **Cap the length.** 140–200 lines. A review nobody finishes changes nothing.

Two constraints that matter as much as the persona: give each reviewer **exactly one doc to edit**,
so parallel reviewers never collide on a file; and require a **one-line verdict** from a fixed
vocabulary (`keep as is` / `revise` / `substantially rework` / `replace`) so the results can be
read as a board rather than sixteen essays.

---

## Reading the results

Start with the verdicts. Anything marked `substantially rework` or `replace` is a plan that would
have wasted an evening. Then read the "one thing I'd change" line from each — collectively that's
the shortest useful version of this whole directory.
