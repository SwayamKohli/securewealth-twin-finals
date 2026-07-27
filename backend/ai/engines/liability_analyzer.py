"""
Liability Analyzer — Aggregation Component
===========================================
Handles: all loan types, credit cards.
Computes: total EMI burden, DTI ratio, credit utilization, high-rate flags.

Sources:
  [8]  Virginia Tech AAEC-184 — DTI ≥ 20% flag, > 50% stressed
  RBI norms — DTI > 50% = high stress, no growth investing
  [23] RBI KYC 2024 — risk categorization thresholds

Called by FinancialProfileBuilder — not used standalone.
"""


def analyze_liabilities(aa_data: dict) -> dict:
    """
    Compute all debt-related metrics from AA data.

    Returns:
        {
            "total":     float,   total outstanding across all loans + credit card debt
            "breakdown": dict,    outstanding by loan type + credit_card_debt
            "total_emi": float,   sum of all monthly EMI obligations
            "debt_ratio": float,  total_emi / monthly_income  (DTI)
            "credit_utilization": float,  cc_outstanding / cc_limit (0–1)
            "high_rate_loans": list,  [{loan_id, loan_type, interest_rate, outstanding_amount}]
                                      sorted by rate desc — for debt reduction suggestions
            "debt_stress": str,   "none" | "moderate" | "stressed"
        }
    """
    loans   = aa_data.get("loans",  [])
    cards   = aa_data.get("cards",  [])
    income  = aa_data.get("monthly_income", 0.0)

    # ── Loan totals ─────────────────────────────────────────────────────────────
    breakdown:  dict[str, float] = {}
    total_emi = 0.0

    for loan in loans:
        loan_type = loan.get("loan_type", "other")
        key = f"{loan_type}_loan"
        outstanding = loan.get("outstanding_amount", 0.0)
        emi         = loan.get("emi", 0.0)

        breakdown[key] = breakdown.get(key, 0.0) + outstanding
        total_emi      += emi

    # ── Credit card debt ────────────────────────────────────────────────────────
    credit_cards   = [c for c in cards if c.get("card_type") == "credit"]
    cc_outstanding = sum(c.get("outstanding_balance", 0.0) for c in credit_cards)
    cc_limit       = sum(c.get("credit_limit",        0.0) for c in credit_cards)

    breakdown["credit_card_debt"] = cc_outstanding

    total = sum(breakdown.values())

    # ── Ratios ──────────────────────────────────────────────────────────────────
    # Debt-to-income (DTI) — monthly EMIs vs monthly income
    # RBI norm: > 50% = high stress
    dti = total_emi / income if income > 0 else 1.0

    # Credit card utilization — anything > 30% is a mild flag
    cc_utilization = cc_outstanding / cc_limit if cc_limit > 0 else 0.0

    # ── High-rate loans (for debt reduction layer in wealth engine) ─────────────
    # A loan above 10% interest rate earns you more by prepaying than investing
    high_rate = [
        {
            "loan_id":           l.get("loan_id", ""),
            "loan_type":         l.get("loan_type", ""),
            "interest_rate":     l.get("interest_rate", 0.0),
            "outstanding_amount": l.get("outstanding_amount", 0.0),
            "emi":               l.get("emi", 0.0),
        }
        for l in loans if l.get("interest_rate", 0) > 10.0
    ]
    high_rate.sort(key=lambda x: x["interest_rate"], reverse=True)

    # ── Debt stress classification ──────────────────────────────────────────────
    if dti > 0.50:
        stress = "stressed"
    elif dti > 0.35:
        stress = "moderate"
    else:
        stress = "none"

    return {
        "total":               total,
        "breakdown":           breakdown,
        "total_emi":           round(total_emi, 2),
        "debt_ratio":          round(dti, 3),
        "credit_utilization":  round(cc_utilization, 3),
        "high_rate_loans":     high_rate,
        "debt_stress":         stress,
    }
