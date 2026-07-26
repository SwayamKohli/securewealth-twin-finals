from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class FraudProbability(BaseModel):
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Fraud probability score (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the fraud probability")
    risk_factors: List[Dict[str, Any]] = Field(..., description="Risk factors that contributed to the score")
    signal_scores: Dict[str, int] = Field(..., description="Per-category signal scores (0-100)")
    ml_details: Dict[str, Any] = Field(..., description="Machine learning model details")
    baseline_used: str = Field(..., description="Which baseline was used (personalized/global_fallback)")


class FraudRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    device_id: str = Field(..., description="Device identifier")
    recipient_id: str = Field(..., description="Recipient identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    hour: int = Field(..., ge=0, le=23, description="Hour of transaction (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    otp_time_sec: float = Field(..., ge=0, description="OTP entry time in seconds")
    session_duration: float = Field(..., ge=0, description="Session duration in milliseconds")
    txns_last_1h: int = Field(..., ge=0, description="Number of transactions in last hour")
    txns_last_24h: int = Field(..., ge=0, description="Number of transactions in last 24 hours")
    in_active_window: Optional[int] = Field(None, description="Whether transaction is in active window")


class FraudResponse(BaseModel):
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Calculated fraud probability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the assessment")
    risk_factors: List[Dict[str, Any]] = Field(..., description="Detailed risk factors")
    signal_scores: Dict[str, int] = Field(..., description="Scores per signal category")
    ml_details: Dict[str, Any] = Field(..., description="ML model details and SHAP values")
    baseline_used: str = Field(..., description="Type of baseline used for comparison")