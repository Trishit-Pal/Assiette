# Phase 3 — Tutor consultation briefing

**Deadline:** book a 30-minute slot with Mr. Weng Wei **by 7 September**.
**Booking link:** https://calendly.com/wuvist/30min
**STAR stage:** this consultation sits between **Action** (the plan I designed in Phase 2) and **Result** (what I'll actually build in Phase 4). It exists to catch mistakes on paper, which is always cheaper than catching them in code.

This file cannot book the slot for you (Calendly requires your Google/email). It is the exact kit to take into the call — written so you could hand it to someone else and they'd know exactly what to say and why.

---

## Why this call exists, in plain terms

Right now, the plan for Assiette only exists on paper. Mr. Weng Wei has 20+ years of building real AI products — he has seen ideas like this succeed and fail before, for reasons that aren't obvious from the outside. The point of this 30 minutes is **not** to get his approval, and **not** to ask him what to build. It's to get him to find the one or two things I can't see yet, because I designed this plan myself and I'm too close to it.

That means the call only works if I show up with **specific decisions already made** and **specific uncertainty already named** — not with "what do you think I should build?" A vague question gets a vague, generic answer. A specific question ("is X my biggest risk, or is Y?") gets a specific, useful one.

## Before you click Calendly (10 minutes)

1. Open [docs/phase3-one-pager.md](phase3-one-pager.md) (or print [phase3-one-pager.html](phase3-one-pager.html) to a tight one-page PDF).
2. Create a Google Doc titled `Assiette — Track 3 brief — Trishit — ESSEC DSBA`.
3. Paste the one-pager. Set font to 11pt, line spacing 1.15, narrow margins so it stays **one page**.
4. Share → General access → **Anyone with the link → Viewer**.
5. Copy the link.
6. Book on Calendly. In the invite notes / description, paste:
   - Track 3, product name Assiette
   - the Google Doc link
   - "Three specific questions are in the doc; I want your pressure-test on grounding vs. hallucination, RAG failure modes, and what you would build first."
7. Optional: attach screenshots of `docs/wireframes/01-home.html`, `02-results.html`, `03-detail.html` (open in Chrome, screenshot the phone frame).

## The story to tell in the first 3 minutes (in plain words)

Rather than reciting bullet points, this is the two-sentence version to actually say out loud, then unpack if he asks:

*"Students in Paris need cheap food almost every evening, and the information to find it is scattered across a government menu app and a dozen uncoordinated charity websites. I've designed — and I'm about to build — an assistant that reads a plain sentence like 'I'm in the 13th with €3, need dinner after 6pm,' looks up real verified options, and only lets an AI model describe what was actually found, never invents a place."*

Then, if useful, the decisions already locked in:

- **Track 3**, not the founder blueprint. I want a working prototype I can demo, not just a business plan.
- **The problem, restated simply:** international / budget students in Paris cannot get one honest answer to "where can I actually afford to eat tonight, near me."
- **I started from the person, not the technology.** The idea came from a real evening I personally lost to exactly this problem, not from "I want to build a RAG app, what problem could it solve."
- **The architecture, in order of trust:** first, plain logic and real data decide what's actually available (no AI guessing here); second, an AI model only writes the friendly summary and French phrases, and only about what the first step already found and verified.
- **What I'm building with:** Streamlit (a simple way to turn Python into a web app), Groq's free AI tier (model `openai/gpt-oss-20b`), no funding, Paris only, English and French only.
- **What I'm deliberately not building yet:** live booking of charity food slots, voice, user accounts. Not because they're impossible — because saying "not yet" clearly is what keeps this shippable this week.

## Where I am stuck / uncertain (say this next, honestly)

Being specific about doubt is more useful to him than pretending the plan is perfect. Three real open questions:

- **The "should I scrape logins" question.** The charities' *live* availability (how many food parcels are actually left tonight) sits behind their own booking forms and personal accounts. I've decided not to try to access that — it would mean logging in as if I were a student in need, which feels wrong, and it's technically fragile anyway. Is that the right call for a first version, or will a product like this feel incomplete without it?
- **The "can this ever be a real business" question.** The one free government data feed I'm using (CROUStillant) explicitly says its data cannot be used commercially. If this project ever grew beyond a course prototype, that's a real wall, not a small footnote. I want a sanity check on whether that kills the idea of a business entirely, or whether there's a version of this that still makes sense (for example, as a non-profit or university-run tool instead of a company).
- **The "how honest is too honest" question.** Many Paris university restaurants only serve lunch, so in the evening, "there is no subsidised hot meal near you right now" will often be the *correct* answer. How strict should that honesty be in a live demo, versus finding the most impressive-looking result?

## Burning AI questions to actually ask (these match the assignment's instructions)

1. **Feasibility / grounding.** "Given that my data is a mix of one clean government API and several messy charity websites, is my plan — look things up first, then let an AI model only describe what was found — solid enough with the tools available to a solo student? Or is 'the AI sounding confident about something false' the failure mode I should be designing against the hardest?"
2. **Failure modes.** "What actually goes wrong with apps like this in the real world — old information that looks current, users trusting a fluent sentence over an actual date-stamp, that kind of thing — and how would you defend a live demo against that in front of an audience?"
3. **What he would build first.** "If you had my exact plan and no funding, what would you personally build first, this weekend — the simple lookup-and-filter logic, or the AI-written part? Which one earns its place in version one, and which one could I have skipped?"

## What NOT to ask (per the course's own instructions)

Do not ask what consulting / luxury / FAANG firms hire for. Do not treat him as a general industry encyclopedia. Every question above is anchored to *this specific plan* and *this specific AI capability* — that is what makes the 30 minutes worth his time and mine.

## After the call (same day, while it's fresh)

Open [phase3-consultation-notes.md](phase3-consultation-notes.md) and fill it in — 8 to 12 lines is enough. Do this the same day; two days later the sharp, specific things he said will have blurred into a vague "he seemed positive," which is useless for the reflection. Those notes are the raw material for the **Result** section of [Phase 4](phase4-reflection.md) — write down what surprised you, not just what confirmed what you already believed.
