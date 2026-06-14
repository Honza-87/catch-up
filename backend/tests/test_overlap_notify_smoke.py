"""Smoke tests for the overlap notify step (live Postgres, stub Notifier)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select

from catchup.models import Member, Overlap, Place, Trip
from catchup.notify.base import OverlapDigestItem
from catchup.overlaps.runner import notify_new, reconcile

pytestmark = pytest.mark.smoke

_PAST = date(2026, 1, 1)


class StubNotifier:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, str | None, list[OverlapDigestItem]]] = []
        self.fail = fail

    def send_login_link(self, email: str, link: str) -> None:  # pragma: no cover - unused here
        pass

    def send_overlap_digest(self, email: str, member_name: str | None, overlaps: list[OverlapDigestItem]) -> None:
        if self.fail:
            raise RuntimeError("send failed")
        self.calls.append((email, member_name, list(overlaps)))


def _place(db, city: str, cc: str, lat: float, lng: float) -> Place:
    p = Place(city=city, country_code=cc, country_name=city, lat=lat, lng=lng)
    db.add(p)
    db.flush()
    return p


def _member(db, email: str) -> Member:
    m = Member(email=email, display_name=email.split("@")[0])
    db.add(m)
    db.flush()
    return m


def _trip(db, member: Member, place: Place, start: date, end: date) -> Trip:
    t = Trip(member_id=member.id, place_id=place.id, start_date=start, end_date=end)
    db.add(t)
    db.flush()
    return t


def _strong_pair(db) -> tuple[Member, Member, Place]:
    lisbon = _place(db, "Lisbon", "PT", 38.72, -9.14)
    a = _member(db, "a@x.com")
    b = _member(db, "b@x.com")
    _trip(db, a, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    _trip(db, b, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    db.commit()
    return a, b, lisbon


def test_one_digest_per_member(db):
    _strong_pair(db)
    reconcile(db, today=_PAST)
    stub = StubNotifier()

    assert notify_new(db, stub) == 2  # one per affected member
    emails = sorted(c[0] for c in stub.calls)
    assert emails == ["a@x.com", "b@x.com"]
    assert all(len(c[2]) == 1 for c in stub.calls)

    row = db.execute(select(Overlap)).scalar_one()
    assert row.notified_at is not None


def test_no_realert_on_rerun(db):
    _strong_pair(db)
    reconcile(db, today=_PAST)
    notify_new(db, StubNotifier())

    second = StubNotifier()
    assert notify_new(db, second) == 0
    assert second.calls == []


def test_failed_send_leaves_unnotified_for_retry(db):
    _strong_pair(db)
    reconcile(db, today=_PAST)

    assert notify_new(db, StubNotifier(fail=True)) == 0
    row = db.execute(select(Overlap)).scalar_one()
    assert row.notified_at is None  # not stamped → retried next run

    retry = StubNotifier()
    assert notify_new(db, retry) == 2
    row = db.execute(select(Overlap)).scalar_one()
    assert row.notified_at is not None


def test_reappearance_realerts(db):
    a, b, lisbon = _strong_pair(db)
    reconcile(db, today=_PAST)
    notify_new(db, StubNotifier())

    # B's trip vanishes → overlap deleted on reconcile.
    t_b = db.execute(select(Trip).where(Trip.member_id == b.id)).scalar_one()
    db.delete(t_b)
    db.commit()
    reconcile(db, today=_PAST)
    assert db.execute(select(Overlap)).scalars().all() == []

    # Same overlap reappears → fresh NULL row → re-alert.
    _trip(db, b, lisbon, date(2026, 7, 1), date(2026, 7, 10))
    db.commit()
    reconcile(db, today=_PAST)
    fresh = StubNotifier()
    assert notify_new(db, fresh) == 2
