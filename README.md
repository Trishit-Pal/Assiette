# Assiette

Track 3 course prototype: an AI assistant that turns *“I’m in the 13th, €3, dinner after 18:00”* into a **grounded** itinerary of cheap Paris student meals (live CROUS menus + curated food distributions) and the French to use at the door.

This is a non-commercial student project. CROUStillant [forbids commercial use](https://www.data.gouv.fr/dataservices/api-croustillant) of their API.

**New here?** For the full product + how to run it, read [docs/00-product-guide.md](docs/00-product-guide.md). For the story only (STAR method), start with [docs/00-star-story.md](docs/00-star-story.md).

## Run the prototype (v3)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm --prefix frontend install
copy .env.example .env
alembic upgrade head
python -m backend.db.seed
npm --prefix frontend run build
uvicorn backend.api:app --reload
```

Open http://127.0.0.1:8000 — FastAPI serves the Canteen-Ticket UI from `frontend/dist`.

Frontend hot-reload (API already on :8000): `npm --prefix frontend run dev` then open http://127.0.0.1:5173.

Or with Docker: `docker compose up`

Without `GROQ_API_KEY` the app still runs: heuristic intent + template itinerary. With a key it uses `openai/gpt-oss-20b` for parsing and grounded copy, then **drops any stop whose id was not retrieved**.

**v3 UI:** standalone Vite frontend (vanilla TypeScript), Canteen-Ticket identity, EN/FR + light/dark, magic-link auth screens, trust page. Streamlit is gone.

**v2 backend:** FastAPI service, Postgres/SQLite persistence, weekly refresh worker, magic-link auth, rate limiting, observability, CI. See [docs/architecture.md](docs/architecture.md), [docs/design-system.md](docs/design-system.md) and [docs/phase5-upgrade-notes.md](docs/phase5-upgrade-notes.md).

## Demo queries (seeded in the UI)

- I live in the 13th, €3 budget, dinner after 18:00
- Je suis végétarien, 5e arrondissement, déjeuner à midi, budget 3,30€
- Where can I get a free food basket this Thursday evening near Bastille?
- I'm new, I don't speak French, cheapest dinner in the 18th
- Halal-friendly lunch near Jussieu under €4

## Course deliverables

| STAR stage | Phase | File |
|---|---|---|
| The whole story, plain language | — | [docs/00-star-story.md](docs/00-star-story.md) |
| Situation | 1 Problem statement | [docs/phase1-problem-statement.md](docs/phase1-problem-statement.md) |
| Action (design) | 2 Spec | [docs/phase2-solution-spec.md](docs/phase2-solution-spec.md) |
| Action (design) | 2 Wireframes | [docs/wireframes/index.html](docs/wireframes/index.html) |
| Action (validate before building) | 3 One-pager (paste into Google Docs) | [docs/phase3-one-pager.md](docs/phase3-one-pager.md) |
| Action (validate before building) | 3 Tutor briefing + Calendly | [docs/phase3-tutor-briefing.md](docs/phase3-tutor-briefing.md) |
| Result | 4 Reflection | [docs/phase4-reflection.md](docs/phase4-reflection.md) |

**You must still:** paste the one-pager into Google Docs, share the link, and book https://calendly.com/wuvist/30min by 7 September.

## How the AI is actually used

1. Parse the sentence into filters (arrondissement, budget, meal, diet).
2. Retrieve Paris CROUS restaurants (region `22`) + `data/distributions.json`.
3. Rank with transparent scores (proximity, price, open-for-slot).
4. Fetch today’s menu only for a shortlist of CROUS sites.
5. Generate an itinerary **only from retrieved rows**.

## Tests

```bash
pytest -q
```
