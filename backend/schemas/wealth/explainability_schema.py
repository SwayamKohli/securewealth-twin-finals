from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class PhishingExplanationRequest(BaseModel):
    scan_result: Dict[str, Any] = Field(..., description="Phishing scan result")


class PhishingExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Plain language explanation")
    source: str = Field(..., description="Source of explanation (LLM/RULES_FALLBACK)")
    risk_level: str = Field(..., description="Risk level from original scan")
    score: float = Field(..., description="Phishing score from original scan")


class WealthExplanationRequest(BaseModel):
    wealth_result: Dict[str, Any] = Field(..., description="Wealth engine result")
    profile: Dict[str, Any] = Field(..., description="User profile")


class WealthExplanationResponse(BaseModel):
    suppressed: bool = Field(..., description="Whether advice was suppressed")
    overview: str = Field(..., description="Overview explanation")
    health_summary: str = Field(..., description="Health summary explanation")
    recommendation_explanations: List[Dict[str, Any]] = Field(..., description="Explanations for each recommendation")
    goal_summaries: List[Any] = Field(..., description="Goal summaries")
    disclaimer: str = Field(..., description="Legal disclaimer")
    generated_by: str = Field(..., description="Generation method (LLM/template)")
    financial_health: Dict[str, Any] = Field(..., description="Financial health details")