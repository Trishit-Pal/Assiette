# Phase 3 — consultation notes

**Purpose, in plain terms:** this is the honest debrief, written right after the call, while the specific things Mr. Weng Wei said are still fresh. Don't polish it. Rough, specific notes are far more useful for the Phase 4 reflection than a tidy summary written two days later from memory.

Date / time of call: booked by 7 September 2026 (Calendly with Mr. Weng Wei). Exact clock time not recorded here.
Google Doc link: one-pager from `docs/phase3-one-pager.md` (pasted to Google Docs for the invite).
Calendly confirmation: slot booked at https://calendly.com/wuvist/30min

**Honesty:** these notes were filled after the call from what I still remember, not from a same-day transcript. I am not inventing verbatim quotes. I remember three pressure-tests, not the exact wording.

## What he challenged (be specific — quote him if you can)

- **Grounding.** A fluent, confident sentence that names a place which is not actually in the data is worse than a blank screen. A student will travel at 19:40 because the paragraph sounded sure. The prompt is not the defence. The defence is: retrieval first, then generation, then a hard check that every stop id was retrieved.
- **Stale data.** A timestamp on the ticket matters more than pretty copy. If charity hours moved last week and Assiette still speaks in the present tense, the app is the failure, not the student who trusted it. He pushed me not to hide age-of-data in small print.
- **Eval.** Do not add v2 features until I have run real student questions through the prototype and asked, for each one, “would I actually walk there based on this answer?” Twenty messy classmate sentences beat a fancy scoring rubric.

## What he would cut from v1

- Live parcel counts / scraping charity logins. Incomplete on purpose.
- A chatbot thread. One query → tickets, not a conversation that can invent a fourth venue.
- City-wide “complete coverage” as a quality claim. Coverage without a verification habit is just more stale rows.

## What he would build first this weekend

- The lookup: CROUStillant list + curated `distributions.json`, filter, rank, show stamps.
- Tests that a forged place id cannot appear.
- Only then Groq copy (summary + French at the door), with a template fallback if the key is missing.

## The one thing that surprised me most

I expected him to push me toward a more impressive model or an agent loop. He pushed the opposite: **evaluation and freshness**, not more AI. The surprising implication was that Assiette is an information product that happens to use a language model, not an LLM product that happens to list restaurants.

## Quotes worth keeping for the reflection

Not verbatim. Themes I am willing to stand behind:

- Grounding has to survive the first time the model is wrong.
- Students will trust fluent prose over a date-stamp unless the stamp is unavoidable.
- Test with questions a hungry classmate would actually type before writing more code.
