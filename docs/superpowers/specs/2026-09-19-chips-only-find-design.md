# Chips-only Find — locked design (2026-09-19)

This document records the production student search UX and API contract after PR #12 (`blank-env-unset`). It is normative for future work on Find/Refresh; it does not restate unrelated auth or deployment details.

## Summary

Students refine **optional filter chips** (arrondissement, budget, meal, diet, category, bursary). There is **no free-text query** on the home page. Intent is derived entirely from chip state. Search remains **public** (no sign-in gate).

## Find and Refresh flow

1. **Find** — User clicks Find (or a preset). The SPA builds a `QueryRequest`-shaped payload from chip state only and calls **GET `/retrieve`** with query parameters. The response returns ranked **tickets** (`places`), `intent`, cache metadata, and optional `empty_reason`.
2. **Compose** — When places exist, the client calls **POST `/compose`** with `intent`, `place_ids` from retrieval, and `data_version`. The server builds a **template itinerary** (`engine: template`); Groq is not used on this path (`use_llm=False`).
3. **Refresh** — Polling revalidates **GET `/retrieve`** on focus/interval (same chip-derived params). Generation is **not** auto-revalidated; the user must Find again to rerun compose.

The legacy **POST `/query`** endpoint remains a retrieve-then-compose wrapper for tests and integrations; it also uses `use_llm=False`.

```
Chips → GET /retrieve → tickets
              ↓
      POST /compose → template summary + stops (grounded to place_ids)
```

## Optional chips and presets

All filter chips are optional except defaults baked into composer state (e.g. meal/diet/category defaults). Users may search with minimal selection.

Three **presets** only set chip state (no extra presets):

| Preset   | Arr. | Meal    | Budget | Diet        | Category      |
|----------|------|---------|--------|-------------|---------------|
| 13e dinner | 13 | dinner  | €3.30  | —           | —             |
| Veg 5e   | 5    | lunch   | €3.30  | vegetarian  | —             |
| Free     | —    | dinner  | €0     | —           | distribution  |

Presets do not bypass retrieval or invent venues.

## API models (no required query string)

**`QueryRequest`** — chip fields only: `arrondissement`, `budget_eur`, `meal`, `diet`, `bursary`, `category`, `use_network`, `refresh`. No `query`, `q`, or other natural-language field.

**`ComposeRequest`** — `intent` (dict from retrieval/chips), `place_ids`, optional `data_version`, `use_network`. No query string.

Intent for ranking is built server-side via `intent_from_request` / `intent_from_payload` with `parse_query=False` on the student path.

## Grounding and LLM

- Venues must come from retrieval (CROUS + seeded distributions). Compose filters `place_ids` to IDs present in the retrieved candidate set.
- **No Groq on the student path**: even if `GROQ_API_KEY` is set, `/compose` and `/query` call `generate_itinerary(..., use_llm=False)`.

## Production configuration guards

- **`SECRET_KEY`**: In production (`ENV=production` or `VERCEL_ENV=production`), settings validation **raises** if `SECRET_KEY` is the default placeholder or shorter than 32 characters.
- **Blank env strings**: `_blank_env_as_unset` treats empty-string environment values as unset so Vercel “blank secret” entries do not break int/bool parsing.

## Vercel entry (`api/index.py`)

- Top-level `app = FastAPI()` is required for Vercel detection, then replaced by `backend.api.app` on successful import.
- On import failure, boot error strings are bound as **default arguments** on a catch-all route so responses remain JSON with `status: boot_error` after the `except` block ends.

## Explicitly out of scope

- Clerk or any new identity provider; magic-link auth stays UI-only.
- Gating search behind authentication.
- Additional presets, time chips, or bursary-only chips beyond existing composer UI.
- Groq-generated copy on Find/Refresh.
- Restyling the SPA.
