"""Notifier interface + provider selection."""

from __future__ import annotations

from catchup.config import Settings, get_settings
from catchup.notify.base import Notifier, OverlapDigestItem
from catchup.notify.console import ConsoleNotifier
from catchup.notify.email_resend import ResendNotifier


def get_notifier(settings: Settings | None = None) -> Notifier:
    """Return the configured Notifier implementation."""
    settings = settings or get_settings()
    if settings.notifier == "resend":
        return ResendNotifier(
            api_key=settings.resend_api_key,
            sender=settings.email_from,
            overlap_subject=settings.overlap_email_subject,
        )
    return ConsoleNotifier()


__all__ = ["Notifier", "OverlapDigestItem", "ConsoleNotifier", "ResendNotifier", "get_notifier"]
