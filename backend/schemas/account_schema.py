from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import AccountType
from schemas.transaction_schema import TransactionResponse


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: UUID
    user_id: UUID
    bank_name: str
    account_type: AccountType
    account_number_masked: str
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class BalanceResponse(BaseModel):
    account_id: UUID
    balance: Decimal
    currency: str
    last_updated: datetime


class AccountSummaryResponse(BaseModel):
    account: AccountResponse
    current_balance: Decimal
    recent_transactions: list[TransactionResponse]


class CreateAccountRequest(BaseModel):
    bank_name: str = Field(
        ...,
        max_length=100,
    )
    account_type: str = Field(
        ...,
        max_length=20,
    )
    account_number: str = Field(
        ...,
        min_length=4,
        max_length=30,
    )
    balance: Decimal
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )