"""Dev notifier: logs the sign-in link instead of sending email."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    def send_login_link(self, email: str, link: str) -> None:
        logger.info("MAGIC LINK for %s -> %s", email, link)
