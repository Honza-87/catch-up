"""Auth routes: magic-link request, callback, logout, current member."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import MemberDetail, RequestLinkBody
from catchup.auth import service
from catchup.auth.deps import get_current_member
from catchup.auth.ratelimit import RateLimiter
from catchup.config import Settings, get_settings
from catchup.db import get_session
from catchup.models import Member
from catchup.notify import get_notifier

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()
_email_limiter = RateLimiter(_settings.ratelimit_email_per_hour)
_ip_limiter = RateLimiter(_settings.ratelimit_ip_per_hour)


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.session_ttl_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


@router.post("/request-link", status_code=202)
def request_link(body: RequestLinkBody, request: Request, db: DbSession = Depends(get_session)) -> dict:
    """Always returns a neutral 202; a link is emailed only for roster emails."""
    settings = get_settings()
    email = str(body.email).lower()
    ip = request.client.host if request.client else "unknown"
    if _email_limiter.check(email) and _ip_limiter.check(ip):
        service.request_link(db, email, get_notifier(settings), settings)
    return {"status": "ok"}


@router.get("/callback")
def callback(token: str, response: Response, db: DbSession = Depends(get_session)) -> dict:
    """Verify a magic link, set the session cookie, return the member."""
    settings = get_settings()
    result = service.verify_link(db, token, settings)
    _set_session_cookie(response, result.session_token, settings)
    return {"member": MemberDetail.model_validate(result.member)}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: DbSession = Depends(get_session)) -> None:
    settings = get_settings()
    raw = request.cookies.get(settings.cookie_name)
    if raw:
        service.logout(db, raw)
    response.delete_cookie(settings.cookie_name, path="/")


@router.get("/me")
def me(member: Member = Depends(get_current_member)) -> dict:
    return {"member": MemberDetail.model_validate(member)}
