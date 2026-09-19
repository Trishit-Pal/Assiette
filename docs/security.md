# Assiette security notes

## Threat model (v2)

- Untrusted user text in queries
- Untrusted public charity page text in retrieval context
- API keys (Groq) and database credentials
- Rate abuse against Groq / CROUStillant

## Controls

1. **Input validation** — Pydantic schemas on `/query` and `/auth/*`.
2. **Rate limiting** — `slowapi`, 30 req/min per IP (configurable).
3. **Prompt-injection sanitisation** — `backend/security.py` strips HTML and known injection patterns before LLM context; structured JSON only.
4. **Grounding enforcement** — itinerary stops must match retrieved venue ids (unchanged from v1).
5. **Auth** — magic-link for allowed student email domains only.
6. **Headers** — CSP, X-Content-Type-Options, X-Frame-Options on API responses.
7. **Secrets** — `GROQ_API_KEY` and `SECRET_KEY` via environment only; never logged.

## Non-commercial constraint

CROUStillant API terms forbid commercial use. Assiette v2 remains a non-commercial student/civic tool.
