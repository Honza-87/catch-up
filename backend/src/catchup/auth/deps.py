"""FastAPI dependency resolving the current member from the session cookie."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.auth.security import hash_token
from catchup.config import get_settings
from catchup.db import get_session
from catchup.errors import AppError
from catchup.models import Member, Session


def get_current_member(request: Request, db: DbSession = Depends(get_session)) -> Member:
    """Return the authenticated Member, or raise 401."""
    settings = get_settings()
    raw = request.cookies.get(settings.cookie_name)
    if not raw:
        raise AppError("unauthenticated", "Sign-in required.", status_code=401)

    row = db.execute(select(Session).where(Session.token_hash == hash_token(raw))).scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise AppError("unauthenticated", "Sign-in required.", status_code=401)

    member = db.get(Member, row.member_id)
    if member is None:
        raise AppError("unauthenticated", "Sign-in required.", status_code=401)
    return member
