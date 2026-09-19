# Phase 4 — Prototype reflection

**Product:** Assiette
**Author:** Trishit, ESSEC–CentraleSupélec DSBA M2
**Length:** two pages
**STAR stage:** this document is the **Result** — what happened once the plan from Phases 1–3 met real code, real data, a tutor pressure-test, and a deadline.

> **Read this in 30 seconds:** Building Assiette taught me that the hard part of an “AI feature” is not calling a model. It is deciding, in advance, what the model is allowed to know, then enforcing that in code. Retrieval decides which Paris venues exist. Groq (`openai/gpt-oss-20b`) only writes about those rows. A post-filter drops any stop id that was not retrieved. The consultation with Mr. Weng Wei did not add magic; it made those three rules non-negotiable. This can be a campus tool. It cannot honestly be a startup on today’s CROUStillant feed.

---

## What I learned about AI development that I did not know before

I thought the hard part would be “calling an LLM.” The hard part was **deciding what the model is allowed to know.**

A meal recommendation that sounds fluent and is wrong is worse than saying nothing. A student will actually travel across Paris at 19:40 because a well-written paragraph told them a distribution was open. Building Assiette forced a split I had not internalised from lectures: **the lookup is the product; the generated paragraph is the cover letter.** Ranking is arithmetic — arrondissement, budget, open-for-slot, diet keywords — over two sources of truth: the CROUStillant API (Paris region 22) and a hand-checked `data/distributions.json`. Groq never gets to invent a fourth source. If the API key is missing or the circuit is open, `template_itinerary()` still ranks the same places. That fallback is not polish. It is proof that the important step never depended on the model.

I also learned that “RAG” is a list of ways the system can quietly fail, not a checkbox. Official charity pages disagree: one Linkee page lists Maison Bleue at 19:00–20:00, another still lists 18:30–20:00. If I had concatenated those pages and asked the model to summarise, the contradiction would have become one confident wrong sentence. A structured row with `last_verified: 2026-09-14` is duller and safer. Keyword overlap on `data/knowledge.md` was enough for door phrases; I did not need a vector index for a file that small.

On the government side, a “free, open” API still has rules that matter: a custom User-Agent, 200 requests per minute, missing menus that must stay “unavailable” rather than guessed, and an explicit ban on commercial use. I also learned that model names expire. A tutorial I had bookmarked still named `llama-3.3-70b-versatile`; Groq had already retired it. The prototype uses `openai/gpt-oss-20b` and JSON mode. Hard-coding a dead model is how a live demo dies.

The single most important technical lesson: **“only talk about retrieved venues” has to run after the model answers.** In `assiette/llm.py`, `generate_itinerary()` keeps only stops whose `id` is in `allowed_ids`, then `prose_is_grounded()` scans the summary for title-case names that are not in the retrieved set. Pytest (`test_compose_drops_forged_place_id`, `test_health_and_query_grounding`) is the part I would actually trust in front of a tutor. A prompt is a request. A filter is a guarantee.

The consultation made that lesson operational rather than theoretical. Mr. Weng Wei pushed three things I still remember, without claiming I have his exact wording: grounding has to survive the first time the model is wrong; a timestamp beats eloquence because students under stress will trust fluent prose; and I should run real classmate questions before adding features. Those three points are why the live UI is retrieve-then-compose, why every ticket carries a verified stamp (and “check hours” after 14 days), and why the honest next experiment is twenty messy queries, not another model.

## What I would do differently if I were starting again

I would start even smaller. Version one should have been **one evening, two neighbouring arrondissements, two real distributions, and the nearest lunch-only CROUS site honestly marked closed for dinner.** Covering all twenty arrondissements and a city-wide charity table made the demo look richer and grew the surface of silent staleness at the same time.

I would treat charity rows as a **dated research log**, not a one-time paste: the exact sentence or screenshot, the URL, and the date. `last_verified` without an artifact is decoration.

I would not have called Groq to parse the sentence until `heuristic_intent()` had tests for “the 13th,” “€3,” and “after 18:00.” Pattern-matching is unglamorous and surprisingly reliable. The model is better spent on the job plain code does poorly: natural French at the door. Heuristics already run when Groq is down; I should have frozen that path before FastAPI, auth screens, and a visual restyle.

I would treat **“there is no subsidised hot meal open now”** as a first-class result. Many CROUS restaurants only serve weekday lunch (currently a €1 complete meal for all students, 11:30–14:30, per CROUS Paris, 3 September 2026). On a Tuesday at 18:20, the useful sentence is often: nothing like that is open near you — here is a distribution that actually runs tonight. That belongs above the fold, not in a caveat.

After the tutor conversation I would also have built one evaluation habit before v2: collect about twenty questions from classmates and, for each answer, ask only “would I have walked there?” I ran the seeded query *“I live in the 13th, €3 budget, dinner after 18:00”* end to end — retrieve returned real 13e tickets (Le rooftop de la barge, Cafétéria inalco, Cop1 Austerlitz), compose stayed inside those ids, Refresh re-hit CROUStillant. That is one question, not twenty. The gap is still the one he named.

## Could this become a business — and why or why not

**Not on this foundation, and not as a wrapper around CROUStillant.**

The need is real. Student food insecurity in Paris is not a course anecdote, and “what is open, what it costs, and am I eligible” is still scattered across Crous Mobile, Linkee, Cop1, Secours Populaire, and Maison étudiante. A polished, honest layer could help students, a CROUS communications team, or a student union.

The wall is legal and operational. CROUStillant’s terms forbid commercial use. Building a company on that feed would break the licence and couple the product to one source that can disappear. The feature people might pay for — remaining parcels tonight — lives behind those organisations’ booking accounts. Scraping it would be fragile and, more importantly, the wrong relationship with people who are already in difficulty. Without live inventory, Assiette is a better directory, and directories are hard to charge for.

The realistic path is **deliberately non-commercial**: a campus or civic tool, grant-funded or run by a student-life office, kept current the way a timetable is, trusted because it refuses to guess. If it ever grew, institutions would publish structured hours and Assiette would be the front door, not a scraper. Calling this a venture today would be the same failure the architecture was designed to avoid — sounding confident about something that is not true.

## The one sentence I am keeping

**People first, real lookups second, the language model last — and a visible date-stamp on every claim.** That is what Phase 4 actually produced, more than any particular line of code.
