"""Unit tests for pure trip date-range validation (no DB)."""

from __future__ import annotations

from datetime import date

import pytest

from catchup.errors import AppError
from catchup.trips.validation import validate_trip_dates


def test_end_after_start_ok():
    validate_trip_dates(date(2026, 7, 1), date(2026, 7, 10))


def test_equal_dates_ok():
    validate_trip_dates(date(2026, 7, 1), date(2026, 7, 1))


def test_end_before_start_rejected():
    with pytest.raises(AppError) as exc:
        validate_trip_dates(date(2026, 7, 10), date(2026, 7, 1))
    assert exc.value.code == "invalid_dates"
    assert exc.value.status_code == 422
