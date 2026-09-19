# Phase 5 — v2 upgrade notes

## What changed from v1

| Area | v1 | v2 |
|---|---|---|
| Persistence | JSON files only | Postgres/SQLite + Alembic migrations |
| API | In-process Streamlit | FastAPI service layer |
| Distributions freshness | Static `last_verified` in JSON | DB timestamps + weekly refresh worker + diff log |
| Security | `.env` key only | Rate limits, CSP, sanitisation, student magic-link auth |
| Observability | None | structlog query_log + optional Sentry |
| UX | Basic dark page | Loading skeletons, empty/error states, offline chip, copyable French |
| CI | None | GitHub Actions (ruff, alembic, pytest) |

## What did not change

- Grounding contract (no invented venues)
- Template fallback when Groq is down
- No live parcel/booking scraping
- Paris only, EN/FR only
- Non-commercial stance

## How to demo v2 / v3

1. `npm --prefix frontend run build`
2. `uvicorn backend.api:app --reload`
3. Open http://127.0.0.1:8000
4. Query: *"I live in the 13th, €3 budget, dinner after 18:00"*
5. Point out: ticket stamp (last verified), offline chip if the API is down, grounding (no invented venues)
