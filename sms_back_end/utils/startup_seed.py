from __future__ import annotations

import os

from sqlalchemy.orm import Session

from database.session import SessionLocal
from database.multi_tenant_school_management.models import User, Grade, Class
from database.multi_tenant_school_management.schemas.user import UserRole
from utils.auth.password_hash_verify import hash_password


def seed_super_admin(db: Session):
    """Optionally create Tutor's first local super administrator.

    This bootstrap belongs only to Tutor. It does not create or link an account
    in any other Ithute product.
    """
    email = os.getenv("TUTOR_BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    if not email:
        return

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.role != UserRole.super_admin:
            existing.role = UserRole.super_admin
        # Do not overwrite an existing password on every application restart.
        return

    password = os.getenv("TUTOR_BOOTSTRAP_ADMIN_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError(
            "TUTOR_BOOTSTRAP_ADMIN_PASSWORD must be at least 12 characters when bootstrapping an admin"
        )

    user = User(
        username=os.getenv("TUTOR_BOOTSTRAP_ADMIN_USERNAME", "superadmin").strip() or "superadmin",
        email=email,
        password=hash_password(password),
        channel="system",
        role=UserRole.super_admin,
        school_id=None,
    )
    db.add(user)
    db.flush()
    print("Tutor local super admin created")


def seed_grades_and_classes(db: Session):
    grade_names = ["Grade-R"] + [f"Grade-{i}" for i in range(1, 13)]

    for grade_name in grade_names:
        grade = db.query(Grade).filter(Grade.name == grade_name).first()
        if not grade:
            grade = Grade(name=grade_name)
            db.add(grade)
            db.flush()

        for i in range(1, 6):
            class_name = f"{grade_name}_{i}"
            existing_class = (
                db.query(Class)
                .filter(Class.name == class_name, Class.grade_id == grade.id)
                .first()
            )
            if existing_class:
                continue
            db.add(Class(name=class_name, grade_id=grade.id))


def run_startup_seed():
    db = SessionLocal()
    try:
        seed_super_admin(db)
        seed_grades_and_classes(db)
        db.commit()
        print("Tutor startup seed completed")
    except Exception as exc:
        db.rollback()
        print(f"Tutor startup seed failed: {exc}")
        raise
    finally:
        db.close()
