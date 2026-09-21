"""Cacheable retrieval: intent → ranked venues, no LLM generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from assiette.cache import DATAV_KEY, LIST_HARD_TTL, LIST_KEY, RETR_HARD_TTL, cache_get, cache_set, retr_key
from assiette.llm import GroqLLM
from assiette.retrieval import DISPLAY_LIMIT, Intent, MatchRecord, RankedPlace, rank_places
from backend.models.schemas import EmptyReasonOut, MatchRecordOut, QueryRequest, RankedPlaceOut, SourceMeta
from backend.observability import get_logger
from backend.repo import VenueRepository, freshness_status

logger = get_logger("retrieval_service")

COLD_MENU_LIMIT = 3
WARM_MENU_LIMIT = 6


def _round_time(hhmm: str | None) -> str | None:
    if not hhmm or ":" not in hhmm:
        return hhmm
    try:
        hour, minute = hhmm.split(":")[:2]
        bucket = (int(minute) // 30) * 30
        return f"{int(hour):02d}:{bucket:02d}"
    except ValueError:
        return hhmm


def intent_hash(intent: Intent, weekday: str | None = None) -> str:
    payload = {
        "arr": intent.arrondissement,
        "budget": intent.budget_eur,
        "meal": intent.meal,
        "diet": intent.diet,
        "bursary": intent.bursary,
        "category": intent.category,
        "time": _round_time(intent.time_hhmm),
        "weekday": weekday or datetime.now().strftime("%A"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _chip_label(req: QueryRequest) -> str:
    bits: list[str] = []
    if req.meal and req.meal != "any":
        bits.append(req.meal)
    if req.arrondissement is not None:
        bits.append(f"{req.arrondissement}e")
    if req.budget_eur is not None:
        bits.append(f"€{req.budget_eur:g}")
    if req.diet != "any":
        bits.append(req.diet)
    if req.category != "any":
        bits.append(req.category)
    return " · ".join(bits) or "filters"


def intent_from_request(req: QueryRequest, llm: GroqLLM | None = None, *, parse_query: bool = False) -> Intent:
    del llm, parse_query
    meal = req.meal or "any"
    return Intent(
        query=_chip_label(req),
        arrondissement=req.arrondissement,
        budget_eur=req.budget_eur,
        time_hhmm=None,
        meal=meal,
        diet=req.diet,
        bursary=req.bursary,
        category=req.category,
    )


def intent_from_payload(payload: dict[str, Any], query: str = "") -> Intent:
    raw_cat = payload.get("category") or "any"
    category = raw_cat if raw_cat in {"any", "crous", "distribution"} else "any"
    return Intent(
        query=query or str(payload.get("query") or ""),
        arrondissement=payload.get("arrondissement"),
        budget_eur=payload.get("budget_eur"),
        time_hhmm=payload.get("time_hhmm"),
        meal=payload.get("meal") or "lunch",
        diet=payload.get("diet") or "any",
        language=payload.get("language") or "en",
        bursary=bool(payload.get("bursary")),
        category=category,
    )


def place_to_out(place: RankedPlace) -> RankedPlaceOut:
    status = "fresh"
    if place.last_verified:
        try:
            verified = datetime.fromisoformat(place.last_verified).replace(tzinfo=timezone.utc)
            status = freshness_status(verified)
        except ValueError:
            status = "stale"
    return RankedPlaceOut(
        id=place.id,
        source=place.source,
        name=place.name,
        org=place.org,
        kind=place.kind,
        address=place.address,
        arrondissement=place.arrondissement,
        latitude=place.latitude,
        longitude=place.longitude,
        price_eur=place.price_eur,
        open_for_request=place.open_for_request,
        schedule_text=place.schedule_text,
        eligibility=place.eligibility,
        menu_text=place.menu_text,
        booking_required=place.booking_required,
        last_verified=place.last_verified,
        source_url=place.source_url,
        french_hint=place.french_hint,
        notes=place.notes,
        score=place.score,
        reasons=place.reasons,
        freshness_status=status,
        match=MatchRecordOut(**asdict(place.match)),
    )


def _mode_from_status(status: str) -> str:
    lowered = (status or "").lower()
    if "live" in lowered:
        return "live"
    if "stale" in lowered:
        return "stale"
    if "fallback" in lowered or "snapshot" in lowered:
        return "snapshot"
    return "cache"


def current_data_version(db: Session) -> str:
    hit = cache_get(DATAV_KEY, 60)
    if hit is not None:
        value, _age, _tier = hit
        if isinstance(value, str) and value:
            return value
    version = VenueRepository(db).data_version()
    cache_set(DATAV_KEY, version, 60)
    return version


def empty_reason_from_meta(meta: dict[str, Any], places: list[Any]) -> EmptyReasonOut | None:
    if places:
        return None
    pre = int(meta.get("pre_filter_candidate_count") or 0)
    dropped_budget = int(meta.get("dropped_by_budget") or 0)
    dropped_arr = int(meta.get("dropped_by_arrondissement") or 0)
    counts = {
        "pre_filter": pre,
        "dropped_by_budget": dropped_budget,
        "dropped_by_arrondissement": dropped_arr,
    }
    if pre == 0:
        return EmptyReasonOut(reason="no_data", blocking_chips=[], suggestion=None, counts=counts)
    chips: list[str] = []
    if dropped_budget:
        chips.append("budget")
    if dropped_arr:
        chips.append("arrondissement")
    if dropped_budget and dropped_arr:
        suggestion = "relax_both"
    elif dropped_budget:
        suggestion = "relax_budget"
    elif dropped_arr:
        suggestion = "relax_arrondissement"
    else:
        suggestion = "relax_both"
    return EmptyReasonOut(
        reason="filters_too_strict",
        blocking_chips=chips,  # type: ignore[arg-type]
        suggestion=suggestion,  # type: ignore[arg-type]
        counts=counts,
    )


def retrieve_places(
    db: Session,
    req: QueryRequest,
    *,
    llm: GroqLLM | None = None,
    parse_query: bool = True,
) -> dict[str, Any]:
    llm = llm or GroqLLM()
    intent = intent_from_request(req, llm, parse_query=parse_query)
    db_session: Session | None = db
    try:
        version = current_data_version(db)
    except SQLAlchemyError as exc:
        logger.warning("retrieve_db_version_failed", error=str(exc))
        db_session = None
        version = "snapshot"
    hashed = intent_hash(intent)
    cache_id = retr_key(version, hashed)
    if req.refresh:
        hit = None
    else:
        hit = cache_get(cache_id, RETR_HARD_TTL)
    if hit is not None:
        value, age, tier = hit
        if isinstance(value, dict) and "places" in value:
            value = dict(value)
            value["meta"] = {**(value.get("meta") or {}), "cache_tier": tier, "cache_age": int(age)}
            return value

    list_warm = cache_get(LIST_KEY, LIST_HARD_TTL) is not None
    menu_limit = WARM_MENU_LIMIT if list_warm else COLD_MENU_LIMIT
    if req.refresh:
        menu_limit = WARM_MENU_LIMIT
    places, meta = rank_places(
        intent,
        use_network=req.use_network,
        menu_limit=menu_limit,
        db_session=db_session,
        force_refresh=bool(req.refresh),
    )
    last_refresh = None
    if db_session is not None:
        try:
            last_refresh = VenueRepository(db).last_refresh()
        except SQLAlchemyError as exc:
            logger.warning("retrieve_db_last_refresh_failed", error=str(exc))
    crous_status = str(meta.get("crous_status") or "")
    offline_mode = crous_status.startswith("fallback")
    sources = [
        SourceMeta(name="CROUStillant", fetched_at=None, mode=_mode_from_status(crous_status)),  # type: ignore[arg-type]
        SourceMeta(
            name="distributions",
            fetched_at=str(meta.get("distributions_compiled") or ""),
            mode="cache",
        ),
    ]
    empty_reason = empty_reason_from_meta(meta, places)
    payload = {
        "intent": intent,
        "places": places,
        "meta": meta,
        "data_version": version,
        "generated_at": datetime.now(timezone.utc),
        "sources": sources,
        "refreshed_at": last_refresh.finished_at if last_refresh else None,
        "offline_mode": offline_mode,
        "intent_hash": hashed,
        "empty_reason": empty_reason,
    }
    serialisable = {
        **payload,
        "intent": intent.__dict__,
        "places": [place_to_out(p).model_dump() for p in places[:DISPLAY_LIMIT]],
        "sources": [s.model_dump() for s in sources],
        "generated_at": payload["generated_at"].isoformat(),
        "refreshed_at": payload["refreshed_at"].isoformat() if payload["refreshed_at"] else None,
        "empty_reason": empty_reason.model_dump() if empty_reason else None,
    }
    cache_set(cache_id, serialisable, RETR_HARD_TTL)
    return payload


def ranked_from_cached(rows: list[dict[str, Any]]) -> list[RankedPlace]:
    places: list[RankedPlace] = []
    for row in rows:
        places.append(
            RankedPlace(
                id=row["id"],
                source=row.get("source") or "",
                name=row.get("name") or "",
                org=row.get("org") or "",
                kind=row.get("kind") or "",
                address=row.get("address") or "",
                arrondissement=row.get("arrondissement"),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                price_eur=float(row.get("price_eur") or 0),
                open_for_request=bool(row.get("open_for_request")),
                schedule_text=row.get("schedule_text") or "",
                eligibility=row.get("eligibility") or "",
                menu_text=row.get("menu_text") or "",
                booking_required=bool(row.get("booking_required")),
                last_verified=row.get("last_verified") or "",
                source_url=row.get("source_url") or "",
                french_hint=row.get("french_hint") or "",
                notes=row.get("notes") or "",
                score=float(row.get("score") or 0),
                reasons=list(row.get("reasons") or []),
                match=MatchRecord(**(row.get("match") or {})),
            )
        )
    return places
