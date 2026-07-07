from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .mixins import CreatedAtMixin

if TYPE_CHECKING:
    from .user import User


class BehaviouralProfile(Base, CreatedAtMixin):
    __tablename__ = "behavioural_profiles"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    active_hours: Mapped[str] = mapped_column(String(50))

    average_otp_time: Mapped[Decimal] = mapped_column(
        Numeric(6, 2)
    )

    round_number_frequency: Mapped[Decimal] = mapped_column(
        Numeric(5, 2)
    )

    transaction_velocity: Mapped[Decimal] = mapped_column(
        Numeric(8, 2)
    )

    baseline_metadata: Mapped[dict] = mapped_column(
        JSONB
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="behavioural_profile",
        lazy="selectin",
    )