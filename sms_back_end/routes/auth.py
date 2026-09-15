from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.config.config import settings
from database.multi_tenant_school_management.models import RefreshToken, SchoolMembership, User
from database.multi_tenant_school_management.schemas.user import UserLogin, UserRead, UserUpdate
from database.session import get_db
from utils.auth.password_hash_verify import hash_password, verify_password
from utils.auth.tokens import authenticate_user, get_current_user
from utils.decode_encode_token import create_refresh_token, decode_token
from utils.school_context import (
    SCHOOL_WORKSPACE_COOKIE,
    SchoolContext,
    get_school_context,
    require_school_roles,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


def _cookie_kwargs(max_age: int) -> dict[str, object]:
    return {
        "max_age": max_age,
        "httponly": True,
        "secure": settings.SESSION_COOKIE_SECURE,
        "samesite": settings.SESSION_COOKIE_SAMESITE,
        "path": "/",
    }


def _set_session_cookies(response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        settings.ACCESS_COOKIE_NAME,
        access_token,
        **_cookie_kwargs(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        **_cookie_kwargs(settings.refresh_cookie_max_age_seconds),
    )


def _clear_session_cookies(response) -> None:
    for name in (
        settings.ACCESS_COOKIE_NAME,
        settings.REFRESH_COOKIE_NAME,
        SCHOOL_WORKSPACE_COOKIE,
    ):
        response.delete_cookie(name, path="/")


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


def _auth_json(
    payload: dict[str, object],
    *,
    status_code: int = 200,
    clear_session: bool = False,
) -> JSONResponse:
    response = JSONResponse(payload, status_code=status_code)
    if clear_session:
        _clear_session_cookies(response)
    return _no_store(response)


def _role_value(user: User) -> str:
    return getattr(user.role, "value", str(user.role))


def _user_payload(user: User) -> dict[str, object]:
    return {
        "id": str(user.id),
        "channel": user.channel,
        "email": user.email,
        "name": user.username,
        "role": _role_value(user),
        "school_id": str(user.school_id) if user.school_id else None,
    }


def _login_payload(user: User, access_token: str) -> dict[str, object]:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": _user_payload(user),
    }


def _membership_for_school(
    db: Session,
    user_id: uuid.UUID,
    school_id: uuid.UUID,
) -> SchoolMembership | None:
    return (
        db.query(SchoolMembership)
        .filter(
            SchoolMembership.user_id == user_id,
            SchoolMembership.school_id == school_id,
            SchoolMembership.is_active.is_(True),
        )
        .first()
    )


def _user_belongs_to_school(db: Session, user: User, school_id: uuid.UUID) -> bool:
    return user.school_id == school_id or _membership_for_school(db, user.id, school_id) is not None


def _issue_refresh_token(db: Session, user: User) -> str:
    refresh_token, jti, expires_at = create_refresh_token({"user_id": str(user.id)})
    db.add(
        RefreshToken(
            jti=jti,
            user_id=user.id,
            revoked=False,
            expires_at=expires_at,
        )
    )
    return refresh_token


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.password or not verify_password(payload.password, str(user.password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = authenticate_user(user)
    refresh_token = _issue_refresh_token(db, user)
    db.commit()

    response = _auth_json(_login_payload(user, access_token))
    _set_session_cookies(response, access_token, refresh_token)
    return response


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return _user_payload(current_user)


@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        return _auth_json(
            {"detail": "Tutor session has expired"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            clear_session=True,
        )

    try:
        claims = decode_token(refresh_token, expected_use="refresh")
        user_id = uuid.UUID(str(claims.get("user_id")))
        jti = str(claims.get("jti"))
    except (HTTPException, TypeError, ValueError):
        return _auth_json(
            {"detail": "Tutor session has expired"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            clear_session=True,
        )

    stored = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.jti == jti,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
        .first()
    )
    if stored is None or stored.expires_at <= datetime.utcnow():
        return _auth_json(
            {"detail": "Tutor session has expired"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            clear_session=True,
        )

    user = db.get(User, user_id)
    if user is None:
        stored.revoked = True
        db.commit()
        return _auth_json(
            {"detail": "Tutor user no longer exists"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            clear_session=True,
        )

    # Rotate refresh tokens on every use. A stolen old refresh token cannot be replayed.
    stored.revoked = True
    access_token = authenticate_user(user)
    new_refresh = _issue_refresh_token(db, user)
    db.commit()

    response = _auth_json({"access_token": access_token, "token_type": "bearer"})
    _set_session_cookies(response, access_token, new_refresh)
    return response


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            claims = decode_token(refresh_token, expected_use="refresh")
            jti = str(claims.get("jti"))
            stored = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
            if stored is not None and not stored.revoked:
                stored.revoked = True
                db.commit()
        except HTTPException:
            pass

    response = _auth_json({"message": "Logged out successfully"})
    _clear_session_cookies(response)
    return response


@router.get("/users", response_model=list[UserRead])
def get_users(
    db: Session = Depends(get_db),
    context: SchoolContext = Depends(
        require_school_roles(
            "school_admin",
            "principal",
            "vice_principal",
            "registrar",
            "hr_manager",
            "ict_manager",
            "system_administrator",
        )
    ),
):
    user_ids = [
        row[0]
        for row in db.query(SchoolMembership.user_id)
        .filter(
            SchoolMembership.school_id == context.school_id,
            SchoolMembership.is_active.is_(True),
        )
        .all()
    ]
    query = db.query(User)
    if user_ids:
        query = query.filter(User.id.in_(user_ids))
    else:
        query = query.filter(User.school_id == context.school_id)
    return query.order_by(User.username.asc()).all()


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: SchoolContext = Depends(get_school_context),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id and not _user_belongs_to_school(db, user, context.school_id):
        raise HTTPException(status_code=404, detail="User not found in this school")
    return user


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    context: SchoolContext = Depends(
        require_school_roles("school_admin", "principal", "hr_manager", "system_administrator")
    ),
):
    user = db.get(User, user_id)
    if user is None or not _user_belongs_to_school(db, user, context.school_id):
        raise HTTPException(status_code=404, detail="User not found in this school")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = str(update_data["password"] or "")
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        update_data["password"] = hash_password(password)

    if "email" in update_data:
        normalized_email = str(update_data["email"]).strip().lower()
        duplicate = (
            db.query(User)
            .filter(User.email == normalized_email, User.id != user.id)
            .first()
        )
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="Email is already in use")
        update_data["email"] = normalized_email

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def remove_user_from_school(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    context: SchoolContext = Depends(require_school_roles("school_admin", "principal", "system_administrator")),
):
    user = db.get(User, user_id)
    if user is None or not _user_belongs_to_school(db, user, context.school_id):
        raise HTTPException(status_code=404, detail="User not found in this school")

    if user.id == context.user_id and not context.is_platform_admin:
        raise HTTPException(status_code=400, detail="You cannot remove your own active school membership")

    membership = _membership_for_school(db, user.id, context.school_id)
    if membership is not None:
        membership.is_active = False
        membership.is_default = False

    if user.school_id == context.school_id:
        replacement = (
            db.query(SchoolMembership)
            .filter(
                SchoolMembership.user_id == user.id,
                SchoolMembership.school_id != context.school_id,
                SchoolMembership.is_active.is_(True),
            )
            .order_by(SchoolMembership.is_default.desc(), SchoolMembership.created_at.asc())
            .first()
        )
        user.school_id = replacement.school_id if replacement is not None else None

    db.commit()
    return {
        "message": "User removed from this school workspace",
        "user_id": str(user.id),
        "school_id": str(context.school_id),
    }
