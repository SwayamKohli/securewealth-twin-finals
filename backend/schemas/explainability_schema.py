from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class PhishingExplanationRequest(BaseModel):
    scan_result: Dict[str, Any] = Field(..., description="Phishing scan result to explain")
    language: str = Field("en", description="Output language: en | hi | pa")


class PhishingExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Plain language explanation of phishing detection")
    source: str = Field(..., description="Source of explanation (LLM or RULES_FALLBACK)")
    risk_level: str = Field(..., description="Risk level from original scan")
    score: float = Field(..., description="Phishing score from original scan")


class ChallengeExplanationRequest(BaseModel):
    requirement: Dict[str, Any] = Field(..., description="Challenge requirement to explain")
    language: str = Field("en", description="Output language: en | hi | pa")
    ollama_url: Optional[str] = Field(None, description="Custom Ollama URL if using local LLM")


class ChallengeExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Explanation of why challenge is required")
    source: str = Field(..., description="Source of explanation")


class DecisionExplanationRequest(BaseModel):
    record: Dict[str, Any] = Field(..., description="Decision record to explain")
    language: str = Field("en", description="Output language: en | hi | pa")
    ollama_url: Optional[str] = Field(None, description="Custom Ollama URL if using local LLM")


class DecisionExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Explanation of transaction decision")
    source: str = Field("template", description="llm = local model answered; template = deterministic fallback")


class DeviceTrustExplanationRequest(BaseModel):
    trust_result: Dict[str, Any] = Field(..., description="Device trust result to explain")
    user_profile: Dict[str, Any] = Field(..., description="User profile for personalization")
    language: Optional[str] = Field("en", description="Output language: en | hi | pa")


class DeviceTrustExplanationResponse(BaseModel):
    device_status: str = Field(..., description="Device trust status")
    device_confidence: int = Field(..., description="Device confidence score")
    security_signals: List[str] = Field(..., description="Security signals detected")
    customer_message: str = Field(..., description="Reassuring message for customer")
    generated_by: str = Field(..., description="Generation method")


class RiskExplanationRequest(BaseModel):
    output: Dict[str, Any] = Field(..., description="Risk evaluation output to explain")
    ollama_url: Optional[str] = Field(None, description="Custom Ollama URL if using local LLM")


class RiskExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Explanation of risk evaluation")
    source: str = Field("template", description="llm = local model answered; template = deterministic fallback")


class UnknownRiskExplanationRequest(BaseModel):
    decision_output: Dict[str, Any] = Field(..., description="Unknown risk decision to explain")
    ollama_url: Optional[str] = Field(None, description="Custom Ollama URL if using local LLM")


class UnknownRiskExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Explanation of unknown risk decision")
    source: str = Field("template", description="llm = local model answered; template = deterministic fallback")


class WealthExplanationRequest(BaseModel):
    wealth_result: Dict[str, Any] = Field(..., description="Wealth engine result to explain")
    profile: Dict[str, Any] = Field(..., description="User profile for context")
    # Was missing entirely, so switching the app to Hindi or Punjabi translated
    # every label but left the actual advice in English.
    language: Optional[str] = Field("en", description="Output language: en | hi | pa")


class WealthExplanationResponse(BaseModel):
    suppressed: bool = Field(..., description="Whether advice was suppressed")
    overview: str = Field(..., description="Overview explanation")
    health_summary: str = Field(..., description="Health summary explanation")
    recommendation_explanations: List[Dict[str, Any]] = Field(..., description="Explanations for each recommendation")
    goal_summaries: List[Any] = Field(..., description="Goal summaries")
    disclaimer: str = Field(..., description="Legal disclaimer")
    generated_by: str = Field(..., description="Generation method")
    financial_health: Dict[str, Any] = Field(..., description="Financial health details")