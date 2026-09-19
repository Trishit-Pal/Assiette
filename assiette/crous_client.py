"""CROUStillant client for Paris university restaurants.

Uses the layered cache (L1/L2) with a JSON snapshot fallback. Falls back to
data/fallback_restaurants.json when the network and cache both miss.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from assiette.cache import (
    LIST_HARD_TTL,
    LIST_KEY,
    LIST_SOFT_TTL,
    MENU404_TTL,
    MENU_HARD_TTL,
    MENU_SOFT_TTL,
    begin_revalidate,
    cache_get,
    cache_set,
    end_revalidate,
    menu404_key,
    menu_key,
)
from assiette.circuit import allow_request, record_failure, record_success
from assiette.geo import arrondissement_from_postal, arrondissement_from_zone
from assiette.http import LIST_TIMEOUT, MENU_TIMEOUT, USER_AGENT, get_session
from assiette.paths import FALLBACK_RESTAURANTS_PATH

log = logging.getLogger(__name__)

BASE_URL = "https://api.croustillant.menu"
PARIS_REGION_CODE = 22
CROUS_STUDENT_PRICE = 3.30
CROUS_BURSARY_PRICE = 1.00
SERVICE = "crous"


def _fallback_list() -> tuple[list[dict], str]:
    fallback = json.loads(FALLBACK_RESTAURANTS_PATH.read_text(encoding="utf-8"))
    fetched = fallback.get("fetched_at") or "2026-09-03"
    return fallback.get("data") or [], f"fallback snapshot {fetched[:10]}"


def _seconds_until_4am() -> int:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
    if now.hour < 4:
        tomorrow = now.replace(hour=4, minute=0, second=0, microsecond=0)
    return max(60, int((tomorrow - now).total_seconds()))


class CrousClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or get_session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def _get(self, path: str, timeout: tuple[int | float, int | float]) -> Any:
        url = f"{BASE_URL}{path}"
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and payload.get("success") is False:
            raise RuntimeError(f"CROUStillant error for {path}")
        return payload

    def _fetch_list(self) -> tuple[list[dict], str]:
        if not allow_request(SERVICE):
            return _fallback_list()
        try:
            payload = self._get(f"/v1/regions/{PARIS_REGION_CODE}/restaurants", LIST_TIMEOUT)
            rows = payload.get("data") or []
            record_success(SERVICE)
            return rows, "CROUStillant live"
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            record_failure(SERVICE)
            log.warning("CROUStillant list failed: %s", exc)
            raise

    def list_paris_restaurants(self, use_network: bool = True, force: bool = False) -> tuple[list[dict], str]:
        if force and use_network:
            try:
                rows, status = self._fetch_list()
                cache_set(
                    LIST_KEY,
                    {"data": rows, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                    LIST_HARD_TTL,
                )
                return rows, status
            except (requests.RequestException, ValueError, RuntimeError):
                pass

        hit = cache_get(LIST_KEY, LIST_HARD_TTL)
        if hit is not None:
            value, age, tier = hit
            rows = value.get("data") if isinstance(value, dict) else value
            stale = age > LIST_SOFT_TTL
            status = "CROUStillant cache"
            if stale:
                status = "cache stale"
                if use_network and begin_revalidate(LIST_KEY):
                    try:
                        fresh_rows, live_status = self._fetch_list()
                        cache_set(
                            LIST_KEY,
                            {"data": fresh_rows, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                            LIST_HARD_TTL,
                        )
                        return fresh_rows, live_status
                    except (requests.RequestException, ValueError, RuntimeError):
                        pass
                    finally:
                        end_revalidate(LIST_KEY)
            return rows or [], f"{status} ({tier})"

        if use_network:
            try:
                rows, status = self._fetch_list()
                cache_set(
                    LIST_KEY,
                    {"data": rows, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                    LIST_HARD_TTL,
                )
                return rows, status
            except (requests.RequestException, ValueError, RuntimeError):
                pass

        rows, status = _fallback_list()
        return rows, status

    def menu_for(
        self, code: int, date: datetime | None = None, use_network: bool = True, force: bool = False
    ) -> tuple[dict | None, str]:
        date = date or datetime.now()
        stamp = date.strftime("%d-%m-%Y")
        key = menu_key(code, stamp)
        neg = menu404_key(code, stamp)

        if force and use_network:
            if not allow_request(SERVICE):
                hit = cache_get(key, MENU_HARD_TTL)
                if hit is not None:
                    value, _age, _tier = hit
                    return value, "menu cache"
                return None, "menu unavailable (circuit open)"
            try:
                return self._fetch_menu(code, stamp, key)
            except requests.HTTPError as exc:
                status_code = getattr(exc.response, "status_code", None)
                if status_code == 404:
                    cache_set(neg, True, MENU404_TTL)
                    return None, "no menu published for this date"
                record_failure(SERVICE)
                log.warning("CROUStillant menu %s failed: %s", code, exc)
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                record_failure(SERVICE)
                log.warning("CROUStillant menu %s failed: %s", code, exc)
            hit = cache_get(key, MENU_HARD_TTL)
            if hit is not None:
                value, _age, _tier = hit
                return value, "menu cache"
            return None, "menu unavailable"

        negative = cache_get(neg, MENU404_TTL)
        if negative is not None:
            return None, "no menu published for this date"

        hit = cache_get(key, MENU_HARD_TTL)
        if hit is not None:
            value, age, _tier = hit
            status = "menu cache" if age <= MENU_SOFT_TTL else "cache stale"
            if age > MENU_SOFT_TTL and use_network and begin_revalidate(key):
                try:
                    return self._fetch_menu(code, stamp, key)
                except (requests.RequestException, ValueError, RuntimeError):
                    return value, status
                finally:
                    end_revalidate(key)
            return value, status

        if not use_network:
            return None, "menu skipped"
        if not allow_request(SERVICE):
            return None, "menu unavailable (circuit open)"
        try:
            return self._fetch_menu(code, stamp, key)
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code == 404:
                cache_set(neg, True, MENU404_TTL)
                return None, "no menu published for this date"
            record_failure(SERVICE)
            log.warning("CROUStillant menu %s failed: %s", code, exc)
            return None, f"menu unavailable ({exc.__class__.__name__})"
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            record_failure(SERVICE)
            log.warning("CROUStillant menu %s failed: %s", code, exc)
            return None, f"menu unavailable ({exc.__class__.__name__})"

    def _fetch_menu(self, code: int, stamp: str, key: str) -> tuple[dict | None, str]:
        payload = self._get(f"/v1/restaurants/{code}/menu/{stamp}", MENU_TIMEOUT)
        record_success(SERVICE)
        ttl = min(MENU_HARD_TTL, _seconds_until_4am())
        cache_set(key, payload, ttl)
        return payload, "CROUStillant live"


def flatten_menu(payload: dict | None, meal_slot: str | None = None) -> str:
    if not payload:
        return ""
    days = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(days, dict):
        days = [days]
    if not isinstance(days, list) or not days:
        return ""
    day = days[0]
    if not isinstance(day, dict):
        return ""
    parts: list[str] = []
    for repas in day.get("repas") or []:
        slot = repas.get("type")
        if meal_slot and slot != meal_slot:
            continue
        for category in repas.get("categories") or []:
            dishes = [p.get("libelle") for p in category.get("plats") or [] if p.get("libelle")]
            if dishes:
                parts.append(f"{category.get('libelle')}: " + ", ".join(dishes[:8]))
    return " | ".join(parts)[:1200]


def normalize_restaurant(raw: dict) -> dict:
    address = raw.get("adresse") or ""
    zone = raw.get("zone") or ""
    arr = arrondissement_from_postal(address) or arrondissement_from_zone(zone)
    hours = raw.get("horaires") or ""
    if isinstance(hours, str) and hours.startswith("["):
        try:
            hours = " · ".join(json.loads(hours))
        except json.JSONDecodeError:
            pass
    return {
        "id": f"crous-{raw.get('code')}",
        "source": "crous",
        "code": raw.get("code"),
        "name": raw.get("nom") or "CROUS",
        "kind": (raw.get("type") or {}).get("libelle") or "Restaurant",
        "address": address,
        "arrondissement": arr,
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "price_eur": CROUS_STUDENT_PRICE,
        "ouvert": bool(raw.get("ouvert")),
        "jours_ouvert": raw.get("jours_ouvert") or [],
        "hours_text": hours if isinstance(hours, str) else str(hours),
        "zone": zone,
        "eligibility": "Student social tariff typically €3.30 (often €1 if boursier). Student proof / CROUS card usually required.",
        "booking_required": False,
        "source_url": f"{BASE_URL}/v1/restaurants/{raw.get('code')}",
        "last_verified": datetime.now().date().isoformat(),
        "french_hint": "Bonjour, le repas à tarif étudiant, s'il vous plaît.",
        "raw": raw,
    }


def crous_open_for_meal(normalized: dict, weekday: str, meal: str) -> bool:
    weekday_fr = {
        "Monday": "Lundi",
        "Tuesday": "Mardi",
        "Wednesday": "Mercredi",
        "Thursday": "Jeudi",
        "Friday": "Vendredi",
        "Saturday": "Samedi",
        "Sunday": "Dimanche",
    }[weekday]
    slots = ("matin", "midi", "soir") if meal == "any" else ({"breakfast": "matin", "lunch": "midi", "dinner": "soir"}[meal],)
    for row in normalized.get("jours_ouvert") or []:
        if (row.get("jour") or "").lower() != weekday_fr.lower():
            continue
        opening = row.get("ouverture") or {}
        return any(bool(opening.get(slot)) for slot in slots)
    return False
