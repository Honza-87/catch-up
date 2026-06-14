"""Shared test fixtures.

Unit tests touch none of this. Smoke tests (`@pytest.mark.smoke`) request the
`db` fixture, which requires a live Postgres at $DATABASE_URL: it brings the
schema to head once per session and truncates tables before each test.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from catchup.db import SessionLocal, engine

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_TABLES = ["overlap", "trip", "significant_event", "session", "signin_token", "roster_invite", "member", "place"]


@pytest.fixture(scope="session")
def _alembic_head() -> None:
    """Bring the database schema to head once per test session (smoke only)."""
    subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=_BACKEND_DIR)


@pytest.fixture
def db(_alembic_head: None) -> Iterator[Session]:
    """A clean session against the live database (truncates first)."""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
