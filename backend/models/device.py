from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import DeviceType, TrustStatus
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    device_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    device_type: Mapped[DeviceType] = mapped_column(
        SqlEnum(
            DeviceType,
            name="device_type_enum",
        ),
        nullable=False,
    )

    sim_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    trust_status: Mapped[TrustStatus] = mapped_column(
        SqlEnum(
            TrustStatus,
            name="trust_status_enum",
        ),
        nullable=False,
        default=TrustStatus.TRUSTED,
    )

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="devices",
        lazy="selectin",
    )