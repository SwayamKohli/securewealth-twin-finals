from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import LoanType
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Loan(Base, TimestampMixin):
    __tablename__ = "loans"

    loan_id: Mapped[uuid.UUID] = mapped_column(
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

    loan_type: Mapped[LoanType] = mapped_column(
        SqlEnum(LoanType, name="loan_type_enum"),
        nullable=False,
    )

    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    emi: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    remaining_tenure: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="loans",
        lazy="selectin",
    )