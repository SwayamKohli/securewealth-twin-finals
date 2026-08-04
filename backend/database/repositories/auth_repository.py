# This only knows how to talk to postgres and perform CRUD operations on the auth tables

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.auth_credential import AuthCredential
from models.user import User


class AuthRepository:

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------
    # USER
    # ----------------------------

    def get_user_by_customer_id(
        self,
        customer_id: str,
    ) -> User | None:

        statement = (
            select(User)
            .where(User.customer_id == customer_id.upper())
        )

        return self.db.execute(statement).scalar_one_or_none()

    def get_user_by_phone(
        self,
        phone: str,
    ) -> User | None:

        statement = (
            select(User)
            .where(User.phone == phone)
        )

        return self.db.scalar(statement)

    def create_user(
        self,
        user: User,
    ) -> User:

        self.db.add(user)
        self.db.flush()

        return user

    # ----------------------------
    # AUTH CREDENTIALS
    # ----------------------------

    def get_credentials(
        self,
        user_id: UUID,
    ) -> AuthCredential | None:

        statement = (
            select(AuthCredential)
            .where(AuthCredential.user_id == user_id)
        )

        return self.db.scalar(statement)

    def create_credentials(
        self,
        credentials: AuthCredential,
    ) -> AuthCredential:

        self.db.add(credentials)
        self.db.flush()

        return credentials

    # ----------------------------
    # LOGIN HELPERS
    # ----------------------------

    def update_last_login(
        self,
        credentials: AuthCredential,
    ) -> None:

        credentials.last_login = datetime.now(
            timezone.utc
        )

    def increment_failed_attempts(
        self,
        credentials: AuthCredential,
    ) -> None:

        credentials.failed_attempts += 1

    def reset_failed_attempts(
        self,
        credentials: AuthCredential,
    ) -> None:

        credentials.failed_attempts = 0