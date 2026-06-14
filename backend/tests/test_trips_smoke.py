"""Smoke tests for trip CRUD + ownership against a live Postgres."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, Session

pytestmark = pytest.mark.smoke

_LISBON = {"city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 38.72, "lng": -9.14}
_PORTO = {"city": "Porto", "country_code": "PT", "country_name": "Portugal", "lat": 41.15, "lng": -8.61}


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


def _trip_body(place=_LISBON, start="2026-07-01", end="2026-07-10", note="conference") -> dict:
    return {"place": place, "start_date": start, "end_date": end, "note": note}


def test_create_then_list_own_trip(db):
    client = _client(_signin(db, "a@example.com"))
    resp = client.post("/trips", json=_trip_body())
    assert resp.status_code == 201
    trip = resp.json()["trip"]
    assert trip["place"]["city"] == "Lisbon"
    assert trip["start_date"] == "2026-07-01"

    mine = client.get("/trips/me").json()["trips"]
    assert len(mine) == 1
    assert mine[0]["id"] == trip["id"]


def test_edit_own_trip(db):
    client = _client(_signin(db, "a@example.com"))
    trip_id = client.post("/trips", json=_trip_body()).json()["trip"]["id"]
    resp = client.patch(f"/trips/{trip_id}", json={"place": _PORTO, "note": "moved"})
    assert resp.status_code == 200
    trip = resp.json()["trip"]
    assert trip["place"]["city"] == "Porto"
    assert trip["note"] == "moved"


def test_delete_own_trip(db):
    client = _client(_signin(db, "a@example.com"))
    trip_id = client.post("/trips", json=_trip_body()).json()["trip"]["id"]
    assert client.delete(f"/trips/{trip_id}").status_code == 204
    assert client.get("/trips/me").json()["trips"] == []


def test_cannot_edit_other_members_trip(db):
    owner = _client(_signin(db, "owner@example.com"))
    trip_id = owner.post("/trips", json=_trip_body()).json()["trip"]["id"]
    intruder = _client(_signin(db, "intruder@example.com"))
    resp = intruder.patch(f"/trips/{trip_id}", json={"note": "hijack"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_cannot_delete_other_members_trip(db):
    owner = _client(_signin(db, "owner@example.com"))
    trip_id = owner.post("/trips", json=_trip_body()).json()["trip"]["id"]
    intruder = _client(_signin(db, "intruder@example.com"))
    assert intruder.delete(f"/trips/{trip_id}").status_code == 403


def test_inverted_dates_rejected(db):
    client = _client(_signin(db, "a@example.com"))
    resp = client.post("/trips", json=_trip_body(start="2026-07-10", end="2026-07-01"))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_dates"


def test_place_dedup_reuses_row(db):
    client = _client(_signin(db, "a@example.com"))
    client.post("/trips", json=_trip_body(start="2026-07-01", end="2026-07-05"))
    client.post("/trips", json=_trip_body(start="2026-08-01", end="2026-08-05"))
    from sqlalchemy import func, select

    from catchup.models import Place

    count = db.execute(select(func.count()).select_from(Place).where(Place.city == "Lisbon")).scalar_one()
    assert count == 1


def test_manual_place_snaps_to_geocoded_row(db):
    client = _client(_signin(db, "a@example.com"))
    # Geocoded Lisbon, then a manual Lisbon (sentinel 0,0 coords, FR-007).
    client.post("/trips", json=_trip_body(start="2026-07-01", end="2026-07-05"))
    manual = {"city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 0, "lng": 0}
    resp = client.post("/trips", json=_trip_body(place=manual, start="2026-08-01", end="2026-08-05"))
    assert resp.status_code == 201
    # Reuses the geocoded row (real coords), so overlaps + map pins stay correct.
    assert resp.json()["trip"]["place"]["lat"] == 38.72

    from sqlalchemy import func, select

    from catchup.models import Place

    count = db.execute(select(func.count()).select_from(Place).where(Place.city == "Lisbon")).scalar_one()
    assert count == 1


def test_unauthenticated_blocked(db):
    client = TestClient(create_app())
    assert client.get("/trips/me").status_code == 401
    assert client.post("/trips", json=_trip_body()).status_code == 401
    assert client.patch("/trips/00000000-0000-0000-0000-000000000000", json={"note": "x"}).status_code == 401
    assert client.delete("/trips/00000000-0000-0000-0000-000000000000").status_code == 401
