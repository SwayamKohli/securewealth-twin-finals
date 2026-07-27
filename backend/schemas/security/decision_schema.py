from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class TransactionContext(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., description="Transaction amount")
    channel: str = Field(..., description="Transaction channel (UPI, IMPS, etc)")
    risk_input: Dict[str, Any] = Field(..., description="Risk evaluation input")
    unknown_risk_event: Optional[Dict[str, Any]] = Field(None, description="Unknown risk event")


class DecisionRecord(BaseModel):
    transaction_id: str = Field(..., description="Transaction identifier")
    account_id: str = Field(..., description="Masked account identifier")
    amount: float = Field(..., description="Transaction amount")
    channel: str = Field(..., description="Transaction channel")
    decision: str = Field(..., description="Final decision (ALLOW/WARN/CHALLENGE/BLOCK)")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score used for decision")
    security_signals: Dict[str, Any] = Field(..., description="Security signals")
    challenge_required: bool = Field(..., description="Whether challenge is required")
    challenge_type: str = Field("", description="Type of challenge required")
    challenge_details: Optional[Dict[str, Any]] = Field(None, description="Full challenge details")
    unknown_risk_applied: bool = Field(..., description="Whether unknown risk was applied")
    unknown_risk_decision: str = Field("", description="Unknown risk decision")
    unknown_risk_reason_code: str = Field("", description="Unknown risk reason code")
    report: str = Field(..., description="Decision report")
    audit_note: str = Field(..., description="Audit note")
    decision_timestamp: str = Field(..., description="Timestamp of decision")
    compliance_ref: str = Field(..., description="Compliance reference")