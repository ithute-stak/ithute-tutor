from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from database.config.config import settings
from utils.decode_encode_token import create_access_token, create_refresh_token, decode_token


def use_test_secret(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "test-secret-key-that-is-long-enough-for-tutor-only")
    monkeypatch.setattr(settings, "ALGORITHM", "HS256")


def test_access_token_is_owned_and_validated_by_tutor(monkeypatch):
    use_test_secret(monkeypatch)
    user_id = uuid.uuid4()

    token = create_access_token({"user_id": str(user_id), "role": "school_admin"})
    claims = decode_token(token, expected_use="access")

    assert claims["user_id"] == str(user_id)
    assert claims["role"] == "school_admin"
    assert claims["token_use"] == "access"
    assert claims["jti"]


def test_refresh_token_cannot_be_used_as_access_token(monkeypatch):
    use_test_secret(monkeypatch)
    token, _, _ = create_refresh_token({"user_id": str(uuid.uuid4())})

    with pytest.raises(HTTPException) as exc:
        decode_token(token, expected_use="access")

    assert exc.value.status_code == 401


def test_tampered_token_is_rejected(monkeypatch):
    use_test_secret(monkeypatch)
    token = create_access_token({"user_id": str(uuid.uuid4())})
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(HTTPException) as exc:
        decode_token(tampered, expected_use="access")

    assert exc.value.status_code == 401
