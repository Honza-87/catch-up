"""Application settings, loaded from environment via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Storage of record
    database_url: str = "postgresql+psycopg://catchup:catchup@localhost:5432/catchup"

    # Signing + sessions
    session_secret: str = "change-me"
    app_base_url: str = "http://localhost:5173"

    # Notifier
    notifier: Literal["console", "resend"] = "console"
    resend_api_key: str = ""
    email_from: str = "catch-up <login@example.com>"
    overlap_email_subject: str = "New catch-up overlaps"

    # Geocoder
    geocoder_url: str = "https://photon.komoot.io"

    # Object storage (S3-compatible)
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "catchup-photos"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_public_base_url: str = "http://localhost:9000/catchup-photos"

    # Auth tuning
    magic_link_ttl_minutes: int = 15
    session_ttl_days: int = 30
    cookie_name: str = "catchup_session"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Rate limits (sign-in link requests)
    ratelimit_email_per_hour: int = 5
    ratelimit_ip_per_hour: int = 20

    # Photo upload
    photo_max_bytes: int = 5 * 1024 * 1024
    photo_allowed_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
