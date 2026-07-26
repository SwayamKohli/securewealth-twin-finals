from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, generate_uuid
from .enums import CardType
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Card(Base, TimestampMixin):
    __tablename__ = "cards"

    card_id: Mapped[uuid.UUID] = mapped_column(
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

    card_type: Mapped[CardType] = mapped_column(
        SqlEnum(CardType, name="card_type_enum"),
        nullable=False,
    )

    issuer: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    reward_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    cashback_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="cards",
        lazy="selectin",
    )