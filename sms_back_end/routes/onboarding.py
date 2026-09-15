from __future__ import annotations

from fastapi import APIRouter, Depends

from database.multi_tenant_school_management.models import User
from utils.auth.tokens import get_current_user


router = APIRouter(prefix="/onboarding", tags=["Tutor Onboarding"])


@router.get("/status")
def onboarding_status(current_user: User = Depends(get_current_user)):
    """Return the local Tutor user's onboarding state."""
    return {
        "user_id": str(current_user.id),
        "needs_school": current_user.school_id is None,
        "role": getattr(current_user.role, "value", str(current_user.role)),
    }
