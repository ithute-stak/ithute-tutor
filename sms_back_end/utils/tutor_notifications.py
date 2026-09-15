from uuid import UUID

from sqlalchemy.orm import Session

from database.multi_tenant_school_management.models import Notification


EVENT_POLICIES = {
    "assignment.published": {"route": "/student/assignments"},
    "assignment.graded": {"route": "/student/results"},
    "admission.decision": {"route": "/admissions"},
    "attendance.absent": {"route": "/student/attendance"},
    "report.published": {"route": "/student/results"},
    "fee.payment_received": {"route": "/payments"},
    "transfer.updated": {"route": "/transfers"},
    "school.emergency": {"route": "/notifications"},
    "library.due": {"route": "/student/library"},
}


def notify_user(
    db: Session,
    *,
    school_id: UUID,
    user_id: UUID,
    event: str,
    title: str,
    message: str,
    data: dict | None = None,
) -> None:
    """Create a Tutor-owned in-app notification.

    External push delivery is intentionally not coupled to any other Ithute
    service. A Tutor-specific delivery provider can be added later behind this
    local notification boundary.
    """
    db.add(
        Notification(
            school_id=school_id,
            user_id=user_id,
            channel="tutor",
            title=title,
            message=message,
            event=event,
        )
    )
