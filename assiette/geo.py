"""Arrondissement helpers and distance — no network."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Literal

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
WEEKDAYS_FR = {
    "lundi": "Monday",
    "mardi": "Tuesday",
    "mercredi": "Wednesday",
    "jeudi": "Thursday",
    "vendredi": "Friday",
    "samedi": "Saturday",
    "dimanche": "Sunday",
}

# Rough adjacency for intra-Paris walking/metro recommendations.
ADJACENT: dict[int, set[int]] = {
    1: {2, 3, 4, 7, 8},
    2: {1, 3, 8, 9, 10},
    3: {1, 2, 4, 10, 11},
    4: {1, 3, 11, 12},
    5: {4, 6, 12, 13, 14},
    6: {5, 7, 14, 15},
    7: {1, 6, 8, 15, 16},
    8: {1, 2, 7, 9, 16, 17},
    9: {2, 8, 10, 17, 18},
    10: {2, 3, 9, 11, 18, 19},
    11: {3, 4, 10, 12, 19, 20},
    12: {4, 5, 11, 13, 20},
    13: {5, 12, 14},
    14: {5, 6, 13, 15},
    15: {6, 7, 14, 16},
    16: {7, 8, 15, 17},
    17: {8, 9, 16, 18},
    18: {9, 10, 17, 19},
    19: {10, 11, 18, 20},
    20: {11, 12, 19},
}

POSTAL_RE = re.compile(r"75(\d{3})\b")
ZONE_RE = re.compile(r"Paris\s*0?(\d{1,2})", re.I)
ORDINAL_RE = re.compile(
    r"\b(\d{1,2})\s*(?:e|ème|eme|th|st|nd|rd|arr(?:ondissement)?)\b",
    re.I,
)


def arrondissement_from_postal(text: str | None) -> int | None:
    if not text:
        return None
    match = POSTAL_RE.search(text)
    if not match:
        return None
    arr = int(match.group(1))
    if 1 <= arr <= 20:
        return arr
    return None


def arrondissement_from_zone(zone: str | None) -> int | None:
    if not zone:
        return None
    if zone.strip().lower() in {"centre", "paris centre"}:
        return 1
    match = ZONE_RE.search(zone)
    if match:
        arr = int(match.group(1))
        return arr if 1 <= arr <= 20 else None
    return arrondissement_from_postal(zone)


def arrondissement_from_query(text: str) -> int | None:
    postal = arrondissement_from_postal(text)
    if postal:
        return postal
    match = ORDINAL_RE.search(text)
    if match:
        arr = int(match.group(1))
        return arr if 1 <= arr <= 20 else None
    return None


def postal_code_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = POSTAL_RE.search(text)
    if not match:
        return None
    return f"75{match.group(1)}"


ArrondissementTier = Literal["exact", "nearby", "out_of_range", "unscoped"]


def arrondissement_tier(place_arr: int | None, query_arr: int | None) -> ArrondissementTier:
    if query_arr is None:
        return "unscoped"
    if place_arr is None:
        return "out_of_range"
    if place_arr == query_arr:
        return "exact"
    if place_arr in ADJACENT.get(query_arr, set()):
        return "nearby"
    return "out_of_range"


def proximity_score(place_arr: int | None, query_arr: int | None) -> tuple[int, str]:
    tier = arrondissement_tier(place_arr, query_arr)
    if tier == "unscoped":
        return 8, "Paris (area unspecified)"
    if tier == "exact":
        return 40, f"same arrondissement ({query_arr}e)"
    if tier == "nearby":
        return 22, f"next to the {query_arr}e ({place_arr}e)"
    if place_arr is None:
        return 0, "Paris (area unspecified)"
    return 0, f"further ({place_arr}e vs {query_arr}e)"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_hhmm(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d{1,2})[:hH](\d{2})?", value.strip())
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def meal_from_minutes(minutes: int | None, explicit: str | None = None) -> str:
    if explicit in {"breakfast", "lunch", "dinner", "any"}:
        return explicit
    if minutes is None:
        return "lunch"
    if minutes < 11 * 60:
        return "breakfast"
    if minutes < 15 * 60:
        return "lunch"
    return "dinner"


def meal_to_crous_slot(meal: str) -> str:
    return {"breakfast": "matin", "lunch": "midi", "dinner": "soir"}.get(meal, "midi")


def weekday_name(when: datetime | None = None) -> str:
    when = when or datetime.now()
    return WEEKDAYS[when.weekday()]


def hhmm_in_window(hhmm: str | None, start: str, end: str) -> bool:
    t = parse_hhmm(hhmm)
    a = parse_hhmm(start)
    b = parse_hhmm(end)
    if t is None or a is None or b is None:
        return True
    if a <= b:
        return a <= t <= b
    return t >= a or t <= b
