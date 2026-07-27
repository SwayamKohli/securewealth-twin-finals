# backend/models/transaction.py
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import TransactionChannel, TransactionStatus
from .mixins import CreatedAtMixin

if TYPE_CHECKING:
    from .account import Account
    from .user import User


class Transaction(Base, CreatedAtMixin):
    __tablename__ = "transactions"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
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

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    merchant_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    merchant_category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    channel: Mapped[TransactionChannel] = mapped_column(
        SqlEnum(TransactionChannel, name="transaction_channel_enum"),
        nullable=False,
    )

    transaction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SqlEnum(TransactionStatus, name="transaction_status_enum"),
        nullable=False,
    )

    # NEW: Security decision field
    decision: Mapped[str | None] = mapped_column(
        String(20),  # ALLOW, WARN, CHALLENGE, BLOCK
        nullable=True,
    )

    decision_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="transactions",
        lazy="selectin",
    )

    account: Mapped["Account"] = relationship(
        back_populates="transactions",
        lazy="selectin",
    )