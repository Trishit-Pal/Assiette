"""Groq-backed intent parse + grounded itinerary. Template fallback if no key."""

from __future__ import annotations

import json
import re
from typing import Any

import requests
from pydantic import BaseModel, Field, ValidationError

from assiette.circuit import allow_request, record_failure, record_success
from assiette.http import GROQ_GENERATE_TIMEOUT, GROQ_PARSE_TIMEOUT, get_session
from assiette.retrieval import Intent, RankedPlace, heuristic_intent, places_to_context
from backend.config import get_settings
from backend.security import sanitise_context_rows, sanitise_for_llm

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
SERVICE = "groq"

_SAFE_WORDS = {
    "paris",
    "crous",
    "assiette",
    "france",
    "student",
    "étudiants",
    "etudiants",
    "restaurant",
    "cantine",
    "distribution",
    "association",
}


class IntentLLMOut(BaseModel):
    arrondissement: int | None = None
    budget_eur: float | None = None
    time_hhmm: str | None = None
    meal: str | None = None
    diet: str | None = None
    language: str | None = None
    bursary: bool | None = None


class StopLLMOut(BaseModel):
    id: str
    why: str = ""
    dietary_note: str = ""
    french_phrases: list[str] = Field(default_factory=list)


class ItineraryLLMOut(BaseModel):
    summary: str = ""
    stops: list[StopLLMOut] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


class GroqLLM:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key if api_key is not None else get_settings().groq_api_key.strip()
        self.model = model
        self.session = get_session()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str, temperature: float = 0.2, timeout=GROQ_GENERATE_TIMEOUT) -> str:
        if not self.available:
            raise RuntimeError("GROQ_API_KEY missing")
        if not allow_request(SERVICE):
            raise RuntimeError("groq circuit open")
        try:
            response = self.session.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            record_success(SERVICE)
            return payload["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, RuntimeError):
            record_failure(SERVICE)
            raise


def parse_intent_with_llm(query: str, llm: GroqLLM, overrides: dict[str, Any] | None = None) -> Intent:
    base = heuristic_intent(query, overrides)
    if not llm.available:
        return base
    system = (
        "Extract meal-search filters for a Paris student food assistant. "
        "Return JSON only with keys: arrondissement (1-20 or null), budget_eur (number or null), "
        "time_hhmm (HH:MM or null), meal (breakfast|lunch|dinner), diet (any|vegetarian|vegan|halal), "
        "language (en|fr), bursary (boolean). Do not add keys."
    )
    try:
        raw = llm.complete(system, query, temperature=0, timeout=GROQ_PARSE_TIMEOUT)
        parsed = IntentLLMOut.model_validate(_extract_json(raw) or {})
        data = parsed.model_dump()
    except (requests.RequestException, KeyError, RuntimeError, ValidationError):
        return base
    merged = {
        "arrondissement": data.get("arrondissement") or base.arrondissement,
        "budget_eur": data.get("budget_eur") if data.get("budget_eur") is not None else base.budget_eur,
        "time_hhmm": data.get("time_hhmm") or base.time_hhmm,
        "meal": data.get("meal") or base.meal,
        "diet": data.get("diet") or base.diet,
        "language": data.get("language") or base.language,
        "bursary": bool(data.get("bursary") if data.get("bursary") is not None else base.bursary),
        "category": base.category,
    }
    if overrides:
        for key, value in overrides.items():
            if value not in (None, "", "any"):
                merged[key] = value
    return Intent(query=query, **merged)


GROUNDING_RULES = """You are Assiette, a student meal assistant for Paris.
You MUST:
- Only mention venues whose names appear in the provided JSON context.
- Never invent a restaurant, address, hour, or dish.
- If nothing fits, say so and suggest relaxing budget, area, or time whiever is most suitable.
- If a distribution requires booking, say that in the first sentence about that stop.
- Never claim remaining parcels or live queue length.
- Prefer 2-3 stops. Honesty over completeness.
Return JSON only:
{
  "summary": "2-4 sentences",
  "stops": [
    {
      "id": "must match a context id",
      "why": "one or two sentences",
      "dietary_note": "short",
      "french_phrases": ["...", "..."]
    }
  ],
  "caveats": ["..."]
}
"""


def template_itinerary(
    intent: Intent,
    places: list[RankedPlace],
    knowledge: list[dict[str, str]],
) -> dict[str, Any]:
    top = places[:3]
    if intent.language == "fr":
        if not top:
            summary = "Je ne trouve pas d'option fiable dans les données pour ces critères. Élargissez le budget, l'arrondissement ou le créneau."
        else:
            names = ", ".join(p.name for p in top)
            summary = (
                f"Voici un itinéraire ancré dans les données pour « {intent.query} ». "
                f"Pistes: {names}. Les créneaux d'associations changent : vérifiez la source avant de vous déplacer."
            )
    else:
        if not top:
            summary = "No reliable option in the retrieved data for these constraints. Relax budget, area, or time."
        else:
            names = ", ".join(p.name for p in top)
            summary = (
                f"Grounded plan for “{intent.query}”: {names}. "
                "Association hours move — check the source before you travel. Assiette cannot see remaining parcels."
            )
    stops = []
    for place in top:
        phrases = [place.french_hint] if place.french_hint else []
        if place.source == "crous":
            phrases.append("Il reste un plat sans viande ?")
        elif place.booking_required:
            phrases.append("J’ai réservé en ligne. Faut-il un QR code ?")
        stops.append(
            {
                "id": place.id,
                "why": "; ".join(place.reasons[:3]),
                "dietary_note": (
                    "Basket contents vary; diet is not guaranteed."
                    if place.source == "distribution"
                    else (place.menu_text[:180] or "Menu not published yet.")
                ),
                "french_phrases": phrases[:3],
            }
        )
    caveats = [
        "Not a booking tool.",
        "CROUStillant data is non-commercial.",
    ]
    if knowledge:
        caveats.append(f"Rule snippet used: {knowledge[0]['title']}")
    return {"summary": summary, "stops": stops, "caveats": caveats, "engine": "template"}


_TITLE_CASE = re.compile(r"\b([A-ZÉÈÊÀÂÎÔÛÇ][\w'’\-]+(?:\s+[A-ZÉÈÊÀÂÎÔÛÇ][\w'’\-]+){0,4})\b")


def prose_is_grounded(text: str, places: list[RankedPlace]) -> bool:
    if not text:
        return True
    allowed = {p.name.lower() for p in places} | {p.org.lower() for p in places if p.org} | _SAFE_WORDS
    for match in _TITLE_CASE.findall(text):
        candidate = match.strip().lower()
        if len(candidate) < 4:
            continue
        if candidate in allowed:
            continue
        if any(candidate in name or name in candidate for name in allowed if len(name) >= 4):
            continue
        if " " not in candidate:
            continue
        return False
    return True


def generate_itinerary(
    intent: Intent,
    places: list[RankedPlace],
    knowledge: list[dict[str, str]],
    llm: GroqLLM | None = None,
    *,
    use_llm: bool = True,
) -> dict[str, Any]:
    allowed_ids = {p.id for p in places[:6]}
    fallback = template_itinerary(intent, places, knowledge)
    if not use_llm:
        return fallback
    llm = llm or GroqLLM()
    if not llm.available or not places:
        return fallback
    user = json.dumps(
        {
            "intent": intent.__dict__,
            "retrieved_venues": sanitise_context_rows(places_to_context(places, limit=6)),
            "knowledge_snippets": sanitise_context_rows(knowledge),
        },
        ensure_ascii=False,
    )
    try:
        raw = llm.complete(GROUNDING_RULES, user, temperature=0.2, timeout=GROQ_GENERATE_TIMEOUT)
        data = _extract_json(raw)
        parsed = ItineraryLLMOut.model_validate(data or {})
    except (requests.RequestException, KeyError, RuntimeError, ValidationError):
        return fallback
    clean_stops = []
    for stop in parsed.stops:
        if stop.id not in allowed_ids:
            continue
        clean_stops.append(
            {
                "id": stop.id,
                "why": sanitise_for_llm(stop.why, 400),
                "dietary_note": sanitise_for_llm(stop.dietary_note, 300),
                "french_phrases": [sanitise_for_llm(p, 200) for p in stop.french_phrases[:4]],
            }
        )
    if not clean_stops:
        return fallback
    summary = sanitise_for_llm(parsed.summary or fallback["summary"], 800)
    caveats = [sanitise_for_llm(c, 300) for c in (parsed.caveats or fallback["caveats"])]
    if not prose_is_grounded(summary, places) or not all(prose_is_grounded(c, places) for c in caveats):
        return fallback
    return {"summary": summary, "stops": clean_stops, "caveats": caveats, "engine": "groq"}
