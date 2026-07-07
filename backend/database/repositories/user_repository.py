from __future__ import annotations

import traceback
from uuid import UUID

from sqlalchemy.orm import Session

from models.user import User
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
    def update(
        db: Session,
        user: User,
        payload: UpdateUserRequest,
    ) -> User:
        try:
            user.full_name = payload.full_name
            user.email = payload.email

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