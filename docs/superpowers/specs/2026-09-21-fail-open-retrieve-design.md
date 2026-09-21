# Fail-open retrieve — locked design (2026-09-21)

When Postgres/Neon is unreachable, student search must still return grounded venues from public CROUStillant data and bundled JSON (`data/distributions.json`, `data/fallback_restaurants.json`). Retrieval never hard-fails with HTTP 503 for SQLAlchemy errors.

## Behavior

- **GET `/retrieve`** and **POST `/compose`** do not return `503 Database unavailable` for SQLAlchemy failures.
- On DB errors during version lookup or refresh metadata: log, set `data_version` to `"snapshot"`, pass `db_session=None` into `rank_places`, and omit `refreshed_at` (no `last_refresh` read).
- Ranking continues via existing `load_distributions` / `CrousClient` fallbacks; venues are never invented.
- **`refresh=true`** still forces a network refresh path in ranking but does **not** call `seed_distributions()`.
- ETag / 304 logic: if DB calls for version or `last_refresh` fail, skip conditional 304 and still run retrieval.

## Out of scope

Clerk, new API keys, IndexedDB, seed-on-deploy, CI/CD or `vercel.json` changes.
