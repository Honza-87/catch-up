"""Notifier protocol — provider-swappable (email now, WhatsApp later)."""

from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    """Sends a sign-in magic link to a recipient."""

    def send_login_link(self, email: str, link: str) -> None: ...
