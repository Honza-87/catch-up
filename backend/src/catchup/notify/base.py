"""Notifier protocol — provider-swappable (email now, WhatsApp later)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class OverlapDigestItem:
    """One overlap line in a member's digest (plain data; no provider specifics)."""

    other_member_name: str | None
    place_label: str | None  # city for strong overlaps; None for country-only (medium)
    country_name: str
    strength: str  # "strong" | "medium"
    start_date: date
    end_date: date


class Notifier(Protocol):
    """Delivers transactional messages to members."""

    def send_login_link(self, email: str, link: str) -> None: ...

    def send_overlap_digest(self, email: str, member_name: str | None, overlaps: list[OverlapDigestItem]) -> None: ...
