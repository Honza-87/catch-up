"""Pure magic-link token helpers (no DB, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from catchup.auth.security import generate_token, hash_token


@dataclass(frozen=True)
class IssuedToken:
    raw: str
    token_hash: str
    expires_at: datetime


def issue_login_token(ttl_minutes: int, now: datetime | None = None) -> IssuedToken:
    """Create a fresh single-use token: raw value, its stored hash, and expiry."""
    now = now or datetime.now(UTC)
    raw = generate_token()
    return IssuedToken(raw=raw, token_hash=hash_token(raw), expires_at=now + timedelta(minutes=ttl_minutes))


def token_is_usable(used_at: datetime | None, expires_at: datetime, now: datetime | None = None) -> bool:
    """A token is usable iff it has not been used and has not expired."""
    now = now or datetime.now(UTC)
    return used_at is None and expires_at > now
