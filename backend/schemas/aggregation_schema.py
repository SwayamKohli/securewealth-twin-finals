from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Request Schemas
# ==========================================================


class LinkAccountRequest(BaseModel):
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


class SyncRequest(BaseModel):
    force_refresh: bool = False


# ==========================================================
# Response Schemas
# ==========================================================


class AggregatedAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: UUID
    bank_name: str
    account_type: str
    account_number_masked: str
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class AggregationStatusResponse(BaseModel):
    accounts_connected: int
    last_synced: datetime | None = None
    healthy: bool
    status: str


class SyncResponse(BaseModel):
    success: bool
    synced_accounts: int
    message: str
    synced_at: datetime


class NetWorthResponse(BaseModel):
    total_account_balance: Decimal
    total_deposits: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


class CashflowResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_cashflow: Decimal
    transaction_count: int