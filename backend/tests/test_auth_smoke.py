"""Smoke tests for magic-link auth against a live Postgres."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from catchup.app import create_app
from catchup.auth import service
from catchup.config import get_settings
from catchup.errors import AppError
from catchup.models import Member, RosterInvite, Session, SigninToken

pytestmark = pytest.mark.smoke


class CapturingNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_login_link(self, email: str, link: str) -> None:
        self.sent.append((email, link))


def _token_from_link(link: str) -> str:
    return link.split("token=")[1]


def test_request_link_skips_non_roster(db):
    notifier = CapturingNotifier()
    service.request_link(db, "stranger@example.com", notifier, get_settings())
    assert notifier.sent == []
    assert db.execute(select(func.count()).select_from(SigninToken)).scalar() == 0


def test_request_link_for_roster_issues_token(db):
    db.add(RosterInvite(email="a@example.com"))
    db.flush()
    notifier = CapturingNotifier()
    service.request_link(db, "a@example.com", notifier, get_settings())
    assert len(notifier.sent) == 1
    assert "token=" in notifier.sent[0][1]
    assert db.execute(select(func.count()).select_from(SigninToken)).scalar() == 1


def test_verify_creates_member_session_and_is_single_use(db):
    settings = get_settings()
    db.add(RosterInvite(email="b@example.com"))
    db.flush()
    notifier = CapturingNotifier()
    service.request_link(db, "b@example.com", notifier, settings)
    raw = _token_from_link(notifier.sent[0][1])

    result = service.verify_link(db, raw, settings)
    assert result.member.email == "b@example.com"
    assert db.execute(select(func.count()).select_from(Member)).scalar() == 1
    assert db.execute(select(func.count()).select_from(Session)).scalar() == 1
    token_row = db.execute(select(SigninToken)).scalar_one()
    assert token_row.used_at is not None

    with pytest.raises(AppError) as exc:
        service.verify_link(db, raw, settings)
    assert exc.value.code == "invalid_or_expired_link"


def test_googlemail_and_gmail_resolve_to_one_member(db):
    settings = get_settings()
    # Both variants are roster-gated on their exact address...
    db.add_all([RosterInvite(email="foo@googlemail.com"), RosterInvite(email="foo@gmail.com")])
    db.flush()
    notifier = CapturingNotifier()

    service.request_link(db, "foo@googlemail.com", notifier, settings)
    service.verify_link(db, _token_from_link(notifier.sent[-1][1]), settings)
    service.request_link(db, "foo@gmail.com", notifier, settings)
    service.verify_link(db, _token_from_link(notifier.sent[-1][1]), settings)

    # ...but both land on a single member, keyed by the gmail.com canonical form.
    members = db.execute(select(Member)).scalars().all()
    assert len(members) == 1
    assert members[0].email == "foo@gmail.com"


def test_me_requires_authentication(db):
    client = TestClient(create_app())
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_request_link_endpoint_is_neutral(db):
    client = TestClient(create_app())
    resp = client.post("/auth/request-link", json={"email": "stranger@example.com"})
    assert resp.status_code == 202
    assert resp.json() == {"status": "ok"}
