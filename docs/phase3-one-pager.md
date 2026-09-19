# Assiette — Phase 1 + 2 one-pager (paste into Google Docs)

**How to submit:** Copy this entire document into a new Google Doc → Share → Anyone with the link (Viewer) → paste the link in your Calendly invite to Mr. Weng Wei. Target length: one page at 11pt, 1.15 line spacing, 1.6cm margins.

**Note on structure (not for the tutor, just for you):** this brief is Phases 1 and 2 compressed to a page, so in STAR terms it is "Situation + the start of Action." The full story — with the plain-English scenario and analogies — lives in [docs/00-star-story.md](00-star-story.md) if you want to rehearse the two-minute verbal version before the call.

Everything from the line below down is what gets copied into the Google Doc. Keep it plain and specific — that reads as more credible to an experienced engineer than polished buzzwords.

---

**Assiette** — an AI meal assistant for budget-constrained students in Paris  
Trishit · ESSEC–CentraleSupélec DSBA M2 · Track 3 · Consultation brief for Mr. Weng Wei · Sept 2026

## Phase 1 — The problem (people first)

International and low-budget students in Paris decide, almost daily, where they can eat a complete meal they can afford and are allowed to access. The decision clusters between 17:30 and 20:30: a remaining €1–€3.30, a metro ride, French signage, and a distribution that may require a prior booking.

What they do today is a patchwork. CROUS / CROUStillant show menus but do not reason over *my* arrondissement, *my* budget, or *my* arrival time. Linkee, Cop1, Restos du Cœur, Secours Populaire and others publish hours on separate sites, the Maison étudiante portal, and Instagram. Google Maps does not know student tariffs or eligibility. Group chats go stale. A wrong trip costs a closed RU or a volunteer asking for documents the student did not bring — often with no French sentence ready.

I am the right person for a v1 because I live this as an international M2 student, I can test with classmates who will flag a bad recommendation immediately, and I can treat it as a data problem (live menus + a curated eligibility table) rather than a chatbot with opinions.

**One sentence:** no existing tool takes an English or French need (“13th, €3, dinner after 18:00”) and returns a grounded itinerary mixing social-tariff CROUS meals and free student distributions, plus the French to use at the door.

## Phase 2 — Simplest AI application that addresses it

**Core AI capability:** retrieval + deterministic recommendation + grounded generation. Not classification-only, not unconstrained generation.

**Inputs.** (1) A sentence + optional filters (arrondissement, budget, meal slot, diet). (2) Live Paris CROUS restaurants and menus from the CROUStillant API (region code 22; free; custom User-Agent; 200 req/min; **non-commercial terms**). (3) A curated `distributions.json` (~15 Paris points: Linkee, Cop1, Restos du Cœur, Secours Populaire, Ordre de Malte, …) with hours, eligibility, lat/lng, `last_verified`. (4) A small `knowledge.md` of rules and door-level French phrases.

**Two key interactions.** A: type a need → ranked 2–3 stop itinerary + map of retrieved pins only. B: open a stop → eligibility, menu snippet or “bring card + bag,” dietary note, copyable French.

**v1 will not build:** live parcel/slot inventory behind Linkee/Cop1 logins; voice; accounts; payments; native mobile; cities outside Paris; languages other than EN/FR; hallucinated venues.

**Stack I can actually ship:** Streamlit + Python + Groq `openai/gpt-oss-20b` (free tier) + CROUStillant + the JSON. LLM parses intent, then **must answer only from retrieved rows**. If Groq or CROUStillant is down, a template + snapshot fallback still demos.

**Biggest risk:** a fluent answer that is stale or overconfident (distribution moved, booking already closed). Defence: timestamps on every card, grounding contract, no claim of remaining stock.

## Three questions for the 30-minute consultation

1. Given mixed public sources (a clean CROUS API + messy association pages), is retrieval + grounded generation technically robust enough, or will **hallucinated venues / invented hours** be the failure mode I should design around first?
2. What failure modes have you seen in RAG-over-public-data apps like this (stale crawls, prompt injection via scraped text, students trusting the model over the timestamp), and how would you defend a 3-minute demo?
3. If you started from this spec today with no funding, would you build **structured filter-first** (what I sketched) or **LLM-first**, and what is the first slice you would actually ship this weekend?

Wireframes (home / results / detail) sit in the project folder `docs/wireframes/` and can be opened in a browser.
