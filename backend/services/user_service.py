from __future__ import annotations

import traceback
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from database.repositories.user_repository import UserRepository
from models.user import User
from models.enums import RiskProfile
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

            # Check for email uniqueness if email is being updated
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
                full_name=payload.full_name,
                email=payload.email,
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

    @staticmethod
    def create_user(
        db: Session,
        user_id: UUID,
        full_name: str,
        phone: str,
        email: str | None = None,
        date_of_birth: date | None = None,
        risk_profile: RiskProfile = RiskProfile.LOW,
    ) -> User:
        try:
            # Check if phone already exists
            existing_user = UserRepository.get_by_phone(
                db=db,
                phone=phone,
            )
            
            if existing_user:
                raise ValueError("Phone number already exists.")
            
            # Check if email already exists if provided
            if email:
                existing_email_user = UserRepository.get_by_email(
                    db=db,
                    email=email,
                )
                
                if existing_email_user:
                    raise ValueError("Email already exists.")

            user = User(
                user_id=user_id,
                full_name=full_name,
                phone=phone,
                email=email,
                date_of_birth=date_of_birth,
                risk_profile=risk_profile,
                is_active=True,
            )

            return UserRepository.create(
                db=db,
                user=user,
            )

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def activate_user(
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

            if user.is_active:
                raise ValueError("User already active.")

            return UserRepository.activate(
                db=db,
                user=user,
            )

        except Exception:
            traceback.print_exc()
            raise