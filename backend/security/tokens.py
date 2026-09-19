"""Signed, expiring session tokens."""

from __future__ import annotations

from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.config import get_settings
from backend.models.orm import User

_SALT = "assiette-session-v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt=_SALT)


def create_session_token(user: User) -> str:
    return _serializer().dumps({"sub": user.id, "email": user.email, "kid": "v1"})


def verify_session_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    max_age = settings.session_ttl_days * 24 * 60 * 60
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict) or "sub" not in payload or "email" not in payload:
        return None
    return payload
