from __future__ import annotations

import traceback
from uuid import UUID

from sqlalchemy.orm import Session

from models.user import User
from models.enums import RiskProfile
from schemas.user_schema import UpdateUserRequest


class UserRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: UUID,
    ) -> User | None:
        try:
            return (
                db.query(User)
                .filter(User.user_id == user_id)
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ) -> User | None:
        try:
            return (
                db.query(User)
                .filter(User.email == email)
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_by_phone(
        db: Session,
        phone: str,
    ) -> User | None:
        try:
            return (
                db.query(User)
                .filter(User.phone == phone)
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def create(
        db: Session,
        user: User,
    ) -> User:
        try:
            db.add(user)
            db.flush()  # Get the user_id without committing
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def update(
        db: Session,
        user: User,
        full_name: str | None = None,
        email: str | None = None,
        date_of_birth: str | None = None,
        risk_profile: RiskProfile | None = None,
    ) -> User:
        try:
            if full_name is not None:
                user.full_name = full_name
            if email is not None:
                user.email = email
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth
            if risk_profile is not None:
                user.risk_profile = risk_profile

            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def deactivate(
        db: Session,
        user: User,
    ) -> User:
        try:
            user.is_active = False

            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def activate(
        db: Session,
        user: User,
    ) -> User:
        try:
            user.is_active = True

            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise