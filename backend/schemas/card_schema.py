from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import CardType


class CreateCardRequest(BaseModel):
    card_type: CardType

    issuer: str = Field(
        ...,
        min_length=1,
        max_length=120,
    )

    reward_type: str = Field(
        ...,
        min_length=1,
        max_length=80,
    )

    cashback_rate: Decimal = Field(
        ...,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    credit_limit: Decimal = Field(
        ...,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )


class UpdateCardRequest(BaseModel):
    card_type: CardType | None = None

    issuer: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    reward_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )

    cashback_rate: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )


class CardResponse(BaseModel):
    card_id: UUID
    user_id: UUID

    card_type: CardType

    issuer: str
    reward_type: str

    cashback_rate: Decimal
    credit_limit: Decimal

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )