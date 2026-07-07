from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import LoanType


class CreateLoanRequest(BaseModel):
    loan_type: LoanType

    outstanding_amount: Decimal = Field(
        ...,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    emi: Decimal = Field(
        ...,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    interest_rate: Decimal = Field(
        ...,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    remaining_tenure: int = Field(
        ...,
        ge=0,
    )


class UpdateLoanRequest(BaseModel):
    loan_type: LoanType | None = None

    outstanding_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    emi: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    interest_rate: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    remaining_tenure: int | None = Field(
        default=None,
        ge=0,
    )


class LoanResponse(BaseModel):
    loan_id: UUID
    user_id: UUID

    loan_type: LoanType

    outstanding_amount: Decimal
    emi: Decimal
    interest_rate: Decimal
    remaining_tenure: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )