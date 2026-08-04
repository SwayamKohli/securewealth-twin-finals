from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class RecommendationType(Enum):
    EMERGENCY_FUND = "EMERGENCY_FUND"
    FD = "FD"
    RD = "RD"
    SIP = "SIP"


class Recommendation(BaseModel):
    recommendation_id: str = Field(..., description="Unique identifier for the recommendation")
    recommendation: str = Field(..., description="Recommendation title")
    product: str = Field(..., description="Product category")
    amount: int = Field(..., ge=0, description="Suggested amount")
    tenure: str = Field(..., description="Tenure information")
    reason: str = Field(..., description="Reason for recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    expected_benefit: str = Field(..., description="Expected benefit")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    source: str = Field(..., description="Source reference")


class GoalSummary(BaseModel):
    goal_type: str = Field(..., description="Type of goal")
    target_amount: float = Field(..., description="Target amount for the goal")
    gap: float = Field(..., description="Remaining gap to achieve goal")
    completion_pct: float = Field(..., description="Completion percentage")
    months_remaining: int = Field(..., description="Months remaining to achieve goal")
    feasibility: str = Field(..., description="Feasibility assessment")
    priority: str = Field(..., description="Priority level")


class FinancialHealth(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Financial health score (0-100)")
    grade: str = Field(..., description="Grade (A/B/C/D)")
    components: Dict[str, float] = Field(..., description="Breakdown of health components")


class WealthRequest(BaseModel):
    profile_data: Dict[str, Any] = Field(..., description="Financial profile data")
    fraud_probability: float = Field(0.0, ge=0.0, le=1.0, description="Fraud probability score")


class WealthPosition(BaseModel):
    """Task 3.2 — Assets, Liabilities and Net Worth surfaced to the frontend."""
    total_assets: float = Field(..., description="Total assets (INR)")
    total_liabilities: float = Field(..., description="Total liabilities (INR)")
    net_worth: float = Field(..., description="Assets minus liabilities (INR)")


class WealthResponse(BaseModel):
    suppressed: bool = Field(..., description="Whether advice is suppressed")
    suppress_reason: Optional[str] = Field(None, description="Reason for suppression")
    user_id: str = Field(..., description="User identifier")
    financial_health: FinancialHealth = Field(..., description="Financial health metrics")
    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    goal_summaries: List[GoalSummary] = Field(..., description="Goal progress summaries")
    wealth_position: Optional[WealthPosition] = Field(None, description="Assets / Liabilities / Net Worth")
    disclaimer: str = Field(..., description="Legal disclaimer")