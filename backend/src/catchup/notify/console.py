"""Dev notifier: logs messages instead of sending email."""

from __future__ import annotations

import logging

from catchup.notify.base import OverlapDigestItem

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    def send_login_link(self, email: str, link: str) -> None:
        logger.info("MAGIC LINK for %s -> %s", email, link)

    def send_overlap_digest(self, email: str, member_name: str | None, overlaps: list[OverlapDigestItem]) -> None:
        lines = [
            f"  - {o.other_member_name or 'A classmate'} in {o.place_label or o.country_name} "
            f"({o.strength}) {o.start_date}–{o.end_date}"
            for o in overlaps
        ]
        logger.info(
            "OVERLAP DIGEST for %s (%s): %d new\n%s",
            member_name or "member",
            email,
            len(overlaps),
            "\n".join(lines),
        )
