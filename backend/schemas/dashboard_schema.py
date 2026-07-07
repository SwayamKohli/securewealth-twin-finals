from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from schemas.account_schema import AccountResponse
from schemas.transaction_schema import TransactionResponse
from schemas.user_schema import UserResponse


class NetWorthResponse(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    user: UserResponse
    accounts: list[AccountResponse]
    net_worth: NetWorthResponse
    recent_transactions: list[TransactionResponse]
    notifications: list[str]

    model_config = ConfigDict(from_attributes=True)


class DashboardActivityResponse(BaseModel):
    transactions: list[TransactionResponse]

    model_config = ConfigDict(from_attributes=True)


class FinancialHealthResponse(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    total_accounts: int
    total_deposits: int
    total_loans: int

    model_config = ConfigDict(from_attributes=True)