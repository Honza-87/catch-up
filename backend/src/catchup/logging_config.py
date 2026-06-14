"""Standard-library logging configuration (no print() in library code)."""

from __future__ import annotations

import logging

from catchup.config import get_settings

_configured = False


def configure_logging() -> None:
    """Configure root logging once, at the level from settings."""
    global _configured
    if _configured:
        return
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _configured = True
