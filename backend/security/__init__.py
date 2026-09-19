"""Security utilities: validation, sanitisation, rate limiting helpers."""

from __future__ import annotations

import html
import re
from typing import Any

from fastapi import Request

from backend.config import get_settings

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"system\s*:", re.I),
    re.compile(r"<\s*script", re.I),
]


def sanitise_for_llm(text: str, max_len: int = 500) -> str:
    """Strip HTML and obvious injection patterns before LLM context."""
    if not text:
        return ""
    clean = html.unescape(re.sub(r"<[^>]+>", " ", text))
    clean = re.sub(r"\s+", " ", clean).strip()
    for pattern in _INJECTION_PATTERNS:
        clean = pattern.sub("[filtered]", clean)
    return clean[:max_len]


def sanitise_context_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return structured rows with text fields sanitised."""
    text_keys = {
        "name",
        "org",
        "address",
        "eligibility",
        "menu_or_notes",
        "notes",
        "french_hint",
        "schedule",
        "why",
        "dietary_note",
        "summary",
        "title",
    }
    cleaned = []
    for row in rows:
        item = dict(row)
        for key in text_keys:
            if key in item and isinstance(item[key], str):
                item[key] = sanitise_for_llm(item[key])
        if "french_phrases" in item and isinstance(item["french_phrases"], list):
            item["french_phrases"] = [sanitise_for_llm(p, 200) for p in item["french_phrases"]]
        if "caveats" in item and isinstance(item["caveats"], list):
            item["caveats"] = [sanitise_for_llm(c, 300) for c in item["caveats"] if isinstance(c, str)]
        cleaned.append(item)
    return cleaned


def is_student_email(email: str, allowed_domains: list[str]) -> bool:
    email = email.strip().lower()
    if "@" not in email:
        return False
    domain = email.split("@", 1)[1]
    return any(domain == d or domain.endswith("." + d) for d in allowed_domains)


def client_ip(request: Request) -> str:
    """Rightmost-trusted X-Forwarded-For hop, then the socket peer."""
    settings = get_settings()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            trusted = max(1, settings.trusted_proxy_count)
            if len(parts) >= trusted:
                return parts[-trusted]
            return parts[0]
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
