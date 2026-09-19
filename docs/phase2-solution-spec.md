# Phase 2 — Solution Specification (v1)

**Product:** Assiette
**One-line:** A student types a need in English or French and gets a ranked, grounded itinerary of affordable Paris meals (CROUS + food distributions) plus the French to use on arrival.
**Stack:** Python, Streamlit, CROUStillant API, curated `distributions.json`, Groq `openai/gpt-oss-20b`.
**Languages (v1):** English and French.
**STAR stage:** this document is the **Action** — the specific design decisions I made in response to the [Situation](phase1-problem-statement.md), before writing a line of code.

> **Read this in 30 seconds:** The app does three things, in order — (1) it *understands* what you're asking for, (2) it *looks up* real, verified places that match, using plain logic (no AI guessing), and (3) only at the very end does an AI model *write up* a friendly summary and French phrases — and it's only allowed to talk about the places step 2 already found and checked. If step 2 finds nothing, step 3's job is to say so honestly, not invent something.

---

## First, three ideas explained without jargon

These three words show up constantly in AI product work. Here's what they actually mean, using this project as the example, before the formal spec below uses them freely.

**"Retrieval"** just means *looking things up in a real source, instead of asking a language model to remember or invent them.* Think of a librarian: you ask a question, and instead of answering from memory, the librarian walks to the shelf and pulls the actual book. In Assiette, "the shelf" is a live government menu feed and a hand-checked list of food charities. The AI model never gets to answer before that lookup happens.

**"Grounding"** means *the AI is only allowed to talk about what was actually retrieved — never anything else.* It's the difference between a tour guide who points at real buildings versus one who's making up landmarks that sound plausible. In Assiette, this isn't just a polite instruction typed into a prompt; it's enforced afterward in the code: if the AI mentions a place that wasn't in the retrieved list, the app deletes that suggestion before showing it to anyone.

**"RAG" (Retrieval-Augmented Generation)** is simply the combination of the two ideas above: *look it up first, then let the AI write about only what was found.* It's the standard pattern for building an AI tool that needs to be both fluent **and** truthful. Assiette is a small, concrete example of RAG done for a real, unglamorous problem instead of a generic chatbot demo.

With those three ideas defined, here is the actual specification.

## 1. Users and jobs-to-be-done

Primary user: an international or budget-constrained student in Paris, typically using a laptop or phone between classes.

Job 1: "Tell me where I can eat tonight near me for under €X."
Job 2: "Is there a free basket I can still catch, and what do I need to bring?"
Job 3: "What is on the CROUS menu, and how do I ask for it in French?"

## 2. Data and inputs

In plain terms: the app has exactly three sources of truth, and it never invents a fourth. If something isn't in one of these three, Assiette is not allowed to know it.

| Source | What it provides | How v1 uses it | Freshness |
|---|---|---|---|
| User query (text) | Area, budget, time, diet, language | Parsed into structured filters | Per request |
| Optional UI filters | Arrondissement, max budget, meal slot, diet | Override / complete the parse | Per request |
| [CROUStillant API](https://api.croustillant.menu) | Paris CROUS restaurants (region code **22**), opening flags, today's menus | Live list + menus for shortlisted sites only | API refreshes ~4×/day; we cache 30 min |
| `data/distributions.json` | ~15 curated distribution / solidarity points (Linkee, Cop1, Restos du Cœur, Secours Populaire, Ordre de Malte, …) | Structured search; **not** live slot inventory | Hand-verified; each row has `last_verified` |
| `data/knowledge.md` | Eligibility rules, typical CROUS prices, French door phrases | Lightweight keyword / overlap retrieval into the LLM context | Static in v1 |

**CROUStillant constraints we respect** — every free API comes with rules, and ignoring them is how student projects get an IP banned or, worse, get someone genuinely bad information:

- Custom `User-Agent` required (e.g. `Assiette/1.0 (essec-dsba-course-project)`) — this is basically the API asking "who is calling me, so I can reach you if something breaks."
- No login needed, but capped at 200 requests per minute per IP address — a rate limit, like a "please don't call more than X times a minute" rule.
- **Non-commercial use only** — this prototype is a course / personal tool, not a productized business on top of their API. (This single sentence turns out to matter a lot — see the business discussion in [Phase 4](phase4-reflection.md).)
- Date format for menus: `DD-MM-YYYY`.

**Typical prices used for ranking (not billed through us — Assiette never handles money)**

- CROUS student social-tariff meal: **€3.30** (bursary tariff **€1.00** when the user says they are a grant-holder, "boursier").
- Food distributions in the dataset: **€0**, with eligibility notes (free is not the same as "no conditions" — most require a student card, and some require pre-registration).

**Explicitly not ingested in v1** (and why each one is a deliberate "not yet," not an oversight): Linkee/Cop1's own booking systems (they sit behind personal logins I can't and shouldn't scrape), Google Forms (same reason), Instagram stories (they disappear and aren't structured data), wearable data (irrelevant to "where's dinner"), audio (adds complexity with no proven benefit for v1).

## 3. Core AI capability

Not "a chatbot with opinions." Three stacked steps, matching the librarian analogy above — understand, look up, then write:

1. **Intent parsing (turning a sentence into a checklist).** An AI model reads the free-text query and turns it into a simple checklist: `{arrondissement, budget_eur, time_hhmm, meal, diet, language, bursary}`. This is the *least* risky use of AI here — worst case, it misreads the sentence, and the on-screen filters let the student correct it by hand. If this step fails entirely, the app still works using simple keyword matching as a backup (no AI required at all).

2. **Retrieval + recommendation (the librarian step — deterministic, not AI).** Combine the real CROUS list with the real distributions list. Filter by Paris / arrondissement / adjacent districts, budget, opening hours vs the requested time, and simple diet keywords in menus. Rank with a transparent, explainable score (closer wins points, cheaper-than-budget wins points, actually-open-now wins points, diet match wins points). Only fetch live menus for the small shortlist that already ranked well — both to respect the 200-requests-per-minute rule and because there's no reason to check the menu of a restaurant that's already closed or too far away.

3. **Grounded generation (the only step that touches an AI language model for the *answer* itself).** The same AI model writes a short itinerary, a dietary note, and 2–4 French phrases. It may **only** mention venues present in the retrieved JSON from step 2 — the code enforces this by checking every place name the model mentions against the list it was actually given, and silently dropping anything that doesn't match. If nothing in step 2 fit the request, the model's job is to say so plainly and suggest relaxing budget, area, or time — not to soften the truth with a vague, hopeful-sounding answer.

**The shape of a single request, start to finish:**

```
query + filters
    → understand: parse intent into a checklist
    → look up: retrieve today's CROUS list (cached) + distributions.json + knowledge snippets
    → sort: filter / rank by proximity, budget, open-now, diet
    → check details: fetch menus only for the top few CROUS candidates
    → write up: AI itinerary, strictly limited to what was actually retrieved
    → show: Streamlit results — ranked cards + map + French phrases
```

## 4. Two key interactions

### Interaction A — Ask once, get tonight's plan

Student types: *"I live in the 13th, €3 budget, dinner after 18:00."*
Assiette returns 2–3 ranked stops (e.g. a still-open CROUS cafeteria if any, otherwise tonight's Linkee/Cop1 site in or next to the 13th), each with price, a plain-language reason it ranked where it did, and walking-scale map pins.

### Interaction B — Open a stop, leave ready to speak

Student expands a card. They see the address, hours, eligibility, today's menu snippet (CROUS) or "bring student card + bag" (distribution), a dietary flag, and copyable French: *"Bonjour, je viens chercher mon panier, voici ma carte étudiante."* This is deliberately the payoff moment: the student doesn't just get information, they get the confidence to actually walk in and ask.

## 5. User experience (v1 screens)

1. **Home / query** — one input, five example chips, optional filters (arrondissement, budget, meal, diet). One box, not a twelve-question form — because a hungry person at 18:10 will not fill out a form.
2. **Results / itinerary** — ranked cards + map; "last updated" shown on every source, so trust is never assumed, only earned by showing the receipt.
3. **Detail** — eligibility, menu, French phrases, source link.

*(See the actual hand-styled mockups: [docs/wireframes/index.html](wireframes/index.html).)*

## 6. What v1 will not build

Saying "not yet" clearly, on paper, is what kept this shippable in days instead of months. None of these are technically impossible — they're deliberately out of scope for a first honest version:

- Real-time remaining slots / booking against Linkee, Cop1, or Google Forms (would require access behind their private logins).
- Voice, live translation, or real-time audio streaming.
- Accounts, profiles, payments, push notifications.
- A native mobile app.
- Coverage outside Paris (Petite couronne only if the user is already next door and a CROUS site is in the snapshot).
- Languages other than English and French.
- Hallucinated venues, invented opening hours, or scraping behind logins — this one isn't a "maybe later," it's a permanent rule.
- Production-grade geo-routing (we rank by arrondissement + straight-line distance, not real metro journey times).

## 7. Success criteria for the course prototype

In plain terms, the prototype "works" if, on a normal weekday demo, all five of these are true:

1. A natural-language query produces a ranked list whose venues **actually exist** in the retrieved data (not invented).
2. At least one result is a **live** CROUS menu **or** a clearly labelled cached fallback — never a silent guess.
3. A distribution result shows real eligibility rules and a real French phrase, not a generic placeholder.
4. Spot-checking the AI's written answer confirms it never mentions a restaurant that wasn't actually retrieved.
5. The demo still works even if Groq (the AI service) is down, or if CROUStillant (the government data feed) is down — using the built-in template and snapshot fallback.

## 8. Biggest risk (carried into the tutor conversation)

**Confident but stale recommendations.** In plain terms: the danger isn't the app being *wrong* in an obvious way — it's the app sounding *right* while quietly being out of date. Charity opening hours change; booking windows close without warning. The mitigation is not "try to always be right" (impossible with fragmented public data) but "never hide how old the information is": every curated row carries a `last_verified` date, the AI is contractually (in code, not just in a prompt) restricted to what was retrieved, timestamps are visible on screen, and the app never claims to know how many food parcels are actually left.

*This exact risk — and how to defend against it — was the first of the three questions taken into the [tutor consultation](phase3-tutor-briefing.md).*
