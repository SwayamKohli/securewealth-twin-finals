"""
Converts raw Account Aggregation (AA) data into a unified financial profile.
This profile is the unified data structure used across intelligence engines:
  - WealthIntelligenceEngine
  - FraudIntelligenceEngine (for user baseline context)
  - ExplainabilityEngine     — for generating human-readable output

Sources:
  [8]  Virginia Tech AAEC-184 (2024) — 4-month emergency fund, ≥20% savings
  [13] Elizabeth Warren — 50/30/20 rule
  [14] Indian Wealth Management Personal Financial Ratios (2018)
  RBI norms — DTI > 50% = stressed, no growth investing

AA Data Schema (expected input):
  {
    "user_id":              str,
    "name":                 str,
    "age":                  int,
    "risk_profile":         "conservative" | "moderate" | "aggressive",
    "monthly_income":       float,
    "monthly_expenses":     float,
    "accounts":             [{account_id, account_type, balance}],
    "deposits":             [{deposit_id, deposit_type, principal, interest_rate, maturity_date}],
    "loans":                [{loan_id, loan_type, outstanding_amount, emi, interest_rate}],
    "cards":                [{card_id, card_type, outstanding_balance, credit_limit, issuer, reward_structure, cashback_structure, spending_pattern}],
    "spending_breakdown":   {needs: float, wants: float, savings: float},
    "goals":                [{goal_type, target_amount, target_date, current_progress}],
  }
"""
from .account_analyzer   import analyze_accounts
from .cashflow_analyzer  import analyze_cashflow
from .liability_analyzer import analyze_liabilities
from .goal_analyzer      import analyze_goals

class FinancialProfileBuilder:
    """
    Build a unified financial profile from raw AA data.

    Usage:
        builder = FinancialProfileBuilder()
        profile = builder.build_profile(aa_data)

    The returned profile dict is the contract between the data layer and
    all AI modules. Do not add fields here without updating schemas.py.
    """

    # Source: [8] Virginia Tech — 4-month emergency fund target
    EMERGENCY_FUND_MONTHS = 4

    # Source: [8] — savings rate thresholds
    SAVINGS_RATE_HEALTHY  = 0.20
    SAVINGS_RATE_LOW      = 0.10

    # RBI norms — DTI thresholds
    DTI_STRESSED  = 0.50
    DTI_MODERATE  = 0.35

    def build_profile(self, aa_data: dict) -> dict:
        """
        Main entry point. Orchestrates the three sub-analyzers and computes
        derived metrics used by the wealth and fraud engines.

        Returns a flat dict (no nesting beyond breakdowns).
        """
        # ── Aggregation results ──────────────────────────────────────────────────
        asset_info    = analyze_accounts(aa_data)
        cashflow_info = analyze_cashflow(aa_data)
        liability_info = analyze_liabilities(aa_data)

        income    = cashflow_info["monthly_income"]
        expenses  = cashflow_info["monthly_expenses"]
        surplus   = cashflow_info["monthly_surplus"]

        liquid    = asset_info["liquid_balance"]   # savings + current accounts
        total_emi = liability_info["total_emi"]
        dti       = liability_info["debt_ratio"]

        # ── Emergency fund gap ─────────────────────────────────────────────────
        # Target: 4 months of expenses [8]
        emergency_target = expenses * self.EMERGENCY_FUND_MONTHS
        emergency_gap    = max(0.0, emergency_target - liquid)
        runway_months    = round(liquid / expenses, 1) if expenses > 0 else 0.0

        # ── Cash flow health classification ────────────────────────────────────
        # Uses both DTI (debt side) and savings rate (income side) [8][14]
        savings_rate = cashflow_info["savings_rate"]
        cash_flow_health = self._classify_health(dti, surplus, savings_rate)

        # ── Investable surplus ─────────────────────────────────────────────────
        # Conservative: keep a 10% buffer on expenses before declaring investable
        investable_surplus = max(0.0, surplus - expenses * 0.10)
        
        # ── Goal Analysis ──────────────────────────────────────────────────────
        goal_info = analyze_goals(aa_data, investable_surplus)
        
        # ── Card Metadata Extraction ───────────────────────────────────────────
        card_metadata = []
        for c in aa_data.get("cards", []):
            card_metadata.append({
                "card_id": c.get("card_id"),
                "card_type": c.get("card_type"),
                "issuer": c.get("issuer"),
                "reward_structure": c.get("reward_structure", {}),
                "cashback_structure": c.get("cashback_structure", {}),
                "spending_pattern": c.get("spending_pattern", {}),
            })

        # ── Assemble full profile ──────────────────────────────────────────────
        profile = {
            # Identity
            "user_id":              aa_data["user_id"],
            "name":                 aa_data.get("name", ""),
            "age":                  aa_data.get("age", 30),
            "risk_profile":         aa_data.get("risk_profile", "moderate"),

            # Wealth position — Source: [14]
            "net_worth":            round(asset_info["total"] - liability_info["total"], 2),
            "total_assets":         round(asset_info["total"],         2),
            "total_liabilities":    round(liability_info["total"],     2),

            # Cash flow metrics
            "monthly_income":       income,
            "monthly_expenses":     expenses,
            "monthly_surplus":      round(surplus,            2),
            "investable_surplus":   round(investable_surplus, 2),
            "savings_rate":         savings_rate,

            # Debt metrics — RBI norms
            "total_emi":            total_emi,
            "debt_ratio":           dti,          # DTI
            "credit_utilization":   liability_info["credit_utilization"],

            # Liquidity / safety — Source: [8]
            "liquidity_ratio":      round(liquid / expenses, 2) if expenses > 0 else 0.0,
            "months_of_runway":     runway_months,
            "emergency_fund_gap":   round(emergency_gap, 2),

            # Health classification
            "cash_flow_health":     cash_flow_health,

            # Breakdowns (for wealth engine layers and explainability)
            "asset_breakdown":      asset_info["breakdown"],
            "liability_breakdown":  liability_info["breakdown"],
            "spending_breakdown":   cashflow_info["spending_breakdown"],

            # Detail lists (for wealth engine Layer 5 + debt layer)
            "maturity_calendar":    asset_info["maturity_calendar"],
            "high_rate_loans":      liability_info["high_rate_loans"],
            "debt_stress":          liability_info["debt_stress"],
            
            # Additional intelligence
            "account_roles":        asset_info.get("account_roles", []),
            "total_idle_balance":   asset_info.get("total_idle_balance", 0.0),
            "card_metadata":        card_metadata,
            "goals":                goal_info["goals"],
            "has_emergency_fund_goal": goal_info["has_emergency_fund_goal"],
            "total_goal_gap":       goal_info["total_goal_gap"],
        }

        return profile

    def _classify_health(self, dti: float, surplus: float, savings_rate: float) -> str:
        """
        Classify overall cash flow health.

        stressed  — DTI > 50%, or no surplus (can't pay expenses)
        moderate  — DTI 35–50%, or savings rate < 10%
        healthy   — DTI < 35% and savings rate ≥ 20%

        Sources: [8] Virginia Tech thresholds, RBI DTI norms
        """
        if dti > self.DTI_STRESSED or surplus <= 0:
            return "stressed"

        if dti > self.DTI_MODERATE or savings_rate < self.SAVINGS_RATE_LOW:
            return "moderate"

        return "healthy"
