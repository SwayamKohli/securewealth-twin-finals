from __future__ import annotations

import traceback
from uuid import UUID

from sqlalchemy.orm import Session

from database.repositories.user_repository import UserRepository
from models.user import User
from schemas.user_schema import UpdateUserRequest


class UserService:

    @staticmethod
    def get_me(
        db: Session,
        user_id: UUID,
    ) -> User:
        try:
            user = UserRepository.get_by_id(
                db=db,
                user_id=user_id,
            )

            if not user:
                raise ValueError("User not found.")

            if not user.is_active:
                raise ValueError("User account is deactivated.")

            return user

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def update_me(
        db: Session,
        user_id: UUID,
        payload: UpdateUserRequest,
    ) -> User:
        try:
            user = UserRepository.get_by_id(
                db=db,
                user_id=user_id,
            )

            if not user:
                raise ValueError("User not found.")

            if not user.is_active:
                raise ValueError("User account is deactivated.")

            if (
                payload.email is not None
                and payload.email != user.email
            ):
                existing_user = UserRepository.get_by_email(
                    db=db,
                    email=payload.email,
                )

                if (
                    existing_user
                    and existing_user.user_id != user.user_id
                ):
                    raise ValueError("Email already exists.")

            return UserRepository.update(
                db=db,
                user=user,
                payload=payload,
            )

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def delete_me(
        db: Session,
        user_id: UUID,
    ) -> User:
        try:
            user = UserRepository.get_by_id(
                db=db,
                user_id=user_id,
            )

            if not user:
                raise ValueError("User not found.")

            if not user.is_active:
                raise ValueError("User already deactivated.")

            return UserRepository.deactivate(
                db=db,
                user=user,
            )

        except Exception:
            traceback.print_exc()
            raise