from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models.enums import AccountType


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
        description="Name of the bank"
    )
    account_type: AccountType = Field(
        ...,
        description="Type of account (SAVINGS, CURRENT, SALARY)"
    )
    account_number: str = Field(
        ...,
        min_length=4,
        max_length=30,
        description="Actual account number (will be masked)"
    )
    balance: Decimal = Field(
        ...,
        gt=0,
        description="Current account balance"
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Currency code (default: INR)"
    )


class UpdateAccountRequest(BaseModel):
    bank_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated bank name"
    )
    balance: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Updated account balance"
    )
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Updated currency code"
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    user_id: UUID
    account_id: UUID
    amount: Decimal
    merchant_name: str
    merchant_category: str
    channel: str
    transaction_time: datetime
    status: str
    created_at: datetime