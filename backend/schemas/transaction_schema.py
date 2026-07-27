# backend/schemas/transaction_schema.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.enums import (
    TransactionChannel,
    TransactionStatus,
)


class InitiateTransactionRequest(BaseModel):
    account_id: UUID
    amount: Decimal
    merchant_name: str
    merchant_category: str
    channel: TransactionChannel


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    user_id: UUID
    account_id: UUID
    amount: Decimal
    merchant_name: str
    merchant_category: str
    channel: TransactionChannel
    transaction_time: datetime
    status: TransactionStatus
    decision: str | None = None  # NEW: Security decision
    decision_timestamp: datetime | None = None  # NEW: Decision timestamp
    created_at: datetime


class TransactionStatusResponse(BaseModel):
    transaction_id: UUID
    status: TransactionStatus
    decision: str | None = None  # NEW: Include decision in status
    decision_timestamp: datetime | None = None
    transaction_time: datetime