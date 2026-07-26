from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SqlEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean

from .base import Base, generate_uuid
from .enums import RiskProfile
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .auth_credential import AuthCredential
    from .account import Account
    from .behavioural_profile import BehaviouralProfile
    from .card import Card
    from .deposit import Deposit
    from .device import Device
    from .loan import Loan
    from .recommendation import Recommendation
    from .transaction import Transaction


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )

    full_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    risk_profile: Mapped[RiskProfile] = mapped_column(
        SqlEnum(
            RiskProfile,
            name="risk_profile_enum",
        ),
        nullable=False,
        default=RiskProfile.LOW,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    auth_credential: Mapped["AuthCredential"] = relationship(
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )

    devices: Mapped[list["Device"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    deposits: Mapped[list["Deposit"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    loans: Mapped[list["Loan"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    cards: Mapped[list["Card"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    behavioural_profile: Mapped["BehaviouralProfile"] = relationship(
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )