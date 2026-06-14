"""Pure validation helpers for profile inputs (no DB, no network)."""

from __future__ import annotations

import io

import phonenumbers
from PIL import Image, UnidentifiedImageError

from catchup.errors import AppError

_EXT_BY_TYPE = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def normalize_whatsapp(raw: str) -> str:
    """Return the E.164 form of a WhatsApp number, or raise invalid_whatsapp."""
    try:
        number = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException as exc:
        raise AppError("invalid_whatsapp", "Enter the number in international form, e.g. +420777123456.", 422) from exc
    if not phonenumbers.is_valid_number(number):
        raise AppError("invalid_whatsapp", "That doesn't look like a valid phone number.", 422)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def validate_photo(
    content_type: str | None, size: int, data: bytes, allowed_types: tuple[str, ...], max_bytes: int
) -> str:
    """Validate an uploaded image; return the file extension or raise."""
    if content_type not in allowed_types:
        raise AppError("invalid_image", "Photo must be JPEG, PNG, or WebP.", 422)
    if size > max_bytes:
        raise AppError("image_too_large", "Photo must be 5 MB or smaller.", 422)
    try:
        Image.open(io.BytesIO(data)).verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise AppError("invalid_image", "That file is not a readable image.", 422) from exc
    return _EXT_BY_TYPE[content_type]
