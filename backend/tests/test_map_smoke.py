"""Smoke tests for the map surfaces: GET /trips + trips embedded in MemberDetail."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, Session

pytestmark = pytest.mark.smoke

_LISBON = {"city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 38.72, "lng": -9.14}


def _signin(db, email: str) -> str:
    member = Member(email=email)
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


def test_list_all_excludes_past_and_sorts(db):
    client = _client(_signin(db, "a@example.com"))
    # Past trip (ended yesterday) — must be excluded.
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(-10), "end_date": _iso(-1), "note": None})
    # Two future trips out of order — must come back sorted by start_date.
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(30), "end_date": _iso(35), "note": None})
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(5), "end_date": _iso(9), "note": None})

    trips = client.get("/trips").json()["trips"]
    assert len(trips) == 2
    assert trips[0]["start_date"] == _iso(5)
    assert trips[1]["start_date"] == _iso(30)
    assert trips[0]["member"]["display_name"] is None  # embedded member identity present


def test_in_progress_trip_counts_as_upcoming(db):
    client = _client(_signin(db, "a@example.com"))
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(-2), "end_date": _iso(2), "note": None})
    assert len(client.get("/trips").json()["trips"]) == 1


def test_member_detail_embeds_upcoming_trips(db):
    raw = _signin(db, "a@example.com")
    client = _client(raw)
    me = client.get("/auth/me").json()["member"]
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(5), "end_date": _iso(9), "note": "x"})
    client.post("/trips", json={"place": _LISBON, "start_date": _iso(-9), "end_date": _iso(-5), "note": "old"})

    detail = client.get(f"/members/{me['id']}").json()["member"]
    assert [t["note"] for t in detail["trips"]] == ["x"]  # only upcoming embedded


def test_list_all_unauthenticated_blocked(db):
    assert TestClient(create_app()).get("/trips").status_code == 401
