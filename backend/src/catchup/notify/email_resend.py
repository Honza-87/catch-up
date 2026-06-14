"""Resend transactional-email notifier."""

from __future__ import annotations

import logging

import httpx

from catchup.notify.base import OverlapDigestItem

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


class ResendNotifier:
    def __init__(self, api_key: str, sender: str, overlap_subject: str = "New catch-up overlaps") -> None:
        self._api_key = api_key
        self._sender = sender
        self._overlap_subject = overlap_subject

    def _send(self, email: str, subject: str, html: str) -> None:
        resp = httpx.post(
            _RESEND_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"from": self._sender, "to": [email], "subject": subject, "html": html},
            timeout=10.0,
        )
        resp.raise_for_status()

    def send_login_link(self, email: str, link: str) -> None:
        html = (
            f'<p>Tap to sign in to catch-up:</p><p><a href="{link}">Sign in</a></p>'
            f"<p>This link expires shortly and can be used once.</p>"
        )
        self._send(email, "Your catch-up sign-in link", html)
        logger.info("Sent login link email to %s", email)

    def send_overlap_digest(self, email: str, member_name: str | None, overlaps: list[OverlapDigestItem]) -> None:
        items = "".join(
            f"<li><strong>{o.other_member_name or 'A classmate'}</strong> in "
            f"{o.place_label or o.country_name} — {o.strength}, {o.start_date} to {o.end_date}</li>"
            for o in overlaps
        )
        html = (
            f"<p>Hi {member_name or 'there'}, you have new overlaps with classmates:</p>"
            f"<ul>{items}</ul>"
            f"<p>Open catch-up to see them on the map.</p>"
        )
        self._send(email, self._overlap_subject, html)
        logger.info("Sent overlap digest email to %s (%d items)", email, len(overlaps))
