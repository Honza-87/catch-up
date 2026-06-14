"""Pure event validation: date-range rules (no DB, no I/O)."""

from __future__ import annotations

from datetime import date

from catchup.errors import AppError


def validate_event_dates(start_date: date, end_date: date) -> None:
    """Reject inverted ranges; a single-day event (end == start) is valid."""
    if end_date < start_date:
        raise AppError("invalid_dates", "End date must be on or after start date.", status_code=422)
