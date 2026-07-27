"""
Cashflow Analyzer — Aggregation Component
==========================================
Handles: income detection, expense categorization, spending trends.
Computes: monthly surplus, savings rate, spending pattern verdict.

Sources:
  [13] Elizabeth Warren — 50/30/20 needs/wants/savings rule
  [8]  Virginia Tech AAEC-184 — ≥20% savings rate = healthy

Called by FinancialProfileBuilder — not used standalone.
"""


def analyze_cashflow(aa_data: dict) -> dict:
    """
    Compute income, expense, surplus, and spending quality metrics.

    Returns:
        {
            "monthly_income":   float,
            "monthly_expenses": float,
            "monthly_surplus":  float,   income - expenses
            "savings_rate":     float,   surplus / income (0–1)
            "spending_breakdown": {
                "needs_pct":   float,    % of income on essentials
                "wants_pct":   float,    % on discretionary
                "savings_pct": float,    % saved/invested
                "verdict":     str,      human-readable assessment
            },
        }
    """
    income   = aa_data.get("monthly_income",   0.0)
    expenses = aa_data.get("monthly_expenses", 0.0)
    surplus  = income - expenses

    savings_rate = surplus / income if income > 0 else 0.0

    spending = _analyze_spending_breakdown(income, aa_data.get("spending_breakdown", {}))

    return {
        "monthly_income":     income,
        "monthly_expenses":   expenses,
        "monthly_surplus":    surplus,
        "savings_rate":       round(savings_rate, 3),
        "spending_breakdown": spending,
    }


def _analyze_spending_breakdown(income: float, breakdown: dict) -> dict:
    """
    Classify spending against the 50/30/20 rule.
    Source: [13] Elizabeth Warren, *All Your Worth* (2005)

    needs  = essential (rent, EMIs, groceries, utilities)
    wants  = discretionary (dining, entertainment, subscriptions)
    savings= saved or invested
    """
    needs   = breakdown.get("needs",   0.0)
    wants   = breakdown.get("wants",   0.0)
    savings = breakdown.get("savings", 0.0)

    if income <= 0:
        return {
            "needs_pct":   0.0,
            "wants_pct":   0.0,
            "savings_pct": 0.0,
            "verdict":     "Income data unavailable",
        }

    needs_pct   = round(needs   / income * 100, 1)
    wants_pct   = round(wants   / income * 100, 1)
    savings_pct = round(savings / income * 100, 1)

    # Verdict logic — each condition ordered from worst to best [13][8]
    if income - needs - wants <= 0:
        verdict = "No savings capacity — expenses exceed income"
    elif savings_pct < 10:
        verdict = "Low savings rate — prioritise building an emergency fund first"
    elif needs_pct > 65:
        verdict = "Essential spending is high — review fixed commitments"
    elif needs_pct <= 50 and wants_pct <= 30 and savings_pct >= 20:
        verdict = "Healthy — aligned with 50/30/20 rule"
    elif savings_pct >= 20:
        verdict = "Good savings rate, but spending mix can be improved"
    else:
        verdict = "Moderate — room to improve savings rate"

    return {
        "needs_pct":   needs_pct,
        "wants_pct":   wants_pct,
        "savings_pct": savings_pct,
        "verdict":     verdict,
    }
