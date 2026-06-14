"""Unit tests for pure event date-range validation (no DB)."""

from __future__ import annotations

from datetime import date

import pytest

from catchup.errors import AppError
from catchup.events.validation import validate_event_dates


def test_end_after_start_ok():
    validate_event_dates(date(2026, 7, 1), date(2026, 7, 3))


def test_equal_dates_ok():
    validate_event_dates(date(2026, 7, 1), date(2026, 7, 1))


def test_end_before_start_rejected():
    with pytest.raises(AppError) as exc:
        validate_event_dates(date(2026, 7, 3), date(2026, 7, 1))
    assert exc.value.code == "invalid_dates"
    assert exc.value.status_code == 422
