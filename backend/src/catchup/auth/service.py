"""Magic-link auth service: request link, verify, session lifecycle (DB + Notifier)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.auth.security import generate_token, hash_token
from catchup.auth.tokens import issue_login_token, token_is_usable
from catchup.config import Settings
from catchup.errors import AppError
from catchup.models import Member, RosterInvite, Session, SigninToken
from catchup.notify.base import Notifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerifiedLogin:
    member: Member
    session_token: str


def request_link(db: DbSession, email: str, notifier: Notifier, settings: Settings) -> None:
    """Issue + email a magic link, but only for roster emails. Always silent on miss."""
    invite = db.get(RosterInvite, email)
    if invite is None:
        logger.info("Sign-in link requested for non-roster email; ignoring")
        return
    issued = issue_login_token(settings.magic_link_ttl_minutes)
    db.add(SigninToken(email=email, token_hash=issued.token_hash, expires_at=issued.expires_at))
    db.flush()
    link = f"{settings.app_base_url}/auth/callback?token={issued.raw}"
    notifier.send_login_link(email, link)


def verify_link(db: DbSession, raw_token: str, settings: Settings) -> VerifiedLogin:
    """Validate a magic-link token, mark it used, ensure the member, open a session."""
    now = datetime.now(UTC)
    tok = db.execute(select(SigninToken).where(SigninToken.token_hash == hash_token(raw_token))).scalar_one_or_none()
    if tok is None or not token_is_usable(tok.used_at, tok.expires_at, now):
        raise AppError("invalid_or_expired_link", "This sign-in link is invalid or expired.", status_code=400)

    tok.used_at = now
    member = db.execute(select(Member).where(Member.email == tok.email)).scalar_one_or_none()
    if member is None:
        member = Member(email=tok.email)
        db.add(member)
        db.flush()
    member.last_login_at = now

    session_token = _create_session(db, member, settings, now)
    db.flush()
    return VerifiedLogin(member=member, session_token=session_token)


def logout(db: DbSession, raw_session_token: str) -> None:
    """Revoke the session backing a cookie (idempotent)."""
    sess = db.execute(select(Session).where(Session.token_hash == hash_token(raw_session_token))).scalar_one_or_none()
    if sess is not None and sess.revoked_at is None:
        sess.revoked_at = datetime.now(UTC)


def _create_session(db: DbSession, member: Member, settings: Settings, now: datetime) -> str:
    raw = generate_token()
    db.add(
        Session(
            member_id=member.id,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(days=settings.session_ttl_days),
        )
    )
    return raw
