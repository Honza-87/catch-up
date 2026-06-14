"""Smoke tests for the member directory against a live Postgres."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, RosterInvite, Session

pytestmark = pytest.mark.smoke


def _signin(db, email: str) -> tuple[str, str]:
    member = Member(email=email, display_name=email.split("@")[0])
    db.add(member)
    db.flush()
    raw = generate_token()
    db.add(
        Session(
            member_id=member.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    db.commit()
    return str(member.id), raw


def _client(raw: str) -> TestClient:
    client = TestClient(create_app())
    client.cookies.set("catchup_session", raw)
    return client


def test_directory_lists_only_joined_members(db):
    _, raw = _signin(db, "a@example.com")
    _signin(db, "b@example.com")
    db.add(RosterInvite(email="never@example.com"))  # invited but never signed in
    db.commit()

    resp = _client(raw).get("/members")
    assert resp.status_code == 200
    assert len(resp.json()["members"]) == 2


def test_member_detail_returns_profile(db):
    _, raw = _signin(db, "a@example.com")
    other_id, _ = _signin(db, "b@example.com")

    resp = _client(raw).get(f"/members/{other_id}")
    assert resp.status_code == 200
    assert resp.json()["member"]["email"] == "b@example.com"


def test_member_detail_unknown_id_404(db):
    _, raw = _signin(db, "a@example.com")
    resp = _client(raw).get("/members/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_directory_requires_auth(db):
    resp = TestClient(create_app()).get("/members")
    assert resp.status_code == 401
