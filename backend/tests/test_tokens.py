"""Unit tests for pure magic-link token helpers (no DB)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from catchup.auth.security import hash_token
from catchup.auth.service import canonical_email
from catchup.auth.tokens import issue_login_token, token_is_usable


def test_canonical_email_maps_googlemail_to_gmail():
    assert canonical_email("Foo.Bar@googlemail.com") == "foo.bar@gmail.com"
    assert canonical_email("foo@gmail.com") == "foo@gmail.com"


def test_canonical_email_leaves_other_domains():
    assert canonical_email("Someone@Example.COM") == "someone@example.com"
    assert canonical_email("a@posteo.de") == "a@posteo.de"


def test_issue_login_token_hash_matches_raw():
    issued = issue_login_token(ttl_minutes=15)
    assert issued.token_hash == hash_token(issued.raw)
    assert issued.raw  # non-empty


def test_issue_login_token_expiry_window():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
    issued = issue_login_token(ttl_minutes=15, now=now)
    assert issued.expires_at == now + timedelta(minutes=15)


def test_issue_login_token_is_unique():
    a = issue_login_token(ttl_minutes=15)
    b = issue_login_token(ttl_minutes=15)
    assert a.raw != b.raw
    assert a.token_hash != b.token_hash


def test_token_is_usable_fresh():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
    assert token_is_usable(used_at=None, expires_at=now + timedelta(minutes=5), now=now) is True


def test_token_is_usable_rejects_used():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
    assert token_is_usable(used_at=now, expires_at=now + timedelta(minutes=5), now=now) is False


def test_token_is_usable_rejects_expired():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
    assert token_is_usable(used_at=None, expires_at=now - timedelta(minutes=1), now=now) is False
