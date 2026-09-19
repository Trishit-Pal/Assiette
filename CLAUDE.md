# Assiette

Non-commercial Paris student meal finder. FastAPI + Vite vanilla TS. Groq writes copy; retrieval decides which venues exist. Production target: Vercel Hobby + Neon + Upstash, polling freshness only.

## Commands

```bash
pip install -r requirements.txt
npm --prefix frontend install
copy .env.example .env
alembic upgrade head
python -m backend.db.seed
npm --prefix frontend run build
python -m uvicorn backend.api:app --reload   # http://127.0.0.1:8000
npm --prefix frontend run dev                # Vite on :5173, proxies API
ruff check backend assiette tests
pytest -q
python -m backend.refresh.worker --source all
```

## Layout

- `frontend/src/` — SPA (home query, /signin, /about). Tickets in `components/ticketCard.ts`.
- `backend/api.py` — `/query` `/retrieve` `/compose` `/health` `/auth/*` `/venues`; serves `frontend/dist` in local dev.
- `api/index.py` — Vercel Python ASGI entry.
- `backend/services/query_service.py` — retrieve then generate.
- `assiette/retrieval.py` — CROUS + `data/distributions.json` (also seeded to SQLite/Postgres).
- `assiette/llm.py` — two Groq JSON calls; **drops stop ids not in retrieval**. Template fallback if no key / Groq down.
- `backend/refresh/pipeline.py` — warms CROUS cache and re-reads the JSON into the DB (not live charity scrapes). Triggered by `POST /internal/refresh`.

## Invariants

- Never invent a venue. Grounding is code, not just the prompt (`tests/test_retrieval.py`, `tests/test_api.py`).
- Paris only (CROUS region 22, arr. 1–20). No live parcel counts. CROUStillant is non-commercial.
- Do not add an agent/tool loop. Retrieve first, then generate.
- Polling only: no websockets, no SSE. Revalidate `/retrieve` on focus/interval; never auto-revalidate generation.

## Gotchas

- Windows: `python -m uvicorn` (bare `uvicorn` may be blocked). PowerShell: `;` not `&&`.
- `GROQ_API_KEY` optional. Empty → heuristic intent + template itinerary.
- Magic-link `/auth/*` is UI-only; `/query` is unauthenticated. Dev mode returns `dev_token` only when `ENV` is not production and SMTP/Resend are unset. Student domains: `ALLOWED_STUDENT_DOMAINS`.
- SQLite default (`assiette.db`). Lifespan does **not** seed unless `ASSIETTE_AUTO_INIT_DB=1`. After pulling schema changes run `alembic upgrade head`.
- Frontend `render()` rebuilds on route/lang/auth only. Chip clicks and query submit must not call it; results patch `#results`.
- Rate limit (SlowAPI) uses rightmost-trusted `X-Forwarded-For`. TestClient is fine.
- Production `SECRET_KEY` must be 32+ chars. `REFRESH_TOKEN` must be 32+ chars or `/internal/refresh` is not mounted.
- Vercel Hobby is non-commercial-only. No donation links.
