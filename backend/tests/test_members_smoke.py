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


class _StubStore:
    """Stand-in PhotoStore: never touches a real bucket."""

    def get(self, key: str) -> tuple[bytes, str]:
        return b"\x89PNG-bytes", "image/png"

    def put(self, key: str, data: bytes, content_type: str) -> None:  # pragma: no cover - unused
        pass

    def delete(self, key: str) -> None:  # pragma: no cover - unused
        pass


def _member_by_email(db, email: str) -> Member:
    return db.execute(select(Member).where(Member.email == email)).scalar_one()


def test_avatar_streams_for_authed_member(db, monkeypatch):
    raw = _signin(db, "pic@example.com")
    member = _member_by_email(db, "pic@example.com")
    member.photo_key = f"members/{member.id}/avatar-abc.png"
    db.commit()
    monkeypatch.setattr("catchup.api.members.get_photo_store", lambda *_: _StubStore())

    resp = _client(raw).get(f"/members/{member.id}/avatar")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == b"\x89PNG-bytes"
    assert resp.headers["cache-control"] == "private, max-age=3600"


def test_avatar_404_when_no_photo(db):
    raw = _signin(db, "nopic@example.com")
    member = _member_by_email(db, "nopic@example.com")
    resp = _client(raw).get(f"/members/{member.id}/avatar")
    assert resp.status_code == 404


def test_avatar_requires_auth(db):
    _signin(db, "pic2@example.com")
    member = _member_by_email(db, "pic2@example.com")
    resp = TestClient(create_app()).get(f"/members/{member.id}/avatar")  # no cookie
    assert resp.status_code == 401


def test_photo_url_is_authed_proxy_path(db):
    raw = _signin(db, "url@example.com")
    member = _member_by_email(db, "url@example.com")
    member.photo_key = "members/x/avatar-y.png"
    db.commit()
    resp = _client(raw).get(f"/members/{member.id}")
    assert resp.json()["member"]["photo_url"].startswith(f"/api/members/{member.id}/avatar?v=")
