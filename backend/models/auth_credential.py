from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .mixins import CreatedAtMixin

if TYPE_CHECKING:
    from .user import User


class AuthCredential(Base, CreatedAtMixin):
    """
    Stores authentication credentials for a user.

    This table is intentionally separated from the
    users table so authentication remains independent
    from profile information.
    """

    __tablename__ = "auth_credentials"

    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    mpin_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="auth_credential",
        lazy="selectin",
    )