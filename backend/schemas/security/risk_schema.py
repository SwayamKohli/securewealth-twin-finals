from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class EnvironmentInput(BaseModel):
    ip_region: str = Field(..., description="IP region of transaction")
    last_login_region: str = Field(..., description="Region of last login")
    time_since_last_login_ms: int = Field(..., description="Time since last login in milliseconds")
    network_type: str = Field(..., description="Network type (HOME_WIFI, MOBILE_DATA, etc)")


class RiskEvaluationInput(BaseModel):
    behavior_signals: Dict[str, Any] = Field(..., description="Behavioral signals from behavior engine")
    environment: EnvironmentInput = Field(..., description="Environmental context")
    device_trust: Dict[str, Any] = Field(..., description="Device trust information")
    ai_fraud_probability: float = Field(0.0, ge=0.0, le=1.0, description="AI fraud probability")
    ai_confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence")


class RiskEvaluationOutput(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Calculated risk score (0-100)")
    security_signals: Dict[str, Any] = Field(..., description="Security signals and details")
    timestamp: str = Field(..., description="Timestamp of evaluation")
    compliance_note: str = Field(..., description="Compliance reference")