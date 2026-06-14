"""Photo storage interface + provider selection."""

from __future__ import annotations

from catchup.config import Settings, get_settings
from catchup.storage.photos import PhotoStore, S3PhotoStore


def get_photo_store(settings: Settings | None = None) -> PhotoStore:
    settings = settings or get_settings()
    return S3PhotoStore(
        endpoint=settings.s3_endpoint,
        bucket=settings.s3_bucket,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        region=settings.s3_region,
        public_base_url=settings.s3_public_base_url,
    )


__all__ = ["PhotoStore", "S3PhotoStore", "get_photo_store"]
