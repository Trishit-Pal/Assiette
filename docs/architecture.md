# Assiette v3 architecture

## Layers

1. **Vite SPA** (`frontend/`) — Canteen-Ticket UI (vanilla TypeScript). Built to `frontend/dist` and served by FastAPI.
2. **FastAPI** (`backend/api.py`) — `/query`, `/health`, `/auth/*`, plus `/`, `/about`, `/signin` for the SPA. Auth, rate limiting, validation, observability, CSP headers.
3. **Service** (`backend/services/query_service.py`) — orchestrates retrieval + grounded LLM.
4. **Retrieval** (`assiette/retrieval.py`) — deterministic ranking; distributions from Postgres when seeded.
5. **Data** — CROUStillant API (live, 30-min cache) + Postgres venues/schedules/versions.
6. **Worker** (`backend/refresh/worker.py`) — weekly refresh with diff log.

## Real-time honesty

| Source | Freshness |
|---|---|
| CROUS menus | ~30 minutes (API cache) |
| Distributions | Weekly refresh + `last_verified_at`; stale after 14d, refused after 30d |
| Parcel slots | Not available (by design) |

## Run locally

```bash
pip install -r requirements.txt
npm --prefix frontend install
copy .env.example .env
alembic upgrade head
python -m backend.db.seed
npm --prefix frontend run build
uvicorn backend.api:app --reload
```

Frontend iteration (API already running on :8000):

```bash
npm --prefix frontend run dev
```

Vite proxies `/query`, `/health`, `/auth` to `http://127.0.0.1:8000`.

Or with Docker: `docker compose up`.
