from __future__ import annotations

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from database.multi_tenant_school_management.models import User
from database.session import SessionLocal
from utils.auth.tokens import decode_access_token, request_access_token
from utils.convex import current_user_id


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Attach Tutor's local authenticated user to the audit context when present."""

    async def dispatch(self, request: Request, call_next):
        token = request_access_token(request)
        context_token = None

        if token:
            try:
                claims = decode_access_token(token)
                user_id = uuid.UUID(str(claims.get("user_id")))
                with SessionLocal() as db:
                    user = db.get(User, user_id)
                    if user is not None:
                        request.state.tutor_user_id = user.id
                        context_token = current_user_id.set(str(user.id))
            except Exception:
                # Protected endpoints perform the authoritative 401 check.
                pass

        try:
            return await call_next(request)
        finally:
            if context_token is not None:
                current_user_id.reset(context_token)
