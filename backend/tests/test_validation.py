"""Unit tests for pure profile validation (no DB)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from catchup.errors import AppError
from catchup.members.validation import normalize_whatsapp, validate_photo

_ALLOWED = ("image/jpeg", "image/png", "image/webp")
_MAX = 5 * 1024 * 1024


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(buf, format="PNG")
    return buf.getvalue()


def test_normalize_whatsapp_returns_e164():
    assert normalize_whatsapp("+420 777 123 456") == "+420777123456"


def test_normalize_whatsapp_rejects_garbage():
    with pytest.raises(AppError) as exc:
        normalize_whatsapp("not a number")
    assert exc.value.code == "invalid_whatsapp"


def test_normalize_whatsapp_rejects_without_country_code():
    with pytest.raises(AppError):
        normalize_whatsapp("777123456")


def test_validate_photo_accepts_png():
    data = _png_bytes()
    assert validate_photo("image/png", len(data), data, _ALLOWED, _MAX) == "png"


def test_validate_photo_rejects_wrong_type():
    with pytest.raises(AppError) as exc:
        validate_photo("text/plain", 10, b"hello", _ALLOWED, _MAX)
    assert exc.value.code == "invalid_image"


def test_validate_photo_rejects_too_large():
    data = _png_bytes()
    with pytest.raises(AppError) as exc:
        validate_photo("image/png", _MAX + 1, data, _ALLOWED, _MAX)
    assert exc.value.code == "image_too_large"


def test_validate_photo_rejects_fake_image_bytes():
    with pytest.raises(AppError) as exc:
        validate_photo("image/png", 5, b"hello", _ALLOWED, _MAX)
    assert exc.value.code == "invalid_image"
