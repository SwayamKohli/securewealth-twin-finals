# backend/schemas/transaction_schema.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from models.enums import (
    TransactionChannel,
    TransactionStatus,
)

# Task 2.3: Investment-only workflow (Savings -> Mutual Fund).
# Person-to-person and merchant payments are not supported.
APPROVED_FUND_CATEGORIES = {
    "EQUITY_MUTUAL_FUND",
    "DEBT_MUTUAL_FUND",
    "BALANCED_MUTUAL_FUND",
    "ELSS_MUTUAL_FUND",
    "INDEX_MUTUAL_FUND",
    "LIQUID_MUTUAL_FUND",
    "SIP",
    "MUTUAL_FUND",  # generic
}


class InitiateTransactionRequest(BaseModel):
    """
    Investment request. `fund_name` / `fund_category` are the canonical
    fields; the legacy `merchant_name` / `merchant_category` keys are still
    accepted for backward compatibility.
    """

    account_id: UUID
    amount: Decimal = Field(gt=0)
    fund_name: str = Field(
        validation_alias=AliasChoices("fund_name", "merchant_name"),
        description="Mutual fund / SIP the customer is investing in.",
    )
    fund_category: str = Field(
        default="MUTUAL_FUND",
        validation_alias=AliasChoices("fund_category", "merchant_category"),
        description="Approved mutual-fund category.",
    )
    channel: TransactionChannel

    @field_validator("fund_category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        normalized = v.strip().upper().replace(" ", "_").replace("-", "_")
        if normalized not in APPROVED_FUND_CATEGORIES:
            raise ValueError(
                "Only mutual fund investments are supported. "
                f"Approved categories: {sorted(APPROVED_FUND_CATEGORIES)}"
            )
        return normalized


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    transaction_id: UUID
    user_id: UUID
    account_id: UUID
    amount: Decimal
    # DB columns are still merchant_*; the API exposes them as fund_*.
    fund_name: str = Field(validation_alias=AliasChoices("fund_name", "merchant_name"))
    fund_category: str = Field(
        validation_alias=AliasChoices("fund_category", "merchant_category")
    )
    channel: TransactionChannel
    transaction_time: datetime
    status: TransactionStatus
    decision: str | None = None
    decision_timestamp: datetime | None = None
    created_at: datetime

    # Security verdict detail (populated on /initiate; task 2.4 — the frontend
    # reads the decision here instead of orchestrating AI modules itself).
    risk_score: int | None = None
    decision_report: str | None = None
    challenge_required: bool | None = None
    challenge_type: str | None = None

    # The behavioural signals that ACTUALLY fired for this investment, e.g.
    # ["amount_spike", "new_recipient"]. Previously the app synthesised this
    # list locally from the amount, so the "what we checked" panel could
    # disagree with the engine that made the decision. Now it comes from the
    # engine itself. Customer-safe: rule names only, no scores or internals.
    triggered_signals: list[str] = Field(default_factory=list)


class TransactionStatusResponse(BaseModel):
    transaction_id: UUID
    status: TransactionStatus
    decision: str | None = None
    decision_timestamp: datetime | None = None
    transaction_time: datetime
