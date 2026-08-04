"""
Wealth Intelligence Engine
==========================
Generates personalized, goal-aware wealth recommendations via a
6-layer deterministic pipeline.

Scope boundaries:
  ✅  Emergency Fund (Liquid FD / RD)
  ✅  FD / RD Planning and reinvestment alerts
  ✅  SIP Planning (Equity / Debt / Balanced MF — product categories only)
  ✅  Expense Optimization
  ✅  Debt Reduction / Prepayment suggestions
  ✅  Goal-Based Recommendations (emergency_fund, education, home_purchase, retirement, custom)
  ✅  Idle Balance Deployment suggestions
  ❌  Stock picks / intraday / guaranteed returns
  ❌  SEBI advisory activities
  ❌  Autonomous investing
  ❌  Credit Card Recommendation Engine (PSB FINALS.md §8 — explicitly out of scope)

Pipeline design: pure rule-based. No ML, no LLM inside this engine.

Security contract:
  - This engine does NOT decide to allow or block any transaction.
  - It SUPPRESSES wealth advice when fraud_probability > 0.70.
  - All amounts are INR. All figures are simulation estimates, not guarantees.

Sources:
  [8]  Virginia Tech Extension AAEC-184 (2024)
       — 4-month emergency fund, ≥20% savings, 50/30/20 rule
  [9]  Value Research — 8 Golden Rules of SIP (2025)
  [10] LinkedIn — Personalizing MF Recommendations (2025)
  [11] RBI Digital Lending Directions (2025)
  [12] ICICI Prudential MF Industry Report (2025)
  [13] Elizabeth Warren — 50/30/20 Budget Rule
  [14] Indian Wealth Management Personal Financial Ratios (2018)
  [22] RBI Product Awareness norms
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ─── Constants ────────────────────────────────────────────────────────────────

# Security gate: suppress wealth advice above this fraud probability.
# Rationale: investment decisions under active account compromise risk are invalid.
FRAUD_RISK_GATE = 0.70

# Source [8] Virginia Tech — 4-month emergency fund minimum
EMERGENCY_FUND_MONTHS = 4

# Source [11] RBI — DTI > 50% = financially stressed, no growth investing
DTI_STRESSED = 0.50

# Source [8] — DTI > 35% = moderate stress, debt management first
DTI_MODERATE = 0.35

# Any loan above this rate: prepaying earns more than most FDs  [source: [14]]
HIGH_RATE_THRESHOLD_PCT = 10.0

# FD maturing within this many days triggers a reinvestment alert  [Layer 5]
FD_MATURITY_ALERT_DAYS = 90

# Idle balance above this multiple of monthly expenses = strong FD suggestion
IDLE_TO_FD_MULTIPLIER = 2.0

# SIP band: 20–30% of investable surplus, capped and floored  [source: [9]]
SIP_RATE_MIN = 0.20
SIP_RATE_MAX = 0.30
SIP_FLOOR_INR = 500
SIP_CAP_INR  = 25_000

# Minimum surplus to add a secondary SIP recommendation  [source: [9]]
SECONDARY_SIP_MIN_SURPLUS = 5_000

# Life-stage equity caps  [source: [10], [14]]
#   Age > 55 → capital preservation priority
#   Age > 40 → balanced approach
#   Age <= 40 → growth-first
EQUITY_CAP_BY_AGE = {
    "senior": 0.20,   # age > 55
    "mid":    0.50,   # 40 < age <= 55
    "young":  0.80,   # age <= 40
}

# Risk tolerance modifiers on equity cap  [source: [10]]
RISK_EQUITY_MODIFIER = {
    "conservative": 0.50,    # halve the cap
    "moderate":     1.00,    # no change
    "aggressive":   1.30,    # raise by 30%, capped at 1.0
}

# ── 3.1 Monthly Expense Integration ───────────────────────────────────────────
# Expense-to-income ratio above this is "high" and worth surfacing to the user
# even when a surplus exists. Complements the 50/30/20 rule.  [source: [13]]
HIGH_EXPENSE_RATIO = 0.70

# ── 3.3 Mutual Fund Only — approved product whitelist ─────────────────────────
# Every recommendation the engine emits MUST use one of these product categories.
# Deposit products (FD/RD), mutual-fund CATEGORIES only (never a scheme name),
# debt prepayment, and budgeting guidance. Stocks, specific fund names, intraday,
# and guaranteed-return products are structurally impossible to emit.
# Enforced by _assert_products_approved() before every return.  [source: PSB FINALS.md §8]
APPROVED_PRODUCTS = frozenset([
    "Liquid Fixed Deposit",
    "Fixed Deposit",
    "Fixed Deposit Renewal",
    "Recurring Deposit",
    "Debt Mutual Fund (SIP)",
    "Equity Mutual Fund (SIP)",
    "Balanced Mutual Fund (SIP)",
    "ELSS Mutual Fund (SIP) — 3-year lock-in",
    "Recurring Deposit / Direct Prepayment",
    "Budgeting Review",
])

# Legal disclaimer — must appear on every non-suppressed response  [source: PSB FINALS.md §8]
DISCLAIMER = (
    "Simulation Only — Not Financial Advice. "
    "Consult a SEBI-registered investment advisor before making any investment decisions."
)


# ─── Engine ───────────────────────────────────────────────────────────────────

class WealthIntelligenceEngine:
    """
    6-layer personalized wealth recommendation engine.

    The engine is stateless and thread-safe. One instance can serve all requests.

    Usage
    -----
    engine = WealthIntelligenceEngine()
    result = engine.generate(profile, fraud_probability=0.12)

    Layers (executed in order):
        Security Gate  — suppress all advice when fraud_probability > 0.70
        Layer 1        — Financial Position Check: can the user invest at all?
        Layer 2        — Debt Burden: prioritise debt reduction if DTI > 50%
        Layer 3        — Emergency Readiness: 4-month runway gate
        Layer 4        — Life Stage & Risk Calibration: equity cap derivation
        Layer 5        — Existing Product Awareness: FD maturities, idle balances
        Goal Layer     — Goal-specific recommendations (ordered by goal priority)
        Layer 6        — Debt Optimisation: high-rate prepayment suggestion
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        profile:           dict,
        fraud_probability: float = 0.0,
    ) -> dict:
        """
        Generate wealth recommendations for a user profile.

        Parameters
        ----------
        profile           : dict from FinancialProfileBuilder.build_profile()
        fraud_probability : float, 0.0–1.0 from FraudIntelligenceEngine.evaluate()
                            Defaults to 0.0 (no fraud signal) when called standalone.

        Returns
        -------
        dict:
            suppressed           bool    True if advice is withheld (fraud gate / no surplus)
            suppress_reason      str     Why advice is suppressed (only when suppressed=True)
            user_id              str
            financial_health     dict    Health score + component breakdowns
            recommendations      list    List of recommendation dicts (empty if suppressed)
            goal_summaries       list    Summary of each goal's status (always present)
            disclaimer           str     Legal disclaimer (always present)
        """
        user_id = profile.get("user_id", "UNKNOWN")

        # Always compute goal summaries, health, and wealth position — these are
        # informational, not suppressed by the fraud gate (user still needs to
        # see their goals and net worth even during a security review).
        goal_summaries   = self._build_goal_summaries(profile)
        financial_health = self._compute_financial_health(profile)
        wealth_position  = self._build_wealth_position(profile)   # 3.2

        # ── Security Gate ──────────────────────────────────────────────────────
        # Design directive — suppress investment advice during
        # active security review. The user can still see their goal progress.
        if fraud_probability > FRAUD_RISK_GATE:
            return self._finalize({
                "suppressed":      True,
                "suppress_reason": "high_fraud_risk",
                "user_id":         user_id,
                "financial_health": financial_health,
                "wealth_position": wealth_position,
                "recommendations": [],
                "goal_summaries":  goal_summaries,
                "disclaimer":      DISCLAIMER,
            })

        # ── Layer 1: Financial Position ────────────────────────────────────────
        # Source: [8] Can the user invest at all?
        # Suppress growth recommendations entirely if there is no surplus.
        surplus = profile.get("investable_surplus", 0.0)
        if surplus <= 0:
            expense_rec = self._expense_optimization(profile)
            return self._finalize({
                "suppressed":      True,
                "suppress_reason": "no_investable_surplus",
                "user_id":         user_id,
                "financial_health": financial_health,
                "wealth_position": wealth_position,
                "recommendations": [expense_rec] if expense_rec else [],
                "goal_summaries":  goal_summaries,
                "disclaimer":      DISCLAIMER,
            })

        # ── Layer 2: Debt Burden ───────────────────────────────────────────────
        # Source: [11] RBI norms — DTI > 50% = stressed, no growth investing.
        dti = profile.get("debt_ratio", 0.0)
        if dti > DTI_STRESSED:
            debt_rec = self._debt_reduction(profile)
            return self._finalize({
                "suppressed":      False,
                "user_id":         user_id,
                "financial_health": financial_health,
                "wealth_position": wealth_position,
                "recommendations": [debt_rec] if debt_rec else [],
                "goal_summaries":  goal_summaries,
                "disclaimer":      DISCLAIMER,
                # Context for explainability layer
                "_context": {
                    "priority_action": "debt_reduction",
                    "dti_pct": round(dti * 100, 1),
                },
            })

        # ── Layer 3: Emergency Readiness ───────────────────────────────────────
        # Source: [8] Build 4-month runway before growth investing.
        recs: list[dict] = []
        months_of_runway = profile.get("months_of_runway", 0.0)
        emergency_gap    = profile.get("emergency_fund_gap", 0.0)
        has_ef_goal      = profile.get("has_emergency_fund_goal", False)

        # ── 3.1 Monthly Expense Integration ────────────────────────────────────
        # Derive an expense-ratio signal used to personalise recommendation text.
        # High expenses (even with a surplus) mean SIP capacity is being throttled
        # by discretionary spend — we surface that in the SIP/goal reasons below.
        expense_ctx = self._expense_context(profile)

        if months_of_runway < EMERGENCY_FUND_MONTHS and not has_ef_goal:
            # No explicit emergency fund goal — add an implicit one
            ef_deposit = min(emergency_gap, surplus * 6) if surplus > 0 else emergency_gap
            ef_deposit  = _round_to_hundred(ef_deposit)
            if ef_deposit > 0:
                recs.append({
                    "recommendation_id": "emergency_fund_implicit",
                    "recommendation":    "Build Emergency Fund",
                    "product":           "Liquid Fixed Deposit",
                    "amount":            ef_deposit,
                    "tenure":            "No lock-in",
                    "reason": (
                        f"Your liquid savings cover {months_of_runway:.1f} months of expenses. "
                        f"A minimum of {EMERGENCY_FUND_MONTHS} months is recommended before growth investing. "
                        f"Gap: {_fmt_inr(emergency_gap)}."
                    ),
                    "confidence":       0.95,
                    "expected_benefit": f"Financial safety net — covers {EMERGENCY_FUND_MONTHS} months of expenses",
                    "priority":         "high",
                    "source":           "[8] Virginia Tech AAEC-184",
                })

        # ── Layer 4: Life Stage & Risk Calibration ─────────────────────────────
        # Source: [10] Equity cap depends on age and declared risk profile.
        equity_cap = self._compute_equity_cap(profile)

        # ── Layer 5: Existing Product Awareness ────────────────────────────────
        # 5a: FD maturities  — Source: [22] RBI product awareness norms
        recs.extend(self._fd_maturity_alerts(profile))

        # 5b: Idle balance deployment  — Source: Change 4 (account roles)
        idle_rec = self._idle_balance_suggestion(profile)
        if idle_rec:
            recs.append(idle_rec)

        # ── Goal Layer ────────────────────────────────────────────────────────
        # Source: [9, 10, 12] Generate one or more recommendations per goal,
        # ordered by priority (already sorted by goal_analyzer).
        sip_amount = self._compute_sip(surplus)
        goals = profile.get("goals", [])

        for goal in goals:
            goal_recs = self._goal_recommendations(goal, profile, surplus, sip_amount, equity_cap)
            recs.extend(goal_recs)

        # If no goals at all — conservative start (fallback)
        if not goals:
            recs.append(self._conservative_start(profile, surplus))

        # ── Layer 6: Debt Optimisation ─────────────────────────────────────────
        # Source: [14] Prepaying a high-rate loan saves more than most FDs earn.
        # Only run when DTI < 50% (user is not already in the debt-reduction branch).
        if dti < DTI_STRESSED:
            debt_opt = self._debt_optimisation(profile, surplus)
            if debt_opt:
                recs.append(debt_opt)

        # Deduplicate by recommendation_id (Layer 3 and Goal Layer may both suggest EF)
        recs = _deduplicate(recs)

        # ── 3.1 Monthly Expense Integration ────────────────────────────────────
        # Weave expense context into SIP/investment recommendation reasons.
        if expense_ctx["high_expense"]:
            recs = self._apply_expense_personalization(recs, expense_ctx)

        return self._finalize({
            "suppressed":       False,
            "user_id":          user_id,
            "financial_health": financial_health,
            "wealth_position":  wealth_position,
            "recommendations":  recs,
            "goal_summaries":   goal_summaries,
            "disclaimer":       DISCLAIMER,
        })

    # ── Layer helpers ──────────────────────────────────────────────────────────

    def _expense_optimization(self, profile: dict) -> dict | None:
        """
        Layer 1 fallback: when no surplus exists, suggest expense review.
        Source: [13] 50/30/20 rule — identify which bucket is overflowing.
        """
        breakdown = profile.get("spending_breakdown", {})
        income    = profile.get("monthly_income", 0.0)
        if income <= 0:
            return None

        needs_pct  = breakdown.get("needs",  0.0)
        wants_pct  = breakdown.get("wants",  0.0)

        # Identify the worst offending category
        if needs_pct > 0.50:
            detail = f"Essential expenses are {needs_pct*100:.0f}% of income (50/30/20 target: 50%)."
        elif wants_pct > 0.30:
            detail = f"Discretionary spending is {wants_pct*100:.0f}% of income (50/30/20 target: 30%)."
        else:
            detail = "Total expenses exceed income. Review all spending categories."

        return {
            "recommendation_id": "expense_optimization",
            "recommendation":    "Reduce Monthly Expenses",
            "product":           "Budgeting Review",
            "amount":            0,
            "tenure":            "Ongoing",
            "reason": (
                f"Monthly expenses exceed income — no investable surplus. {detail} "
                "Reducing expenses is the first step before any investment decision."
            ),
            "confidence":       0.90,
            "expected_benefit": "Create investable surplus for wealth building",
            "priority":         "high",
            "source":           "[13] Elizabeth Warren 50/30/20 Rule",
        }

    def _debt_reduction(self, profile: dict) -> dict | None:
        """
        Layer 2: when DTI > 50%, focus all surplus on highest-rate loan.
        Source: [11] RBI — no growth investing above DTI 50%.
        """
        dti           = profile.get("debt_ratio", 0.0)
        surplus       = profile.get("investable_surplus", 0.0)
        high_rate     = profile.get("high_rate_loans", [])
        monthly_income = profile.get("monthly_income", 0.0)

        target_loan = high_rate[0] if high_rate else None
        prepay_amt  = _round_to_hundred(surplus * 0.50) if surplus > 0 else 0

        reason = (
            f"Debt-to-income ratio is {dti*100:.0f}% — above the RBI stress threshold of 50%. "
            "Growth investing is not advisable until the debt burden is reduced."
        )
        if target_loan:
            reason += (
                f" Priority target: {target_loan['loan_type'].title()} Loan "
                f"at {target_loan['interest_rate']}% — highest cost debt."
            )

        if prepay_amt <= 0:
            return None

        return {
            "recommendation_id": "debt_reduction_stressed",
            "recommendation":    "Debt Reduction — Priority Action",
            "product":           f"{target_loan['loan_type'].title()} Loan Prepayment" if target_loan else "Loan Prepayment",
            "amount":            prepay_amt,
            "tenure":            "Monthly additional payment",
            "reason":            reason,
            "confidence":        0.93,
            "expected_benefit": (
                f"Reduces DTI from {dti*100:.0f}% toward the 35% healthy threshold. "
                "Unlocks capacity for wealth building once DTI normalises."
            ),
            "priority":  "high",
            "source":    "[11] RBI Digital Lending Directions 2025",
        }

    def _fd_maturity_alerts(self, profile: dict) -> list[dict]:
        """
        Layer 5a: FDs maturing within 90 days — alert to reinvest, not idle.
        Source: [22] Avoid idle funds losing purchasing power to inflation.
        """
        calendar = profile.get("maturity_calendar", [])
        alerts   = []

        for entry in calendar:
            days = entry.get("days_to_maturity", 9999)
            if days > FD_MATURITY_ALERT_DAYS:
                break  # already sorted soonest-first by account_analyzer

            principal = entry.get("principal", 0)
            rate      = entry.get("interest_rate", 0)
            dep_type  = entry.get("deposit_type", "FD")

            if principal <= 0:
                continue

            alerts.append({
                "recommendation_id": f"fd_reinvest_{entry.get('deposit_id', 'unknown')}",
                "recommendation":    f"{dep_type} Reinvestment Alert",
                "product":           "Fixed Deposit Renewal",
                # int-cast: principal arrives from the AA feed and may be a float
                # (e.g. 100000.0). The frontend contract pins amount to int, so we
                # normalise here rather than leak a float. See _finalize() guard.
                "amount":            int(round(principal)),
                "tenure":            f"Maturing in {days} days",
                "reason": (
                    f"Your {_fmt_inr(principal)} {dep_type} at {rate}% matures in {days} days. "
                    "Reinvesting promptly avoids idle cash losing value to inflation."
                ),
                "confidence":       0.90,
                "expected_benefit": f"Continuous interest accumulation on {_fmt_inr(principal)}",
                "priority":         "high" if days <= 30 else "medium",
                "source":           "[22] RBI Product Awareness Norms",
            })

        return alerts

    def _idle_balance_suggestion(self, profile: dict) -> dict | None:
        """
        Layer 5b: detect idle balances and suggest deployment to FD.
        Source: Change 4 (account roles) + [8] Virginia Tech.

        Idle balance = savings/current balance above 1-month emergency buffer.
        Only suggest if idle amount exceeds 2x monthly expenses.
        """
        idle_total = profile.get("total_idle_balance", 0.0)
        expenses   = profile.get("monthly_expenses", 0.0)

        if idle_total <= 0 or expenses <= 0:
            return None

        # Suggest only if the idle amount is worth moving
        if idle_total < expenses * IDLE_TO_FD_MULTIPLIER:
            return None

        # Conservative deployment: move 50% to FD, keep rest liquid
        fd_amount = _round_to_hundred(idle_total * 0.50)
        if fd_amount < 5_000:
            return None

        # Estimate interest at 7% p.a. (typical PSB FD rate) for 6 months
        est_interest = round(fd_amount * 0.07 * (6 / 12))

        account_roles = profile.get("account_roles", [])
        idle_accounts = [
            a["account_id"] for a in account_roles
            if a.get("inferred_role") == "idle"
        ]
        account_context = f" (accounts: {', '.join(idle_accounts)})" if idle_accounts else ""

        return {
            "recommendation_id": "idle_balance_fd",
            "recommendation":    "Deploy Idle Savings to Fixed Deposit",
            "product":           "Fixed Deposit",
            "amount":            fd_amount,
            "tenure":            "6 months",
            "reason": (
                f"You have {_fmt_inr(idle_total)} sitting idle in your savings "
                f"account{account_context} beyond your emergency buffer. "
                f"Moving {_fmt_inr(fd_amount)} to a 6-month FD at ~7% p.a. "
                f"would earn approximately {_fmt_inr(est_interest)} in interest, "
                "instead of earning near-zero in a savings account."
            ),
            "confidence":       0.87,
            "expected_benefit": f"~{_fmt_inr(est_interest)} interest over 6 months",
            "priority":         "medium",
            "source":           "[8] Virginia Tech AAEC-184",
        }

    def _goal_recommendations(
        self,
        goal:       dict,
        profile:    dict,
        surplus:    float,
        sip_amount: int,
        equity_cap: float,
    ) -> list[dict]:
        """
        Generate 1–2 recommendations for a single goal.
        Source: [9, 10, 12] — SIP golden rules, MF personalisation, industry report.
        """
        goal_type      = goal.get("goal_type", "custom")
        gap            = goal.get("gap", 0.0)
        months_rem     = goal.get("months_remaining", 999)
        monthly_req    = goal.get("monthly_required", 0.0)
        completion_pct = goal.get("completion_pct", 0.0)
        feasibility    = goal.get("feasibility", "achievable")
        priority       = goal.get("priority", "medium")
        target_amount  = goal.get("target_amount", 0.0)

        if gap <= 0:
            # Goal already achieved — no recommendation needed
            return []

        recs = []

        if goal_type == "emergency_fund":
            ef_deposit = min(gap, surplus * 6)
            ef_deposit  = _round_to_hundred(ef_deposit)
            if ef_deposit > 0:
                recs.append({
                    "recommendation_id": "emergency_fund_goal",
                    "recommendation":    "Emergency Fund",
                    "product":           "Liquid Fixed Deposit",
                    "amount":            ef_deposit,
                    "tenure":            "No lock-in",
                    "reason": (
                        f"You have completed {completion_pct:.1f}% of your emergency fund goal "
                        f"({_fmt_inr(target_amount)} target). Gap remaining: {_fmt_inr(gap)}. "
                        "Liquid FD earns interest while keeping funds accessible within 1–2 days."
                    ),
                    "confidence":       0.95,
                    "expected_benefit": f"Close {_fmt_inr(gap)} emergency fund gap",
                    "priority":         priority,
                    "source":           "[8] Virginia Tech AAEC-184",
                })

        elif goal_type in ("education", "vacation", "custom"):
            # Medium-horizon goal: capital-safe FD + optional debt SIP
            fd_amount = _round_to_hundred(min(monthly_req * 3, surplus * 3))
            if fd_amount > 0:
                # Estimate at 7% for horizon in years
                horizon_years = round(months_rem / 12, 1)
                est_maturity  = round(fd_amount * (1 + 0.07) ** horizon_years)
                recs.append({
                    "recommendation_id": f"{goal_type}_fd",
                    "recommendation":    f"{goal_type.replace('_',' ').title()} Corpus",
                    "product":           "Fixed Deposit",
                    "amount":            fd_amount,
                    "tenure":            f"{horizon_years:.0f} year{'s' if horizon_years != 1 else ''}",
                    "reason": (
                        f"Goal: {_fmt_inr(target_amount)} by {goal.get('target_date', 'target date')} "
                        f"({months_rem} months). {completion_pct:.1f}% complete. "
                        f"Capital-safe FD for {horizon_years:.0f}-year horizon."
                    ),
                    "confidence":       0.85,
                    "expected_benefit": f"~{_fmt_inr(est_maturity)} at maturity (est. 7% p.a.)",
                    "priority":         priority,
                    "feasibility_note": feasibility,
                    "source":           "[8] Virginia Tech AAEC-184",
                })

            if surplus > SECONDARY_SIP_MIN_SURPLUS and equity_cap > 0.20:
                recs.append({
                    "recommendation_id": f"{goal_type}_sip",
                    "recommendation":    f"{goal_type.replace('_',' ').title()} SIP",
                    "product":           "Debt Mutual Fund (SIP)",
                    "amount":            sip_amount,
                    "tenure":            "Monthly SIP",
                    "reason": (
                        f"Stable returns with lower volatility than equity. "
                        f"Complements the FD corpus for the {goal_type.replace('_',' ')} goal."
                    ),
                    "confidence":       0.80,
                    "expected_benefit": "Steady corpus growth alongside FD",
                    "priority":         "medium",
                    "source":           "[9] Value Research SIP Golden Rules",
                })

        elif goal_type == "home_purchase":
            # Long-horizon: balanced MF SIP + parallel liquid buffer
            est_corpus_10yr = round(sip_amount * 12 * 10 * 1.5)
            recs.append({
                "recommendation_id": "home_purchase_sip",
                "recommendation":    "Home Purchase SIP",
                "product":           "Balanced Mutual Fund (SIP)",
                "amount":            sip_amount,
                "tenure":            "Monthly SIP",
                "reason": (
                    f"Goal: {_fmt_inr(target_amount)} down payment. "
                    f"{months_rem} months remaining. {completion_pct:.1f}% complete. "
                    "Rupee cost averaging over a 5–10 year horizon reduces timing risk."
                ),
                "confidence":       0.85,
                "expected_benefit": f"Est. {_fmt_inr(est_corpus_10yr)} corpus over 10 years",
                "priority":         priority,
                "feasibility_note": feasibility,
                "source":           "[10] LinkedIn — Personalising MF Recommendations",
            })
            # Parallel liquid buffer if emergency fund is still incomplete
            ef_gap = profile.get("emergency_fund_gap", 0.0)
            if ef_gap > 0:
                rd_amount = _round_to_hundred(surplus * 0.15)
                if rd_amount >= 500:
                    recs.append({
                        "recommendation_id": "home_purchase_parallel_rd",
                        "recommendation":    "Parallel Safety Net",
                        "product":           "Recurring Deposit",
                        "amount":            rd_amount,
                        "tenure":            "12 months",
                        "reason": (
                            "Build liquid buffer in parallel while the SIP grows your home purchase corpus. "
                            f"Emergency fund gap: {_fmt_inr(ef_gap)}."
                        ),
                        "confidence":       0.80,
                        "expected_benefit": "Liquid backup for unexpected needs",
                        "priority":         "medium",
                        "source":           "[8] Virginia Tech AAEC-184",
                    })

        elif goal_type == "retirement":
            # Long-horizon: equity-leaning SIP + optional ELSS for tax benefit
            equity_sip = int(sip_amount * equity_cap)
            if equity_sip < SIP_FLOOR_INR:
                equity_sip = SIP_FLOOR_INR

            recs.append({
                "recommendation_id": "retirement_sip",
                "recommendation":    "Retirement SIP",
                "product":           "Equity Mutual Fund (SIP)",
                "amount":            equity_sip,
                "tenure":            "Monthly SIP",
                "reason": (
                    f"Goal: {_fmt_inr(target_amount)}. "
                    f"{completion_pct:.1f}% complete ({months_rem} months remaining). "
                    "Long horizon absorbs equity volatility. Systematic investing maximises compounding."
                ),
                "confidence":       0.88,
                "expected_benefit": "Compounding over 10+ years builds significant retirement corpus",
                "priority":         priority,
                "feasibility_note": feasibility,
                "source":           "[9] Value Research SIP Golden Rules, [12] ICICI Prudential Report",
            })

            # ELSS: tax-saving + retirement growth. Only if surplus > 8k (meaningful benefit).
            if surplus > 8_000:
                elss_amount = min(_round_to_hundred(surplus * 0.10), 5_000)
                annual_elss = elss_amount * 12
                tax_savings = min(annual_elss, 150_000)
                recs.append({
                    "recommendation_id": "retirement_elss",
                    "recommendation":    "Tax-Saving SIP",
                    "product":           "ELSS Mutual Fund (SIP) — 3-year lock-in",
                    "amount":            elss_amount,
                    "tenure":            "Monthly SIP — 3-year lock-in",
                    "reason": (
                        "ELSS qualifies for Section 80C deduction up to ₹1,50,000/year "
                        "while also building your retirement corpus through equity exposure."
                    ),
                    "confidence":       0.83,
                    "expected_benefit": f"Up to {_fmt_inr(tax_savings)} tax benefit per year under Section 80C",
                    "priority":         "medium",
                    "source":           "[12] ICICI Prudential MF Industry Report",
                })

        elif goal_type in ("debt_payoff", "business_expansion"):
            # Debt payoff and business expansion: channel surplus to target
            channel_amount = _round_to_hundred(min(monthly_req, surplus * 0.50))
            if channel_amount > 0:
                recs.append({
                    "recommendation_id": f"{goal_type}_channel",
                    "recommendation":    goal_type.replace("_", " ").title(),
                    "product":           "Recurring Deposit / Direct Prepayment",
                    "amount":            channel_amount,
                    "tenure":            "Monthly",
                    "reason": (
                        f"Goal: {_fmt_inr(target_amount)}. "
                        f"{completion_pct:.1f}% complete ({months_rem} months remaining). "
                        f"Monthly required: {_fmt_inr(monthly_req)}. "
                        f"Channelling {_fmt_inr(channel_amount)}/month from investable surplus."
                    ),
                    "confidence":       0.82,
                    "expected_benefit": f"Closes {_fmt_inr(gap)} gap over {months_rem} months",
                    "priority":         priority,
                    "feasibility_note": feasibility,
                    "source":           "[8] Virginia Tech AAEC-184",
                })

        return recs

    def _conservative_start(self, profile: dict, surplus: float) -> dict:
        """
        Fallback when no goals are defined: liquid FD to begin wealth journey.
        Source: [8] — build liquidity first.
        """
        amount = _round_to_hundred(surplus * 2)
        return {
            "recommendation_id": "conservative_start",
            "recommendation":    "Conservative Start — Build Liquidity First",
            "product":           "Liquid Fixed Deposit",
            "amount":            max(amount, 1_000),
            "tenure":            "6 months",
            "reason": (
                "No financial goals defined. Starting with a short-duration liquid FD "
                "builds a safe base and earns interest while you decide on longer-term goals."
            ),
            "confidence":       0.75,
            "expected_benefit": "Safe base to plan from; earns ~6–7% p.a.",
            "priority":         "low",
            "source":           "[8] Virginia Tech AAEC-184",
        }

    def _debt_optimisation(self, profile: dict, surplus: float) -> dict | None:
        """
        Layer 6: high-rate loan prepayment suggestion.
        Source: [14] Indian Wealth Mgmt Ratios — prepaying >10% loan beats most FDs.
        Only fires when DTI < 50% (otherwise Layer 2 already handled it).
        """
        high_rate = profile.get("high_rate_loans", [])
        if not high_rate or surplus < 2_000:
            return None

        top_loan   = high_rate[0]  # already sorted by interest_rate desc
        loan_rate  = top_loan.get("interest_rate", 0.0)
        if loan_rate <= HIGH_RATE_THRESHOLD_PCT:
            return None

        prepay = _round_to_hundred(surplus * 0.15)
        if prepay < 500:
            return None

        return {
            "recommendation_id": "debt_optimisation",
            "recommendation":    "Loan Prepayment — Debt Optimisation",
            "product":           f"{top_loan['loan_type'].title()} Loan Prepayment",
            "amount":            prepay,
            "tenure":            "One-time or monthly additional payment",
            "reason": (
                f"Your {top_loan['loan_type']} loan at {loan_rate}% interest costs more "
                f"than most FDs or debt funds earn. Prepaying {_fmt_inr(prepay)}/month "
                "reduces the outstanding principal, cutting total interest paid."
            ),
            "confidence":       0.92,
            "expected_benefit": (
                f"Interest savings exceed equivalent FD earnings at current {loan_rate}% rate"
            ),
            "priority":         "medium",
            "source":           "[14] Indian Wealth Management Personal Financial Ratios",
        }

    # ── Internal computation helpers ───────────────────────────────────────────

    def _compute_equity_cap(self, profile: dict) -> float:
        """
        Derive maximum equity allocation based on age and risk tolerance.
        Source: [10] Personalising MF Recommendations, [14] Indian Wealth Mgmt Ratios.
        """
        age            = profile.get("age", 30)
        risk_tolerance = profile.get("risk_profile", "moderate")

        if age > 55:
            base_cap = EQUITY_CAP_BY_AGE["senior"]
        elif age > 40:
            base_cap = EQUITY_CAP_BY_AGE["mid"]
        else:
            base_cap = EQUITY_CAP_BY_AGE["young"]

        modifier = RISK_EQUITY_MODIFIER.get(risk_tolerance, 1.0)
        return min(base_cap * modifier, 1.0)

    def _compute_sip(self, surplus: float) -> int:
        """
        Compute recommended SIP amount from investable surplus.
        Source: [9] Value Research — 20–30% of investable surplus.
        Rounded to nearest ₹100. Floored at ₹500, capped at ₹25,000.
        """
        raw = surplus * SIP_RATE_MIN
        return max(SIP_FLOOR_INR, min(SIP_CAP_INR, _round_to_hundred(raw)))

    def _compute_financial_health(self, profile: dict) -> dict:
        """
        Compute a composite financial health score (0–100) with component breakdown.
        Source: [8] Virginia Tech, [14] Indian Wealth Mgmt Ratios, RBI DTI norms.

        Score components:
            Emergency Readiness (25 pts) — months_of_runway / 4 months target
            Debt Burden         (25 pts) — 1 - min(dti / 0.50, 1.0)
            Savings Rate        (25 pts) — min(savings_rate / 0.20, 1.0)
            Wealth Buffer       (25 pts) — min(net_worth / (monthly_income * 12), 1.0)
        """
        income          = profile.get("monthly_income", 1.0) or 1.0
        runway          = profile.get("months_of_runway", 0.0)
        dti             = profile.get("debt_ratio", 0.0)
        savings_rate    = profile.get("savings_rate", 0.0)
        net_worth       = profile.get("net_worth", 0.0)

        # Emergency readiness (target: 4 months)
        emergency_score = min(runway / EMERGENCY_FUND_MONTHS, 1.0) * 25

        # Debt burden (target: DTI < 50%)
        debt_score = (1.0 - min(dti / DTI_STRESSED, 1.0)) * 25

        # Savings rate (target: 20%)  [8]
        savings_score = min(savings_rate / 0.20, 1.0) * 25

        # Wealth buffer (target: 1 year of income in net worth)
        # Clamped to 0 when net_worth is negative (liabilities exceed assets).
        annual_income  = income * 12
        wealth_score   = max(0.0, min(net_worth / annual_income, 1.0)) * 25 if annual_income > 0 else 0.0

        total = round(emergency_score + debt_score + savings_score + wealth_score, 1)
        total = max(0.0, min(100.0, total))

        return {
            "score":      total,
            "grade":      _health_grade(total),
            "components": {
                "emergency_readiness": round(emergency_score, 1),
                "debt_management":     round(debt_score, 1),
                "savings_discipline":  round(savings_score, 1),
                "wealth_buffer":       round(wealth_score, 1),
            },
        }

    def _build_goal_summaries(self, profile: dict) -> list[dict]:
        """
        Lightweight summaries of each goal's status — always returned,
        even when advice is suppressed by the fraud gate.
        """
        goals = profile.get("goals", [])
        summaries = []
        for g in goals:
            summaries.append({
                "goal_type":      g.get("goal_type"),
                "target_amount":  g.get("target_amount"),
                "gap":            g.get("gap"),
                "completion_pct": g.get("completion_pct"),
                "months_remaining": g.get("months_remaining"),
                "feasibility":    g.get("feasibility"),
                "priority":       g.get("priority"),
            })
        return summaries

    # ── 3.2 Net Worth exposure ─────────────────────────────────────────────────

    def _build_wealth_position(self, profile: dict) -> dict:
        """
        Expose Assets ↓ Liabilities ↓ Net Worth to the frontend output.

        All three figures are already computed by FinancialProfileBuilder; this
        surfaces them in the wealth engine output so the frontend does not need
        to reach back into the raw profile. Always present, on every path
        (including fraud-suppressed), like goal_summaries and financial_health.
        """
        total_assets      = float(profile.get("total_assets", 0.0))
        total_liabilities = float(profile.get("total_liabilities", 0.0))
        net_worth         = float(profile.get("net_worth", total_assets - total_liabilities))
        return {
            "total_assets":      round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "net_worth":         round(net_worth, 2),
        }

    # ── 3.1 Monthly Expense Integration ────────────────────────────────────────

    def _expense_context(self, profile: dict) -> dict:
        """
        Derive an expense-to-income signal used to personalise advice.

        Returns a small context dict:
            expense_ratio  float  monthly_expenses / monthly_income (0.0 if no income)
            high_expense   bool   True when expense_ratio > HIGH_EXPENSE_RATIO
            wants_pct      float  discretionary spend as a fraction of income
        """
        income   = profile.get("monthly_income", 0.0) or 0.0
        expenses = profile.get("monthly_expenses", 0.0) or 0.0
        ratio    = (expenses / income) if income > 0 else 0.0
        wants    = profile.get("spending_breakdown", {}).get("wants", 0.0)
        return {
            "expense_ratio": round(ratio, 3),
            "high_expense":  ratio > HIGH_EXPENSE_RATIO,
            "wants_pct":     wants,
        }

    def _apply_expense_personalization(self, recs: list[dict], ctx: dict) -> list[dict]:
        """
        Append an expense-awareness sentence to SIP / investment recommendation
        reasons when the user's expense ratio is high. Amounts and IDs are left
        untouched (so existing explainer templates stay valid) — only the free-text
        'reason' is enriched for more personalised advice.
        """
        pct = ctx["expense_ratio"] * 100
        note = (
            f" Note: your monthly expenses are {pct:.0f}% of income. "
            "Trimming discretionary spending would free up more surplus to raise "
            "this contribution."
        )
        for rec in recs:
            # Only enrich growth/SIP recommendations — not debt or emergency-fund recs.
            if "SIP" in rec.get("product", "") or rec.get("recommendation_id", "").endswith("_sip"):
                rec["reason"] = rec.get("reason", "") + note
        return recs

    # ── 3.3 Mutual Fund Only — product guard ───────────────────────────────────

    def _finalize(self, result: dict) -> dict:
        """
        Final gate applied to every return path: assert every emitted product is
        on the APPROVED_PRODUCTS whitelist before the result leaves the engine.
        This structurally guarantees no stock pick / specific fund name / non-MF
        growth product can ever ship, even after future edits.

        Also enforces the frontend data-type contract: recommendation `amount` is
        pinned to `int` in schemas.py. Any recommendation whose amount arrives as a
        float (e.g. an FD principal fed through from the AA layer as 100000.0) is
        coerced to int here so the JSON sent to the frontend never mixes int/float
        for the same field. Pydantic's lax mode would hide this — the frontend
        would not.
        """
        recs = result.get("recommendations", [])
        for rec in recs:
            amt = rec.get("amount")
            if isinstance(amt, float):
                rec["amount"] = int(round(amt))
        _assert_products_approved(recs)
        return result


# ─── Private helpers ──────────────────────────────────────────────────

def _assert_products_approved(recs: list[dict]) -> None:
    """
    3.3 Mutual Fund Only guard. Raise if any recommendation uses a product
    outside the approved whitelist. Loan prepayment products are dynamic
    (e.g. "Personal Loan Prepayment"), so a "... Loan Prepayment" suffix is
    accepted in addition to exact whitelist membership.
    """
    for rec in recs:
        product = rec.get("product", "")
        if product in APPROVED_PRODUCTS:
            continue
        if product.endswith("Loan Prepayment"):
            continue
        raise ValueError(
            f"Disallowed product '{product}' in recommendation "
            f"'{rec.get('recommendation_id', '?')}' — not in APPROVED_PRODUCTS. "
            "Wealth engine is restricted to deposits, mutual-fund categories, "
            "loan prepayment, and budgeting guidance (no stocks / fund names)."
        )


def _round_to_hundred(amount: float) -> int:
    """Round to nearest ₹100 for clean recommendations."""
    return max(0, round(amount / 100) * 100)


def _fmt_inr(amount: float) -> str:
    """Format a rupee amount as ₹X,XX,XXX."""
    # Indian number format: 2,34,567
    amount = int(round(amount))
    if amount < 0:
        return f"-{_fmt_inr(-amount)}"
    if amount < 1_000:
        return f"Rs.{amount}"
    s = str(amount)
    if len(s) <= 3:
        return f"Rs.{s}"
    last3   = s[-3:]
    rest    = s[:-3]
    grouped = ",".join(rest[max(0, i - 2):i] for i in range(len(rest), 0, -2))
    return f"Rs.{grouped[::-1]},{last3}" if grouped else f"Rs.{last3}"


def _health_grade(score: float) -> str:
    """Convert numeric health score to letter grade."""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def _deduplicate(recs: list[dict]) -> list[dict]:
    """
    Remove duplicate recommendation_ids, keeping the first occurrence.
    Preserves insertion order. Used when Layer 3 (implicit EF) and
    the Goal Layer (explicit EF goal) both fire.
    """
    seen: set[str] = set()
    out:  list[dict] = []
    for rec in recs:
        rid = rec.get("recommendation_id", "")
        if rid not in seen:
            seen.add(rid)
            out.append(rec)
    return out
