from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import DepositType
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Deposit(Base, TimestampMixin):
    __tablename__ = "deposits"

    deposit_id: Mapped[uuid.UUID] = mapped_column(
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

    deposit_type: Mapped[DepositType] = mapped_column(
        SqlEnum(
            DepositType,
            name="deposit_type_enum",
        ),
        nullable=False,
    )

    principal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    maturity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    institution: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="deposits",
        lazy="selectin",
    )