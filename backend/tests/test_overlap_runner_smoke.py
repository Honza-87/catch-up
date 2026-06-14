"""Smoke tests for the overlap runner reconcile + GET /overlaps/me (live Postgres)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from catchup.app import create_app
from catchup.auth.security import generate_token, hash_token
from catchup.models import Member, Overlap, Place, Session, Trip
from catchup.overlaps.runner import reconcile

pytestmark = pytest.mark.smoke

_PAST = date(2026, 1, 1)  # a "today" earlier than the July fixtures → no clamping


def _place(db, city: str, cc: str, lat: float, lng: float) -> Place:
    p = Place(city=city, country_code=cc, country_name=city, lat=lat, lng=lng)
    db.add(p)
    db.flush()
    return p


def _member(db, email: str, home: Place | None = None) -> Member:
    m = Member(email=email, display_name=email.split("@")[0], home_place_id=home.id if home else None)
    db.add(m)
    db.flush()
    return m


def _trip(db, member: Member, place: Place, start: date, end: date) -> Trip:
    t = Trip(member_id=member.id, place_id=place.id, start_date=start, end_date=end)
    db.add(t)
    db.flush()
    return t


def _session(db, member: Member) -> str:
    raw = generate_token()
    db.add(Session(member_id=member.id, token_hash=hash_token(raw), expires_at=datetime.now(UTC) + timedelta(days=1)))
    db.commit()
    return raw


def test_reconcile_inserts_strong_trip_trip(db):
    lisbon = _place(db, "Lisbon", "PT", 38.72, -9.14)
    a = _member(db, "a@x.com")
    b = _member(db, "b@x.com")
    _trip(db, a, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    _trip(db, b, lisbon, date(2026, 7, 5), date(2026, 7, 15))
    db.commit()

    assert reconcile(db, today=_PAST) == 1
    rows = db.execute(select(Overlap)).scalars().all()
    assert len(rows) == 1
    assert rows[0].strength == "strong"
    assert rows[0].kind == "trip-trip"
    assert rows[0].notified_at is None
    assert (rows[0].start_date, rows[0].end_date) == (date(2026, 7, 5), date(2026, 7, 10))


def test_reconcile_deletes_vanished(db):
    lisbon = _place(db, "Lisbon", "PT", 38.72, -9.14)
    a = _member(db, "a@x.com")
    b = _member(db, "b@x.com")
    _trip(db, a, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    t_b = _trip(db, b, lisbon, date(2026, 7, 5), date(2026, 7, 15))
    db.commit()
    reconcile(db, today=_PAST)
    assert db.execute(select(Overlap)).scalars().all()

    db.delete(t_b)
    db.commit()
    reconcile(db, today=_PAST)
    assert db.execute(select(Overlap)).scalars().all() == []


def test_reconcile_updates_dates_keeps_notified_at(db):
    lisbon = _place(db, "Lisbon", "PT", 38.72, -9.14)
    a = _member(db, "a@x.com")
    b = _member(db, "b@x.com")
    _trip(db, a, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    t_b = _trip(db, b, lisbon, date(2026, 7, 5), date(2026, 7, 15))
    db.commit()
    reconcile(db, today=_PAST)

    row = db.execute(select(Overlap)).scalar_one()
    stamped = datetime.now(UTC)
    row.notified_at = stamped
    db.commit()

    # Shift B's trip → matched interval changes, but identity (same place) is stable.
    t_b.start_date = date(2026, 7, 8)
    db.commit()
    assert reconcile(db, today=_PAST) == 0  # not a new insert

    row = db.execute(select(Overlap)).scalar_one()
    assert row.start_date == date(2026, 7, 8)
    assert row.notified_at is not None  # preserved across the date shift


def test_get_overlaps_me_strong_first_and_resolves_other(db):
    lisbon = _place(db, "Lisbon", "PT", 38.72, -9.14)
    porto = _place(db, "Porto", "PT", 41.15, -8.61)
    a = _member(db, "a@x.com")
    b = _member(db, "b@x.com")
    c = _member(db, "c@x.com")
    # a & b strong (same city); a & c medium (same country, diff city)
    _trip(db, a, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    _trip(db, b, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    _trip(db, c, porto, date(2026, 7, 1), date(2026, 7, 10))
    raw = _session(db, a)
    reconcile(db, today=_PAST)
    db.commit()

    client = TestClient(create_app())
    client.cookies.set("catchup_session", raw)
    overlaps = client.get("/overlaps/me").json()["overlaps"]
    assert [o["strength"] for o in overlaps] == ["strong", "medium"]
    assert overlaps[0]["other_member"]["display_name"] == "b"
    assert overlaps[0]["place"]["city"] == "Lisbon"
    assert overlaps[1]["place"] is None


def test_get_overlaps_me_unauthenticated_blocked(db):
    assert TestClient(create_app()).get("/overlaps/me").status_code == 401
