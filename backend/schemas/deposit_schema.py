from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.enums import DepositType


class CreateDepositRequest(BaseModel):
    deposit_type: DepositType
    principal: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )
    interest_rate: Decimal = Field(
        ...,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )
    start_date: date
    maturity_date: date
    institution: str = Field(
        ...,
        min_length=1,
        max_length=120,
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date <= self.start_date:
            raise ValueError(
                "maturity_date must be after start_date"
            )
        return self


class UpdateDepositRequest(BaseModel):
    deposit_type: DepositType | None = None

    principal: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    interest_rate: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    start_date: date | None = None
    maturity_date: date | None = None

    institution: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.maturity_date is not None
            and self.maturity_date <= self.start_date
        ):
            raise ValueError(
                "maturity_date must be after start_date"
            )
        return self


class DepositResponse(BaseModel):
    deposit_id: UUID
    user_id: UUID

    deposit_type: DepositType

    principal: Decimal
    interest_rate: Decimal

    start_date: date
    maturity_date: date

    institution: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )