"""Token generation and keyed hashing, shared by magic links and sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from catchup.config import get_settings


def generate_token() -> str:
    """Return a high-entropy URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """Return a keyed (HMAC-SHA256) hash of a raw token for storage at rest."""
    secret = get_settings().session_secret.encode("utf-8")
    return hmac.new(secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()
