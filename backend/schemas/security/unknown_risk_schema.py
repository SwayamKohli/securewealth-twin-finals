from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class UnknownRiskEvent(BaseModel):
    status: str = Field(..., description="AI status (NORMAL/ANOMALOUS/UNKNOWN_RISK)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in assessment")
    transaction_id: str = Field("", description="Associated transaction ID")
    detail: Dict[str, Any] = Field({}, description="Additional details")


class UnknownRiskDecision(BaseModel):
    severity: str = Field(..., description="Risk severity (LOW/MEDIUM/HIGH)")
    decision: str = Field(..., description="Recommended decision (WARN/CHALLENGE/BLOCK)")
    reason_code: str = Field(..., description="Machine-readable reason code")
    increase_monitoring: bool = Field(..., description="Whether to increase monitoring")
    audit_entry: Dict[str, Any] = Field(..., description="Audit entry")
    timestamp: str = Field(..., description="Decision timestamp")