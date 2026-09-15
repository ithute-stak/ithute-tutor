from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt
from fastapi import HTTPException

from database.config.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(data: dict, *, token_use: str, expires_delta: timedelta, jti: str | None = None) -> str:
    now = _now()
    payload = {
        **data,
        "token_use": token_use,
        "jti": jti or str(uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return pyjwt.encode(payload, settings.require_secret_key(), algorithm=settings.ALGORITHM)


def decode_token(token: str, *, expected_use: str | None = None) -> dict:
    try:
        payload = pyjwt.decode(
            token,
            settings.require_secret_key(),
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "iat", "jti", "token_use"]},
        )
    except pyjwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Session token has expired") from exc
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid session token") from exc

    if expected_use and payload.get("token_use") != expected_use:
        raise HTTPException(status_code=401, detail="Invalid session token type")
    return payload


def create_access_token(data: dict) -> str:
    return _encode(
        data,
        token_use="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(data: dict):
    jti = str(uuid4())
    expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _encode(
        data,
        token_use="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        jti=jti,
    )
    # SQLAlchemy's current model stores a timezone-naive UTC DateTime.
    return token, jti, expires_at.replace(tzinfo=None)
