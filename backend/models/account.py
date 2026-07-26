from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import AccountType
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .transaction import Transaction
    from .user import User


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    account_id: Mapped[uuid.UUID] = mapped_column(
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

    bank_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SqlEnum(
            AccountType,
            name="account_type_enum",
        ),
        nullable=False,
    )

    account_number_masked: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    user: Mapped["User"] = relationship(
        back_populates="accounts",
        lazy="selectin",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        lazy="selectin",
    )