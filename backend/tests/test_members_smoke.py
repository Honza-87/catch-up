"""Smoke tests for profile editing against a live Postgres."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, Session

pytestmark = pytest.mark.smoke


def _signin(db, email: str) -> str:
    """Create a member + active session; return the raw session cookie value."""
    member = Member(email=email)
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
    return raw


def _client(raw: str) -> TestClient:
    client = TestClient(create_app())
    client.cookies.set("catchup_session", raw)
    return client


def test_update_profile_persists(db):
    client = _client(_signin(db, "m@example.com"))
    resp = client.patch(
        "/members/me",
        json={
            "display_name": "Maya",
            "job_title": "Engineer",
            "company": "Acme",
            "whatsapp_e164": "+420777123456",
            "home_place": {
                "city": "Lisbon",
                "country_code": "PT",
                "country_name": "Portugal",
                "lat": 38.72,
                "lng": -9.14,
            },
        },
    )
    assert resp.status_code == 200
    member = resp.json()["member"]
    assert member["display_name"] == "Maya"
    assert member["whatsapp_e164"] == "+420777123456"
    assert member["home_place"]["city"] == "Lisbon"


def test_invalid_whatsapp_rejected(db):
    client = _client(_signin(db, "m@example.com"))
    resp = client.patch("/members/me", json={"whatsapp_e164": "nope"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_whatsapp"


def test_patch_me_does_not_touch_other_member(db):
    raw1 = _signin(db, "one@example.com")
    _signin(db, "two@example.com")
    _client(raw1).patch("/members/me", json={"display_name": "One"})
    other = db.execute(select(Member).where(Member.email == "two@example.com")).scalar_one()
    assert other.display_name is None


def test_photo_rejects_non_image(db):
    client = _client(_signin(db, "m@example.com"))
    resp = client.post("/members/me/photo", files={"file": ("x.txt", b"hello", "text/plain")})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_image"
