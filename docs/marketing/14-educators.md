# Educators, planetariums & outreach

**Status:** not started · **Effort:** high (2–3 weekends up front, then a slow drip) · **Payoff:** high, compounding · **Hub:** [Marketing plan](./README.md)

## The bet

Teachers are the only audience that shares relentlessly inside networks we cannot otherwise reach, and that keeps using a resource for years rather than one afternoon — a worksheet adopted in September comes back every September. Exoplanet Palette has an unusually strong hook for them that has nothing to do with pretty colours: the site is a live, honest demonstration of the difference between a **model** and an **observation**, which is the single hardest thing to find good classroom material for. The five solar-system anchors built from measured spectra and real photographs make that check verifiable by a fifteen-year-old with their own eyes. The cost is that teachers need artefacts we do not have yet — a printable, a time box, a "what this is for" note — and none of those write themselves.

## What teachers actually need

Research consistently says the same handful of things, and almost none of them are "more content". From the RAND *American Instructional Resources Survey* (Spring 2025) and the 2025 ACM CHIIR study of teacher resource search, the selection criteria that actually decide adoption are: curriculum alignment, age-appropriateness, and whether it looks engaging — and when a resource database returns too many or too few results, teachers abandon it and go back to Google or YouTube. Design for the Google path, not for a database.

Concretely, a resource gets used when it has:

- **A stated time box.** "45 minutes, one period" or "10 minutes, starter". A resource with no duration is a resource a teacher cannot plan around.
- **Curriculum alignment stated in their vocabulary**, on the artefact itself, not buried on a website.
- **No login, no account, no app.** This we already win: static site, free, no login, works on a locked-down school laptop. Say so explicitly — it is a selling point, not a given.
- **A printable fallback.** School wifi fails, tablets are booked, the IT filter blocks something. A PDF that works with zero internet is the difference between "used" and "abandoned mid-lesson".
- **A teacher-facing "what this is for" note** — the misconceptions it targets, what to say when a student asks the obvious awkward question, and an answer key. This is the artefact teachers actually search for and the one hobby projects never make.
- **A licence they can act on without asking.** Ambiguity means they will not photocopy it for 30 students.

**US / NGSS.** Verified against the DCI arrangements (`nextgenscience.org`, *AllDCI.pdf*). Ranked by how honest the claim is:

- **MS-PS4-2** — "Develop and use a model to describe that waves are reflected, absorbed, or transmitted through various materials." *This is the only exact match on the list*, and it is exact: reflected/absorbed is literally the albedo spectrum, and "develop and use a **model**" is the practice the site embodies. Lead every US-facing artefact with this one, even though it is middle school — the same activity runs at high school as enrichment.
- **HS-PS4-3** — "Evaluate the claims, evidence, and reasoning behind the idea that electromagnetic radiation can be described either by a wave model or a particle model…" Adjacent, not aligned: it is about *two competing models of light*, not about checking a model against an observation. Cite as "supports", not "meets".
- **HS-PS4-1** — frequency/wavelength/speed. **Weak.** The PE requires *mathematical representations*; the site never asks a student to compute anything. Drop it unless the worksheet adds a v = fλ step, which it should not.
- **HS-ESS1-2** — ~~"astronomical evidence of light spectra"~~. **Do not cite this.** The full wording is "Construct an explanation of **the Big Bang theory** based on astronomical evidence of light spectra, motion of distant galaxies, and composition of matter in the universe", and the clarification statement is redshift and the CMB. Quoting it with the Big Bang elided is the exact kind of alignment-stretch that a curriculum lead spots in ten seconds and never trusts you again after.
- The real prize is the **Science and Engineering Practices**, not the content PEs: **SEP-2 Developing and Using Models** and **SEP-7 Engaging in Argument from Evidence**, plus the crosscutting concept **Systems and System Models**. NGSS-aligned material for *content* is abundant; material that lets a student interrogate a model against an observation is scarce. That is precisely what the solar-system anchors are. Lead with this.

**UK.** AQA A-level Physics 7408 has an **Astrophysics** option covering spectral classes (OBAFGKM), Wien's displacement law, Stefan–Boltzmann, and black-body radiation — the host-star "lamp" feature maps onto this almost exactly. The spec also covers **exoplanet detection, but explicitly limited to radial velocity and transit**. Be honest in the material: reflected-light colour is *not* on the spec. Position it as enrichment and as context for why the transit method leaves colour unanswered — do not claim spec coverage we do not have.

**Portugal / EU (maintainer's home advantage).** Now verified directly against the DGE *Aprendizagens Essenciais* PDFs (`dge.mec.pt/.../10_fq_a.pdf`, `11_fq_a.pdf`, Agosto 2018). Two corrections and one much better hook:

- **"Das Estrelas ao Átomo" is not an AE heading.** It is a unit title from the older *Programa*; teachers still say it, but do not print it as an alignment. The 10.º-ano AE domains are **Elementos químicos e sua organização**, **Propriedades e transformações da matéria** and **Energia e sua conservação**. The relevant subdomain is **Energia dos eletrões nos átomos**.
- **The verbatim 10.º-ano outcomes to quote** (Química, *Energia dos eletrões nos átomos*): "Interpretar os espectros de emissão do átomo de hidrogénio…", "Comparar os espectros de absorção e emissão de vários elementos químicos, concluindo que são característicos de cada elemento", and best of all "Explicar, a partir de informação selecionada, algumas aplicações da espectroscopia atómica (por exemplo, **identificação de elementos químicos nas estrelas**…)". Stars are named in the curriculum text itself.
- **Do not claim black-body radiation at 10.º ano.** The Física subdomain *Energia, fenómenos térmicos e radiação* goes only as far as "todos os corpos emitem radiação e que à temperatura ambiente emitem predominantemente no infravermelho" — no Wien, no Stefan–Boltzmann. The host-star "lamp" is enrichment here, not coverage.
- **The 11.º-ano line is the real prize.** Domain **Ondas e eletromagnetismo**, subdomain *Eletromagnetismo e ondas eletromagnéticas*: "Fundamentar a utilização das ondas eletromagnéticas nas comunicações e **no conhecimento do Universo, integrando aspetos que evidenciem o carácter provisório do conhecimento científico** e reconhecendo problemas em aberto." A curriculum that explicitly asks for *the provisional character of scientific knowledge*, evidenced through EM waves used to know the Universe, is describing this project. Put that sentence at the top of the Portuguese worksheet, verbatim, and the alignment argument is over.

The institutional opening is just as strong: **ESERO Portugal** is run by **Ciência Viva** in partnership with ESA, out of the **Pavilhão do Conhecimento in Lisbon** (esero.pt), it publishes a "Recursos de Professores" library, it runs an accredited *Centro de Formação* (recognised by the Ministério da Educação since 2007), and it hosts the annual **Conferência de Professores EspAciais** each October. There is **no public "submit a resource" form** — the route is a person, a conversation, and ideally a slot at that conference. A Lisbon-based maintainer can walk in. That is an advantage almost nobody else pitching a hobby site has, and it is worth more than any of the online listing sites below.

## What to build

Ranked by effort-to-payoff. Do 1–3 before touching any distribution channel; an empty `/teach` page makes every outreach email worse than not sending it.

1. **A `/teach` page on the site.** *~1 evening.* One page. What the site is, what is modelled vs measured, the time box for each activity, the licence, a download list, and a short "how to use the honesty as a lesson" section. Every channel below links here; it is the hub that makes the rest submittable. Highest leverage by a distance.
2. **"Why is this one blue?" — one-page worksheet.** *~1 weekend.* A4 **and** US Letter, 1 page student-facing + 1 page teacher notes/answer key. Structure: pick three planets from a named list, read the spectrum plot, predict the colour, check it, explain which molecule ate which wavelength. 45 minutes, one period. State NGSS PEs and the time box in the footer.
3. **Solar-system anchor activity — "does the model agree with the photograph?"** *~1 weekend.* The signature piece and the one worth doing properly. The five anchors are **Earth, Jupiter, Saturn, Uranus, Neptune** — not Mars; Mars has no measured spectrum in the dataset. Students compare each computed colour against the real photograph, find where it agrees and where it does not, and write down *why a disagreement is information rather than failure*. The Neptune card is the whole lesson in one object: the famous Voyager 2 blue is **contrast-enhanced**, and the computed colour is the one that matches modern reanalysis — so here the *photograph* is the thing that misleads. This is SEP-2 and SEP-7 in one page, and it is the activity astroEDU is most likely to accept. 50 minutes. See the review in [reviews/14-educators-review.md](./reviews/14-educators-review.md) for the fully worked lesson.
4. **No-internet PDF fallback.** *~1 weekend, mostly build scripting.* A ~20-planet subset as a printable pack: swatch, spectrum plot, the plain-English "why". Lets the worksheet run with the wifi down. Reuse the existing static build; do not hand-make it.
5. **Printable wall poster / gallery chart.** *~2 evenings if it reuses [07-wallpapers](./07-wallpapers.md) render code.* A0 and A3, plus a "print at home" A4 tiling. Posters have a long half-life on a lab wall and are pure passive advertising, but they teach nothing on their own — hence rank 5, not 1. Put the URL and a QR code on it.
6. **A 10-minute guided tour framed as a lesson starter.** *~1 evening — and mostly already done.* The shipped tour **`start-here` — "Start here: five worlds we can check"** *is* the anchor tour; it needs a teacher note and a time box, not a build. "The darkest worlds" and "Two ways to be blue" are the other two with lesson shape. Lowest effort of all, but it only pays off once someone is already on the site.
7. **Translate 2 and 3 into Portuguese.** *~1 evening each.* Unlocks ESERO Portugal properly and costs almost nothing given the maintainer's Portuguese. Do this before the Ciência Viva conversation, not after.

Deliberately **not** building: a lesson-plan sequence, a slide deck, a teacher training workshop, anything with student accounts or progress tracking. All are high-effort, and none survive a solo maintainer's evenings.

## Where to put it

| Channel | How to submit | Free? | Verdict |
|---|---|---|---|
| **astroEDU** (IAU Office of Astronomy for Education) | Four steps, confirmed on `astroedu.iau.org/en/submission/`: email `astroedu@astro4edu.org` to propose, complete their **Google submission form**, download the activity template, return the filled template by email. Two referees — one research scientist, one educator. Published **CC BY 4.0**. No published review timeline. | Yes | **Do this first.** Peer review gives credibility nothing else on this list gives, and the CC BY requirement matches our licence anyway. Slow (months) — submit activity 3 and forget about it. |
| **ESERO Portugal / Ciência Viva** | esero.pt, based at Pavilhão do Conhecimento, Lisbon. Contact the office directly; they run teacher training and a teacher-resource library. | Yes | **Highest-value single move.** Local, in-person, ESA-branded, reaches Portuguese teachers with national legitimacy. Needs the Portuguese translation first. |
| **ASP — *Universe in the Classroom*** | **Defunct.** Founded 1984; **ceased publication in 2018**. The back issues now live as a PDF archive (hosted by ASP, mirrored by the AAS). There is no editor to pitch and no issue to be in. | n/a | **Skip — this was wrong in the last draft.** The ASP itself is still worth an email (it co-runs the Night Sky Network below and its education staff are real), but not via this newsletter. |
| **OER Commons** | Free account, build the listing in their "Open Author" tool. 42,000+ indexed resources, CC-licensed. | Yes | **Do it.** Low effort, permanent, good for search. Do not expect traffic on its own — it is a credibility artefact you can cite. |
| **TES** | Free author account, upload as a free resource. Large UK/international teacher base. | Yes | **Do it.** Best single route to UK secondary teachers. Free upload; you choose free vs paid — choose free. |
| **NASA Night Sky Network** | 370+ US amateur clubs; membership is club-based, individuals cannot join. Route in is the monthly **"Night Sky Notes"** segment distributed to clubs — pitch via nightsky.jpl.nasa.gov. | Yes | **Worth one email.** Reaches clubs, not classrooms. Cheap to try, low odds. |
| **AAS — Resources for Educators** | `aas.org/education/resources-educators` is a curated links page, not a submission system. Email the Education Committee. | Yes | **One email, no follow-up.** Being listed is nice; it is not a traffic source. |
| **NASA's Universe of Learning** | STScI / Caltech-IPAC / Sonoma State / JPL consortium. **No public third-party submission route found** — resources are made by the funded team and its network. | n/a | **Not submittable.** Do not spend evenings here. Reachable only via a person inside the network — treat as a bonus if someone finds you. |
| **NASA/JPL Edu** | `jpl.nasa.gov/edu` publishes NASA-authored standards-aligned lessons. No external submission route. | n/a | **Skip.** Same as above. |
| **Teachers Pay Teachers** | Seller account required; **Basic is a one-time US$29 fee**, and your first upload must be free. | **No** | **Skip.** Paying to give something away, on a platform whose culture is commercial, for an audience we reach free via TES and OER Commons. |
| **Subject-teacher Facebook groups** (e.g. "Physics Teachers", NSTA-adjacent groups) and **r/ScienceTeachers**, **r/Physics**, **r/astronomy** | Post as a person, with the worksheet, not a link drop. Read each group's self-promo rule first. | Yes | **Good, but rationed.** One post per community, spaced out, always leading with the free PDF. See [10-reddit](./10-reddit.md) for tone. |
| **Wakelet / Padlet teacher shares** | No submission process — these are collections other people curate. | Yes | **Not a channel.** Being included is a downstream effect of the above; do not chase it. |
| **IAU OAE national outreach coordinators** | astro4edu.org lists national contacts, including for Portugal. | Yes | **Cheap add-on.** Email the Portuguese coordinator at the same time as ESERO. |

## Talks

**Astronomy on Tap** runs in dozens of cities worldwide (10+ years old as of 2026), always needs speakers, and is aimed at a pub audience. Verified on `astronomyontap.org`: there is **no formal speaker-application process**, the only central address is `astronomyontap@gmail.com`, the site's own line is that "presenters are typically from local research and educational institutions", and the current site makes **no mention of virtual or remote events** — the 2020-era streaming chapters were a pandemic arrangement, not a standing offer. Two consequences: (a) route in via individual chapter organisers, named on the chapter page or its Eventbrite listing; (b) **do not lead with "I can do it remotely"** — a Zoom face on a pub wall is a worse night than no talk, and offering it first reads as someone who has never been in the room. Offer in person for Lisbon and Porto, and treat everything else as a bonus. Email five chapters, expect one or two yeses.

This is also a warm route to actual astronomers, which matters more than the audience size: the people in the room are the ones who might cite, correct, or amplify the project. Pair it with [13-credit-the-scientists](./13-credit-the-scientists.md).

**10-minute talk structure** (AoT slots are short and the audience has beer):

1. **0:00** — One slide, no words: a wall of ~5,700 coloured swatches. "Every one of these is a real planet, and none of these are photographs."
2. **1:00** — Why a planet has a colour at all: albedo spectrum × starlight. One equation, spoken not written.
3. **3:00** — The honest bit, early: these are computed. Show the solar-system anchors next to the real photographs. Where it agrees, where it does not, and why the disagreement is the interesting part.
4. **5:30** — The physics that makes colours: methane eats red, clouds whiten, sodium eats yellow, HD 189733b comes out cobalt.
5. **7:00** — The Roman hook: true colour vs "as Roman would see it" through four bands. How much identity survives a filter set. This is the memorable slide — land it.
6. **9:00** — Microlensing planets: swatches for worlds from which no light is ever received. Say plainly that these are model-only. It gets a laugh and it makes the honesty point better than any slide about honesty.
7. **9:30** — URL, licence, "the data is open", done.

Also viable, same deck: local astronomy club monthly meetings (they book speakers months ahead and are desperate for new topics), university public-lecture series, and Ciência Viva / Pavilhão do Conhecimento events in Lisbon.

## Planetariums & museums

Honest assessment: **a full fulldome show is out of reach and should not be attempted.** Fulldome production is a specialist pipeline, and the free shows in circulation (ESO's *From Earth to the Universe*, NOIRLab's *Big Astronomy*) are institution-funded productions, not weekend projects.

What *is* reachable, in order:

1. **Lobby / foyer screen loop.** A silent, looping, high-resolution video or a self-running full-screen web page of the gallery, with captions. This is genuinely realistic: museums have idle screens and no content for them. Ship it as a plain MP4 plus a kiosk-mode URL, and it costs one weekend of render scripting.
2. **A live presenter's aside.** Planetarium operators improvise around a star field constantly. Give them a single slide plus two sentences of script and a URL; a presenter who likes it will use it for years.
3. **Fulldome assets, not a show.** If it ever becomes tempting, produce a *clip* — 60–90 seconds of the gallery, rendered to the standard fulldome master format — and list it on **fddb.org** (Fulldome Database) and the **International Planetarium Society** free-materials page. Clips get used inside other people's live shows. Rank this after everything in "What to build".

Minimum viable approach: email three local science centres (start with Pavilhão do Conhecimento, which is also the ESERO office — one relationship, two doors) offering the lobby loop for free under CC BY. Do not build the loop until one of them says yes.

## Draft copy

**A. To a teacher-network coordinator (ESERO / ASP / OAE national coordinator).** Subject: `Free classroom resource: the colour of every known exoplanet, computed from physics`

> Hello [name],
>
> I maintain Exoplanet Palette (<SITE_URL>) — a free, static site that computes the visible colour of every known exoplanet (~5,700) from physics: a modelled albedo spectrum times the host star's spectrum, through CIE colour matching to a hex code. No login, no tracking, no app, works on a school laptop.
>
> I have made two one-page classroom activities from it, CC BY 4.0, A4 and Letter, with teacher notes and an answer key:
>
> - *Why is this one blue?* (45 min) — students read a spectrum, predict a colour, and work out which molecule absorbed which wavelength.
> - *Does the model agree with the photograph?* (50 min) — the site includes five solar-system planets built from **measured** spectra, so students can check the computed colour against a real photograph of Jupiter or Neptune and argue about where it disagrees and why.
>
> The second one is the reason I am writing. The site is deliberately, repeatedly honest that these colours are computed and not photographed — including flagging microlensing planets, from which no light is ever received, as model-only. That makes it a working demonstration of the difference between a model and an observation, which I understand is one of the harder practices to find material for.
>
> Everything is free and openly licensed, and I am happy to adapt the format, translate it, or record a short walkthrough if that would help it fit your library.
>
> Would this be a fit for [programme name]?
>
> Best,
> [name] · [city]

**B. To an Astronomy on Tap chapter organiser.** Subject: `Talk offer (remote): "Every exoplanet is a colour you have never seen"`

> Hi [name],
>
> I would love to give a 10-minute talk at Astronomy on Tap [city]. I am Lisbon-based and can be there in person. [For distant chapters only, and only if they raise it: I can also do it over video if that ever suits a night you are short.]
>
> **Every exoplanet is a colour you have never seen — and never will.** I built a site that computes the visible colour of all ~5,700 known exoplanets from their albedo spectra and their host stars' light. The talk is about what colour actually *is* when nobody has ever seen the object: why methane makes a planet blue-green, why HD 189733b comes out cobalt, and what happens to a planet's colour identity when you can only see it through the Roman Coronagraph's four filters.
>
> There is a punchline that works well in a bar: the site also produces swatches for microlensing planets, from which no light is ever received by anyone, ever. I show them, and then explain why I still think they belong there.
>
> Lots of colour on screen, one equation, no jargon that is not explained. Site is <SITE_URL> if you want to see whether it fits your night.
>
> Cheers,
> [name]

## Licence

**CC BY 4.0** for all classroom artefacts — worksheets, teacher notes, poster, PDF pack. Reasons, in order of weight:

- **astroEDU publishes under CC BY 4.0**, so anything more restrictive is not submittable there at all.
- **NC and ND kill school reuse.** `NC` creates genuine doubt for a fee-paying school or a paid teacher-training course; `ND` blocks translation and blocks a teacher cropping a page — both of which we actively want.
- CC BY keeps attribution, which is the only thing that makes this channel pay back in links.

Put the licence and the URL **in the footer of every printable**, not only on the site — the artefact travels without the site. Keep the data licence decision separate and consistent with [06-open-data](./06-open-data.md).

## Timing

- **Now → end of August.** Build `/teach`, the two worksheets, and the Portuguese translations. Northern-hemisphere term starts late August/September and teachers plan in the two weeks before; anything landing after mid-September waits a full year for that first-impression slot.
- **Late August.** Submit to TES and OER Commons, email ESERO Portugal and the OAE Portuguese coordinator. One wave. (ESERO's *Conferência de Professores EspAciais* runs in October — an August email is the right lead time to ask about a slot or a resource-library listing.)
- **September and again in January.** The two moments teachers look for new material. Post to subject groups/subreddits in September; hold the second post for January.
- **Anytime, decoupled.** astroEDU (months-long review — start it early and forget it) and Astronomy on Tap (rolling).
- **Around the Roman launch** — see [15-roman-launch](./15-roman-launch.md). Teacher interest in Roman will spike, and the four-band feature is the only place on the internet showing what that instrument does to colour. Have the worksheet already listed by then, not written then.

## How we'll know it worked

Primary metric: **repeat-term usage**, not raw traffic. A resource that is genuinely adopted shows a visible traffic bump in *both* September and January. One spike is a share; two spikes is adoption. Judge this channel at the 12-month mark, not the 12-week mark.

Supporting metrics:

- Distinct school/university referrers and distinct countries hitting `/teach`.
- Worksheet PDF downloads, split by source.
- Any inbound "can I use this with my class / can I translate it" email — a leading indicator worth more than a thousand pageviews.

UTM tagging, per [99-tracking](./99-tracking.md):

- `?utm_source=educators&utm_medium=worksheet&utm_campaign=teach` on QR codes and PDF footers
- `&utm_content=<channel>` for the channel — `astroedu`, `esero`, `tes`, `oer`, `asp`, `aot-<city>`
- Poster QR gets its own `utm_medium=poster` so wall-chart pickup is separable.

Note that cookieless analytics will undercount here, and school networks strip referrers aggressively — so treat all numbers as a floor and weight the qualitative signal (emails, translation requests) higher than usual.

## Risks

- **Building six artefacts nobody asked for.** The realistic failure mode. Mitigation: build `/teach` + one worksheet, send five emails, and only build the rest if anything comes back.
- **Bureaucratic sinks.** astroEDU review runs months; NASA-side channels have no submission door at all. Send and forget; never let these block a weekend.
- **Curriculum-alignment overclaim.** Reflected-light colour is not on the AQA spec (confirmed: detection is limited to Doppler/radial-velocity and transit), HS-ESS1-2 is a **Big Bang** PE and not ours, and 10.º-ano FQ-A does not cover black-body laws. The Portuguese *Aprendizagens Essenciais* wording is now verified — quote it verbatim and nothing else. Claiming alignment we do not have destroys credibility with exactly the audience that checks. State alignment conservatively; say "enrichment" where it is enrichment.
- **The honesty pitch backfiring.** A small number of teachers will read "these are not photographs" as "then this is not real science". Pre-empt it in the teacher note: modelling *is* the science, and the anchors are how you check it.
- **Maintenance debt.** A PDF with a dead URL or stale planet count is worse than no PDF. Regenerate printables from the build, and avoid printing counts that change.
- **Solo-maintainer bus factor.** Teachers commit to a resource for years. If the site might disappear, the offline PDF pack and an open licence are the honest mitigation — they keep working when we do not.

## Links

- [Marketing plan](./README.md) — hub
- [02-press-kit](./02-press-kit.md) — the assets and boilerplate these emails reuse
- [03-seo-planet-pages](./03-seo-planet-pages.md) — teachers arrive via Google; `/teach` needs to be findable
- [05-machine-readable](./05-machine-readable.md) — students and student projects consuming the data directly
- [06-open-data](./06-open-data.md) — licence must be consistent with the classroom-artefact licence
- [07-wallpapers](./07-wallpapers.md) — shares render code with the printable poster
- [08-short-video](./08-short-video.md) — the talk deck and a short video are the same material twice
- [10-reddit](./10-reddit.md) — tone and self-promo rules for r/ScienceTeachers and friends
- [13-credit-the-scientists](./13-credit-the-scientists.md) — Astronomy on Tap is the warm route to the same people
- [15-roman-launch](./15-roman-launch.md) — the moment teacher demand for Roman material spikes
- [99-tracking](./99-tracking.md) — UTM conventions and the cookieless-undercount caveat
