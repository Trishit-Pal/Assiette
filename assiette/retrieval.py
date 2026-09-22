"""Deterministic retrieval + ranking, plus lightweight knowledge search."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Literal

from assiette.crous_client import (
    CROUS_BURSARY_PRICE,
    CROUS_STUDENT_PRICE,
    CrousClient,
    crous_open_for_meal,
    flatten_menu,
    normalize_restaurant,
)
from assiette.geo import (
    arrondissement_from_query,
    arrondissement_tier,
    meal_from_minutes,
    meal_to_crous_slot,
    parse_hhmm,
    proximity_score,
    weekday_name,
)
from assiette.paths import DISTRIBUTIONS_PATH, KNOWLEDGE_PATH

DIET_KEYWORDS = {
    "vegetarian": (
        "végétarien",
        "vegetarien",
        "vegetarian",
        "veggie",
        "sans viande",
        "tofu",
        "fromage",
        "salade",
    ),
    "vegan": ("vegan", "végan", "végétalien", "vegetalien", "végétal"),
    "halal": ("halal",),
}

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you",
    "les", "des", "une", "dans", "pour", "avec", "que", "qui", "pas",
}

MIN_EXACT_ARRONDISSEMENT_RESULTS = 4
DISPLAY_LIMIT = 10
BUDGET_EPSILON = 0.05
_ARR_RANK = {"exact": 0, "nearby": 1, "unscoped": 2}

ArrMatch = Literal["exact", "nearby", "unscoped"]
BudgetMatch = Literal["ok", "unscoped"]
MealMatch = Literal["open", "closed"]
DietMatch = Literal["match", "not_confirmed", "not_applicable"]


Category = Literal["any", "crous", "distribution"]


@dataclass
class Intent:
    query: str
    arrondissement: int | None = None
    budget_eur: float | None = None
    time_hhmm: str | None = None
    meal: str = "lunch"
    diet: str = "any"
    language: str = "en"
    bursary: bool = False
    category: Category = "any"


@dataclass
class MatchRecord:
    arrondissement: ArrMatch = "unscoped"
    budget: BudgetMatch = "unscoped"
    meal: MealMatch = "open"
    diet: DietMatch = "not_applicable"


@dataclass
class RankedPlace:
    id: str
    source: str
    name: str
    org: str
    kind: str
    address: str
    arrondissement: int | None
    latitude: float | None
    longitude: float | None
    price_eur: float
    open_for_request: bool
    schedule_text: str
    eligibility: str
    menu_text: str
    booking_required: bool
    last_verified: str
    source_url: str
    french_hint: str
    notes: str
    score: float
    reasons: list[str] = field(default_factory=list)
    diet_match: bool = True
    crous_code: int | None = None
    match: MatchRecord = field(default_factory=MatchRecord)


def _parse_last_verified_utc(raw: str) -> datetime | None:
    text = raw.strip()
    if not text:
        return None
    if "T" in text:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    else:
        dt = datetime.strptime(text[:10], "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_distributions(path=None, db_session=None) -> dict:
    del db_session  # kept for callers; catalog is always JSON-backed
    payload = json.loads((path or DISTRIBUTIONS_PATH).read_text(encoding="utf-8"))
    from backend.repo import freshness_status

    kept: list[dict] = []
    for row in payload.get("distributions") or []:
        verified = _parse_last_verified_utc(str(row.get("last_verified") or ""))
        if verified is not None and freshness_status(verified) == "refused":
            continue
        kept.append(row)
    return {"distributions": kept, "last_compiled": payload.get("last_compiled")}


@lru_cache(maxsize=4)
def knowledge_chunks(path=None) -> list[tuple[str, str]]:
    text = (path or KNOWLEDGE_PATH).read_text(encoding="utf-8")
    chunks: list[tuple[str, str]] = []
    current_title = "intro"
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                chunks.append((current_title, "\n".join(current).strip()))
            current_title = line[3:].strip()
            current = []
        else:
            current.append(line)
    if current:
        chunks.append((current_title, "\n".join(current).strip()))
    return chunks


def _tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-zàâçéèêëîïôùûüÿœæ0-9]+", text.lower())
        if len(tok) > 2 and tok not in STOPWORDS
    }


def search_knowledge(query: str, limit: int = 3) -> list[dict[str, str]]:
    q = _tokens(query)
    scored: list[tuple[float, str, str]] = []
    for title, body in knowledge_chunks():
        corpus = _tokens(title + " " + body)
        if not q or not corpus:
            continue
        overlap = len(q & corpus)
        if overlap:
            scored.append((overlap / max(len(q), 1), title, body))
    scored.sort(reverse=True)
    return [{"title": t, "body": b[:900]} for _, t, b in scored[:limit]]


def heuristic_intent(query: str, overrides: dict[str, Any] | None = None) -> Intent:
    overrides = overrides or {}
    q = query.lower()
    language = "fr" if re.search(r"\b(je|j'|où|budget|arrondissement|déjeuner|dîner|diner)\b", q) else "en"
    if "je suis" in q or "où" in q or "déjeuner" in q:
        language = "fr"
    bursary = bool(re.search(r"boursier|boursière|bursary|grant", q))
    diet = "any"
    if re.search(r"vegan|végan|végétalien", q):
        diet = "vegan"
    elif re.search(r"végétarien|vegetarien|vegetarian|veggie", q):
        diet = "vegetarian"
    elif "halal" in q:
        diet = "halal"

    budget = None
    money = re.search(r"€\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*€", query)
    if money:
        budget = float((money.group(1) or money.group(2)).replace(",", "."))
    if re.search(r"\bfree\b|gratuit|panier", q) and budget is None:
        budget = 0.0

    time_hhmm = None
    tm = re.search(r"\b(\d{1,2})[:hH](\d{2})\b", query)
    if tm:
        time_hhmm = f"{int(tm.group(1)):02d}:{tm.group(2)}"
    elif re.search(r"after\s+(\d{1,2})\b", q):
        hour = int(re.search(r"after\s+(\d{1,2})", q).group(1))
        time_hhmm = f"{hour:02d}:00"
    elif "18:00" in query or "18h" in q:
        time_hhmm = "18:00"

    explicit_meal = None
    if re.search(r"breakfast|petit[- ]déjeuner|matin", q):
        explicit_meal = "breakfast"
    elif re.search(r"lunch|déjeuner|midi", q):
        explicit_meal = "lunch"
    elif re.search(r"dinner|dîner|diner|soir|tonight|ce soir", q):
        explicit_meal = "dinner"
    elif q.startswith("any "):
        explicit_meal = "any"

    meal = meal_from_minutes(parse_hhmm(time_hhmm), explicit_meal)
    arr = arrondissement_from_query(query)

    intent = Intent(
        query=query,
        arrondissement=arr,
        budget_eur=budget,
        time_hhmm=time_hhmm,
        meal=meal,
        diet=diet,
        language=language,
        bursary=bursary,
    )
    for key, value in overrides.items():
        if value in (None, "", "any"):
            continue
        if hasattr(intent, key):
            setattr(intent, key, value)
    return intent


def _diet_hit(text: str, diet: str) -> bool:
    if diet == "any":
        return True
    blob = text.lower()
    return any(k in blob for k in DIET_KEYWORDS.get(diet, ()))


def _distribution_schedule_text(row: dict) -> str:
    bits = [f"{slot['weekday']} {slot['start']}–{slot['end']}" for slot in row.get("schedule") or []]
    return " · ".join(bits)


def _distribution_open(row: dict, weekday: str, hhmm: str | None, meal: str) -> bool:
    slots = [s for s in row.get("schedule") or [] if s.get("weekday") == weekday]
    if not slots:
        return False
    t = parse_hhmm(hhmm)
    for slot in slots:
        start = parse_hhmm(slot["start"])
        end = parse_hhmm(slot["end"])
        if t is not None and end is not None:
            # "after 18:00" still matches a 19:30 distribution the same evening.
            if t <= end:
                return True
            continue
        if meal == "dinner" and start is not None and start >= 16 * 60:
            return True
        if meal == "breakfast" and end is not None and end <= 12 * 60:
            return True
        if meal in {"lunch", "any"}:
            return True
    return False


def _diet_status(intent: Intent, *, source: str) -> DietMatch:
    if intent.diet == "any":
        return "not_applicable"
    if source == "distribution":
        return "not_confirmed"
    return "not_confirmed"


def _place_sort_key(place: RankedPlace, selected_arr: int | None) -> tuple:
    open_key = 0 if place.open_for_request else 1
    diet_key = 0 if place.match.diet == "match" else 1
    if selected_arr is not None:
        return (
            _ARR_RANK.get(place.match.arrondissement, 3),
            open_key,
            diet_key,
            place.price_eur,
            place.id,
        )
    return (open_key, diet_key, place.price_eur, place.id)


def _derived_score(place: RankedPlace) -> float:
    score = 100.0 if place.open_for_request else 0.0
    if place.match.arrondissement == "exact":
        score += 20
    elif place.match.arrondissement == "nearby":
        score += 10
    if place.match.diet == "match":
        score += 5
    return score


def rank_places(
    intent: Intent,
    *,
    client: CrousClient | None = None,
    when: datetime | None = None,
    use_network: bool = True,
    menu_limit: int = 8,
    db_session=None,
    force_refresh: bool = False,
) -> tuple[list[RankedPlace], dict[str, Any]]:
    when = when or datetime.now()
    weekday = weekday_name(when)
    client = client or CrousClient()
    restaurants, crous_status = client.list_paris_restaurants(
        use_network=use_network, force=force_refresh and use_network
    )
    dist_payload = load_distributions(db_session=db_session)
    distributions = dist_payload.get("distributions") or []

    crous_price = CROUS_BURSARY_PRICE if intent.bursary else CROUS_STUDENT_PRICE
    budget = intent.budget_eur
    meta: dict[str, Any] = {
        "weekday": weekday,
        "crous_status": crous_status,
        "distributions_compiled": dist_payload.get("last_compiled"),
        "knowledge": search_knowledge(intent.query + " " + intent.diet + " " + intent.meal),
        "pre_filter_candidate_count": 0,
        "dropped_by_budget": 0,
        "dropped_by_arrondissement": 0,
        "arrondissement_relaxed_to_nearby": False,
    }

    candidates: list[RankedPlace] = []
    include_crous = intent.category != "distribution"
    include_dist = intent.category != "crous"

    def _passes_hard_filters(place_arr: int | None, price: float) -> ArrMatch | None:
        meta["pre_filter_candidate_count"] += 1
        tier = arrondissement_tier(place_arr, intent.arrondissement)
        if intent.arrondissement is not None and tier == "out_of_range":
            meta["dropped_by_arrondissement"] += 1
            return None
        if budget is not None and price > budget + BUDGET_EPSILON:
            meta["dropped_by_budget"] += 1
            return None
        return tier

    for raw in restaurants if include_crous else ():
        n = normalize_restaurant(raw)
        if n["latitude"] is None or n["arrondissement"] is None:
            if n.get("zone") in {"Petite couronne", "Aubervilliers"}:
                continue
        open_meal = crous_open_for_meal(n, weekday, intent.meal) and n.get("ouvert", True)
        price = crous_price
        arr_match = _passes_hard_filters(n["arrondissement"], price)
        if arr_match is None:
            continue
        reasons: list[str] = []
        _, prox_why = proximity_score(n["arrondissement"], intent.arrondissement)
        reasons.append(prox_why)
        if open_meal:
            reasons.append(f"flagged open for {intent.meal}")
        else:
            reasons.append(f"likely closed for {intent.meal}")
        if budget is not None:
            reasons.append(f"fits budget (€{price:.2f})")
        diet = _diet_status(intent, source="crous")
        place = RankedPlace(
            id=n["id"],
            source="crous",
            name=n["name"],
            org="CROUS",
            kind=n["kind"],
            address=n["address"],
            arrondissement=n["arrondissement"],
            latitude=n["latitude"],
            longitude=n["longitude"],
            price_eur=price,
            open_for_request=open_meal,
            schedule_text=n["hours_text"],
            eligibility=n["eligibility"],
            menu_text="",
            booking_required=False,
            last_verified=n["last_verified"],
            source_url=n["source_url"],
            french_hint=n["french_hint"],
            notes=n["zone"],
            score=0,
            reasons=reasons,
            diet_match=True,
            crous_code=n.get("code"),
            match=MatchRecord(
                arrondissement=arr_match,
                budget="unscoped" if budget is None else "ok",
                meal="open" if open_meal else "closed",
                diet=diet,
            ),
        )
        candidates.append(place)

    for row in distributions if include_dist else ():
        open_req = _distribution_open(row, weekday, intent.time_hhmm, intent.meal)
        price = float(row.get("price_eur") or 0)
        arr_match = _passes_hard_filters(row.get("arrondissement"), price)
        if arr_match is None:
            continue
        reasons: list[str] = []
        _, prox_why = proximity_score(row.get("arrondissement"), intent.arrondissement)
        reasons.append(prox_why)
        if open_req:
            reasons.append(f"scheduled {weekday}")
        else:
            reasons.append(f"not scheduled {weekday} at that time")
        if budget is not None:
            reasons.append(f"fits budget (€{price:.2f})")
        if row.get("booking_required"):
            reasons.append("prior booking usually required")
        if intent.diet != "any":
            reasons.append("diet not confirmed")
        diet = _diet_status(intent, source="distribution")
        candidates.append(
            RankedPlace(
                id=row["id"],
                source="distribution",
                name=row["name"],
                org=row.get("org") or "",
                kind=row.get("kind") or "distribution",
                address=row.get("address") or "",
                arrondissement=row.get("arrondissement"),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                price_eur=price,
                open_for_request=open_req,
                schedule_text=_distribution_schedule_text(row),
                eligibility=row.get("eligibility") or "",
                menu_text=row.get("notes") or "",
                booking_required=bool(row.get("booking_required")),
                last_verified=row.get("last_verified") or "",
                source_url=row.get("source_url") or "",
                french_hint=row.get("french_hint") or "",
                notes=row.get("notes") or "",
                score=0,
                reasons=reasons,
                diet_match=True,
                match=MatchRecord(
                    arrondissement=arr_match,
                    budget="unscoped" if budget is None else "ok",
                    meal="open" if open_req else "closed",
                    diet=diet,
                ),
            )
        )

    candidates.sort(key=lambda p: _place_sort_key(p, intent.arrondissement))

    slot = meal_to_crous_slot(intent.meal)
    to_fetch = [
        p for p in candidates if p.source == "crous" and p.crous_code
    ][:menu_limit]

    def _fetch_menu(place: RankedPlace) -> None:
        payload, menu_status = client.menu_for(
            int(place.crous_code), date=when, use_network=use_network, force=force_refresh and use_network
        )
        place.menu_text = flatten_menu(payload, slot) or flatten_menu(payload)
        place.reasons.append(menu_status)
        if intent.diet != "any":
            place.diet_match = _diet_hit(place.menu_text, intent.diet)
            if place.diet_match:
                place.match.diet = "match"
                place.reasons.append(f"menu mentions {intent.diet}")
            elif place.menu_text:
                place.match.diet = "not_confirmed"
                place.reasons.append("diet not obvious on menu")

    if to_fetch:
        with ThreadPoolExecutor(max_workers=min(6, len(to_fetch))) as pool:
            list(pool.map(_fetch_menu, to_fetch))

    candidates.sort(key=lambda p: _place_sort_key(p, intent.arrondissement))
    if intent.arrondissement is not None:
        exact_n = sum(1 for p in candidates if p.match.arrondissement == "exact")
        if exact_n >= MIN_EXACT_ARRONDISSEMENT_RESULTS:
            candidates = [p for p in candidates if p.match.arrondissement != "nearby"]
            meta["arrondissement_relaxed_to_nearby"] = False
        else:
            meta["arrondissement_relaxed_to_nearby"] = any(
                p.match.arrondissement == "nearby" for p in candidates
            )
    meta["menu_fetches"] = len(to_fetch)
    ranked = candidates[:DISPLAY_LIMIT]
    for place in ranked:
        place.score = _derived_score(place)
    return ranked, meta


def places_to_context(places: list[RankedPlace], limit: int = 6) -> list[dict[str, Any]]:
    rows = []
    for place in places[:limit]:
        rows.append(
            {
                "id": place.id,
                "source": place.source,
                "name": place.name,
                "org": place.org,
                "address": place.address,
                "arrondissement": place.arrondissement,
                "price_eur": place.price_eur,
                "open_for_request": place.open_for_request,
                "schedule": place.schedule_text,
                "eligibility": place.eligibility,
                "menu_or_notes": place.menu_text or place.notes,
                "booking_required": place.booking_required,
                "last_verified": place.last_verified,
                "french_hint": place.french_hint,
                "reasons": place.reasons,
            }
        )
    return rows
