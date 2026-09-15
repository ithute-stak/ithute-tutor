from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database.config.config import settings
from database.multi_tenant_school_management.models import User
from database.session import get_db
from utils.decode_encode_token import create_access_token, decode_token


def request_access_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[7:].strip() or None
    return request.cookies.get(settings.ACCESS_COOKIE_NAME)


def decode_access_token(token: str) -> dict:
    return decode_token(token, expected_use="access")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request_access_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Tutor session",
        )

    claims = decode_access_token(token)
    raw_user_id = claims.get("user_id")
    try:
        user_id = uuid.UUID(str(raw_user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Tutor session",
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tutor user no longer exists",
        )

    request.state.tutor_user_id = user.id
    return user


def authenticate_user(user: User) -> str:
    return create_access_token({"user_id": str(user.id), "role": getattr(user.role, "value", str(user.role))})
