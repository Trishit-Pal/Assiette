"""Magic-link authentication for student emails."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db.session import get_db
from backend.models.orm import AuthToken, User
from backend.security import is_student_email
from backend.security.tokens import create_session_token, verify_session_token

__all__ = [
    "create_session_token",
    "request_magic_link",
    "verify_magic_link",
    "require_user",
    "optional_user",
]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def request_magic_link(db: Session, email: str) -> str | None:
    settings = get_settings()
    email = email.strip().lower()
    if not is_student_email(email, settings.student_domains):
        return None

    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        user = User(email=email, role="student")
        db.add(user)
        db.flush()

    raw_token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_token_ttl_minutes)
    db.add(
        AuthToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=expires,
        )
    )
    db.commit()

    if settings.resend_api_key or settings.smtp_host:
        _send_email(email, raw_token)
    return raw_token


def verify_magic_link(db: Session, token: str) -> User | None:
    now = datetime.now(timezone.utc)
    token_hash = _hash_token(token)
    row = db.scalars(select(AuthToken).where(AuthToken.token_hash == token_hash)).first()
    if row is None or row.used_at is not None:
        return None
    expires = row.expires_at.replace(tzinfo=timezone.utc) if row.expires_at.tzinfo is None else row.expires_at
    if expires < now:
        return None
    row.used_at = now
    db.commit()
    return db.get(User, row.user_id)


def _bearer(request: Request) -> str | None:
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _bearer(request)
    if not token:
        return None
    payload = verify_session_token(token)
    if payload is None:
        return None
    return db.get(User, payload["sub"])


def require_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    return user


def _send_email(email: str, token: str) -> None:
    import smtplib
    from email.message import EmailMessage

    from assiette.http import DEFAULT_TIMEOUT, get_session

    settings = get_settings()
    link = f"{settings.api_base_url.rstrip('/')}/signin?token={token}"
    body = (
        f"Click to sign in to Assiette (valid {settings.auth_token_ttl_minutes} min):\n\n{link}\n"
    )
    if settings.resend_api_key:
        get_session().post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
            json={"from": settings.mail_from, "to": [email], "subject": "Assiette login link", "text": body},
            timeout=DEFAULT_TIMEOUT,
        ).raise_for_status()
        return
    msg = EmailMessage()
    msg["Subject"] = "Assiette login link"
    msg["From"] = settings.mail_from
    msg["To"] = email
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_user:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
