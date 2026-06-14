"""Smoke tests for significant-event CRUD + ownership against a live Postgres."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, Place, Session

pytestmark = pytest.mark.smoke


def _home(db) -> Place:
    p = Place(city="Berlin", country_code="DE", country_name="Germany", lat=52.52, lng=13.4)
    db.add(p)
    db.flush()
    return p


def _signin(db, email: str, with_home: bool = True) -> str:
    home = _home(db) if with_home else None
    member = Member(email=email, display_name=email.split("@")[0], home_place_id=home.id if home else None)
    db.add(member)
    db.flush()
    raw = generate_token()
    db.add(Session(member_id=member.id, token_hash=hash_token(raw), expires_at=datetime.now(UTC) + timedelta(days=1)))
    db.commit()
    return raw


def _client(raw: str) -> TestClient:
    client = TestClient(create_app())
    client.cookies.set("catchup_session", raw)
    return client


def _iso(days: int) -> str:
    return (datetime.now(UTC).date() + timedelta(days=days)).isoformat()


def _body(title="My birthday", start=None, end=None, note="cake") -> dict:
    return {"title": title, "start_date": start or _iso(10), "end_date": end or _iso(10), "note": note}


def test_create_event_at_home(db):
    client = _client(_signin(db, "a@example.com"))
    resp = client.post("/events", json=_body())
    assert resp.status_code == 201
    event = resp.json()["event"]
    assert event["title"] == "My birthday"
    assert event["place"]["city"] == "Berlin"  # anchored to home

    mine = client.get("/events/me").json()["events"]
    assert len(mine) == 1


def test_create_event_requires_home(db):
    client = _client(_signin(db, "nohome@example.com", with_home=False))
    resp = client.post("/events", json=_body())
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "no_home"


def test_edit_and_delete_own_event(db):
    client = _client(_signin(db, "a@example.com"))
    event_id = client.post("/events", json=_body()).json()["event"]["id"]
    edited = client.patch(f"/events/{event_id}", json={"title": "Housewarming"})
    assert edited.status_code == 200
    assert edited.json()["event"]["title"] == "Housewarming"
    assert client.delete(f"/events/{event_id}").status_code == 204
    assert client.get("/events/me").json()["events"] == []


def test_cannot_edit_or_delete_other_members_event(db):
    owner = _client(_signin(db, "owner@example.com"))
    event_id = owner.post("/events", json=_body()).json()["event"]["id"]
    intruder = _client(_signin(db, "intruder@example.com"))
    assert intruder.patch(f"/events/{event_id}", json={"title": "x"}).status_code == 403
    assert intruder.delete(f"/events/{event_id}").status_code == 403


def test_inverted_dates_rejected(db):
    client = _client(_signin(db, "a@example.com"))
    resp = client.post("/events", json=_body(start=_iso(10), end=_iso(5)))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_dates"


def test_list_all_excludes_past(db):
    client = _client(_signin(db, "a@example.com"))
    client.post("/events", json=_body(start=_iso(-10), end=_iso(-5)))  # past
    client.post("/events", json=_body(start=_iso(5), end=_iso(6)))  # upcoming
    events = client.get("/events").json()["events"]
    assert len(events) == 1
    assert events[0]["member"]["display_name"] == "a"


def test_member_detail_embeds_upcoming_events(db):
    raw = _signin(db, "a@example.com")
    client = _client(raw)
    me = client.get("/auth/me").json()["member"]
    client.post("/events", json=_body(title="Bday", start=_iso(5), end=_iso(5)))
    detail = client.get(f"/members/{me['id']}").json()["member"]
    assert [e["title"] for e in detail["events"]] == ["Bday"]


def test_unauthenticated_blocked(db):
    client = TestClient(create_app())
    assert client.get("/events").status_code == 401
    assert client.get("/events/me").status_code == 401
    assert client.post("/events", json=_body()).status_code == 401
