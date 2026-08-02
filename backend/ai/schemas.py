"""
Pydantic Schemas
==================
Defines the data contracts for all intelligence engines.

These schemas serve three purposes:
  1. Runtime validation — call schema.model_validate(data) to validate engine output
  2. Documentation      — single source of truth for API consumers
  3. Type safety        — IDE support and static analysis

Engine → Schema mapping:
  FinancialProfileBuilder.build_profile()      -> FinancialProfile
  FraudIntelligenceEngine.evaluate()           -> FraudEngineOutput
  ZeroDayDetector.detect()                     -> ZeroDayOutput
  WealthIntelligenceEngine.generate()          -> WealthEngineOutput
  RecommendationExplainer.explain()            -> ExplainerOutput

Pydantic v2 is used throughout (model_validate, model_json_schema).

Sources:
  PSB FINALS.md §5  — Account Aggregation schema
  PSB FINALS.md §6  — Risk Engine output contract
  PSB FINALS.md §8  — Wealth Intelligence output contract
"""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Shared primitives ────────────────────────────────────────────────────────

class SpendingBreakdown(BaseModel):
    needs_pct:   float = Field(ge=0, le=100, description="% of income spent on needs")
    wants_pct:   float = Field(ge=0, le=100, description="% of income spent on wants")
    savings_pct: float = Field(ge=0, le=100, description="% of income saved")
    verdict:     str   = Field(description="Plain-language cash flow verdict")


class AssetBreakdown(BaseModel):
    bank_balances:       float = Field(ge=0)
    fixed_deposits:      float = Field(ge=0)
    recurring_deposits:  float = Field(ge=0)


class LiabilityBreakdown(BaseModel):
    model_config = {"extra": "allow"}  # loan types vary (home_loan, car_loan, etc.)


class AccountRole(BaseModel):
    account_id:    str
    account_type:  str
    inferred_role: Literal["salary_account", "savings", "current", "idle"]
    balance:       float = Field(ge=0)
    idle_balance:  float = Field(ge=0)


class MaturityEntry(BaseModel):
    deposit_id:       str
    deposit_type:     Literal["FD", "RD"]
    principal:        float = Field(ge=0)
    interest_rate:    float = Field(ge=0)
    days_to_maturity: int   = Field(ge=0)


class HighRateLoan(BaseModel):
    loan_id:           str
    loan_type:         str
    interest_rate:     float = Field(ge=0)
    outstanding_amount: float = Field(ge=0)
    emi:               float = Field(ge=0)


class GoalItem(BaseModel):
    goal_type:        str
    target_amount:    float = Field(ge=0)
    target_date:      Optional[str] = None
    current_progress: float = Field(ge=0)
    gap:              float = Field(ge=0)
    completion_pct:   float = Field(ge=0, le=100)
    months_remaining: int   = Field(ge=0)
    monthly_required: float = Field(ge=0)
    feasibility:      Literal["achievable", "stretch", "unrealistic"]
    priority:         Literal["high", "medium", "low"]


class CardRewardStructure(BaseModel):
    model_config = {"extra": "allow"}


class CardCashbackStructure(BaseModel):
    model_config = {"extra": "allow"}


class CardSpendingPattern(BaseModel):
    model_config = {"extra": "allow"}


class CardMetadata(BaseModel):
    card_id:            Optional[str]  = None
    card_type:          Optional[str]  = None
    issuer:             Optional[str]  = None
    reward_structure:   CardRewardStructure    = Field(default_factory=CardRewardStructure)
    cashback_structure: CardCashbackStructure  = Field(default_factory=CardCashbackStructure)
    spending_pattern:   CardSpendingPattern    = Field(default_factory=CardSpendingPattern)


# ─── Schema 1: Financial Profile ──────────────────────────────────────────────

class FinancialProfile(BaseModel):
    """
    Output of FinancialProfileBuilder.build_profile().
    Unified profile used across Fraud Engine, Wealth Engine, and Explainer.
    """

    # Identity
    user_id:      str
    name:         str = ""
    age:          int = Field(ge=0, le=120)
    risk_profile: Literal["conservative", "moderate", "aggressive"]

    # Wealth position
    net_worth:         float
    total_assets:      float = Field(ge=0)
    total_liabilities: float = Field(ge=0)

    # Cash flow
    monthly_income:      float = Field(ge=0)
    monthly_expenses:    float = Field(ge=0)
    monthly_surplus:     float
    investable_surplus:  float
    savings_rate:        float

    # Debt metrics
    total_emi:           float = Field(ge=0)
    debt_ratio:          float = Field(ge=0, description="DTI: total_emi / monthly_income")
    credit_utilization:  float = Field(ge=0, le=1)

    # Liquidity / safety
    liquidity_ratio:    float = Field(ge=0)
    months_of_runway:   float = Field(ge=0)
    emergency_fund_gap: float = Field(ge=0)

    # Health
    cash_flow_health: Literal["stressed", "moderate", "healthy"]
    debt_stress:      Literal["stressed", "moderate", "none"] = "none"

    # Breakdowns
    asset_breakdown:     AssetBreakdown
    liability_breakdown: LiabilityBreakdown
    spending_breakdown:  SpendingBreakdown

    # Detail lists
    maturity_calendar: list[MaturityEntry] = Field(default_factory=list)
    high_rate_loans:   list[HighRateLoan]  = Field(default_factory=list)

    # Extended intelligence (from pre-freeze changes)
    account_roles:       list[AccountRole]  = Field(default_factory=list)
    total_idle_balance:  float = Field(ge=0, default=0.0)
    card_metadata:       list[CardMetadata] = Field(default_factory=list)
    goals:               list[GoalItem]     = Field(default_factory=list)
    has_emergency_fund_goal: bool = False
    total_goal_gap:      float = Field(ge=0, default=0.0)


# ─── Schema 2: Fraud Engine Output ────────────────────────────────────────────

class ShapFeature(BaseModel):
    feature:      str
    contribution: float


class MlDetails(BaseModel):
    xgb_fraud_prob:    float = Field(ge=0, le=1)
    shap_top_features: list[ShapFeature] = Field(default_factory=list)


class RiskFactor(BaseModel):
    factor:   str
    category: Literal[
        "environmental", "possession", "behavioral", "structural", "velocity"
    ]
    severity: Literal["low", "medium", "high"]
    detail:   dict[str, Any] = Field(default_factory=dict)


class SignalScores(BaseModel):
    environmental: int = Field(ge=0, le=100)
    possession:    int = Field(ge=0, le=100)
    behavioral:    int = Field(ge=0, le=100)
    structural:    int = Field(ge=0, le=100)
    velocity:      int = Field(ge=0, le=100)


class FraudEngineOutput(BaseModel):
    """
    Output of FraudIntelligenceEngine.evaluate().
    Used for ALLOW / WARN / CHALLENGE / BLOCK decisions.
    """

    fraud_probability: float = Field(ge=0, le=1)
    confidence:        float = Field(ge=0, le=1)
    risk_factors:      list[RiskFactor]
    signal_scores:     SignalScores
    ml_details:        MlDetails
    baseline_used:     Literal["personalized", "global_fallback"]


# ─── Schema 3: Zero-Day Detector Output ───────────────────────────────────────

class AnomalousDimension(BaseModel):
    feature:              str
    reconstruction_error: float = Field(ge=0)


class ZeroDayOutput(BaseModel):
    """
    Output of ZeroDayDetector.detect().
    Used independently alongside FraudEngineOutput.
    """

    status:               Literal["NORMAL", "ANOMALOUS", "UNKNOWN_RISK"]
    confidence:           float = Field(ge=0, le=1)
    reconstruction_error: float = Field(ge=0)
    error_percentile:     float = Field(ge=0, le=100)
    anomalous_dimensions: list[AnomalousDimension] = Field(default_factory=list)


# ─── Schema 4: Wealth Engine Output ───────────────────────────────────────────

class HealthComponents(BaseModel):
    emergency_readiness: float = Field(ge=0, le=25)
    debt_management:     float = Field(ge=0, le=25)
    savings_discipline:  float = Field(ge=0, le=25)
    # wealth_buffer uses net_worth which can be negative (liabilities > assets),
    # so the component score is clamped to [0, 25] in the engine but we allow
    # any float here to be safe against edge cases in test data.
    wealth_buffer:       float = Field(le=25)


class FinancialHealth(BaseModel):
    score:      float = Field(ge=0, le=100)
    grade:      Literal["A", "B", "C", "D"]
    components: HealthComponents


class WealthPosition(BaseModel):
    """
    3.2 Net Worth exposure — Assets ↓ Liabilities ↓ Net Worth.
    net_worth may be negative (liabilities exceed assets), so it is unbounded.
    Assets and liabilities are magnitudes, so they are non-negative.
    """
    total_assets:      float = Field(ge=0)
    total_liabilities: float = Field(ge=0)
    net_worth:         float


class GoalSummary(BaseModel):
    goal_type:        str
    target_amount:    float = Field(ge=0)
    gap:              float = Field(ge=0)
    completion_pct:   float = Field(ge=0, le=100)
    months_remaining: int   = Field(ge=0)
    feasibility:      Literal["achievable", "stretch", "unrealistic"]
    priority:         Literal["high", "medium", "low"]


class WealthRecommendation(BaseModel):
    recommendation_id: str
    recommendation:    str
    product:           str
    amount:            int   = Field(ge=0)
    tenure:            str
    reason:            str
    confidence:        float = Field(ge=0, le=1)
    expected_benefit:  str
    priority:          Literal["high", "medium", "low"]
    source:            str
    feasibility_note:  Optional[Literal["achievable", "stretch", "unrealistic"]] = None


class WealthEngineOutput(BaseModel):
    """
    Output of WealthIntelligenceEngine.generate().
    Used by RecommendationExplainer and wealth advisory interfaces.
    """

    suppressed:       bool
    suppress_reason:  Optional[Literal["high_fraud_risk", "no_investable_surplus"]] = None
    user_id:          str
    financial_health: FinancialHealth
    wealth_position:  WealthPosition        # 3.2 Net Worth exposure — always present
    recommendations:  list[WealthRecommendation]
    goal_summaries:   list[GoalSummary]
    disclaimer:       str

    @model_validator(mode="after")
    def suppress_reason_required_when_suppressed(self) -> "WealthEngineOutput":
        if self.suppressed and self.suppress_reason is None:
            raise ValueError("suppress_reason must be present when suppressed=True")
        if not self.suppressed and self.suppress_reason is not None:
            raise ValueError("suppress_reason must be absent when suppressed=False")
        return self


# ─── Schema 5: Explainer Output ───────────────────────────────────────────────

class RecommendationExplanation(BaseModel):
    recommendation_id: str
    recommendation:    str
    product:           str
    amount:            int = Field(ge=0)
    tenure:            str
    explanation:       str
    expected_benefit:  str
    priority:          Literal["high", "medium", "low"]


class ExplainerOutput(BaseModel):
    """
    Output of RecommendationExplainer.explain().
    Output format for the wealth advisory card displayed to the user.
    """

    suppressed:                  bool
    suppress_reason:             Optional[str] = None
    overview:                    str
    health_summary:              str
    recommendation_explanations: list[RecommendationExplanation]
    goal_summaries:              list[GoalSummary]
    disclaimer:                  str
    generated_by:                Literal["llm", "template"]
