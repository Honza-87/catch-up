"""Resend transactional-email notifier."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


class ResendNotifier:
    def __init__(self, api_key: str, sender: str) -> None:
        self._api_key = api_key
        self._sender = sender

    def send_login_link(self, email: str, link: str) -> None:
        html = (
            f'<p>Tap to sign in to catch-up:</p><p><a href="{link}">Sign in</a></p>'
            f"<p>This link expires shortly and can be used once.</p>"
        )
        resp = httpx.post(
            _RESEND_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "from": self._sender,
                "to": [email],
                "subject": "Your catch-up sign-in link",
                "html": html,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        logger.info("Sent login link email to %s", email)
