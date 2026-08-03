"""
Account Analyzer — Aggregation Component
==========================================
Handles: savings accounts, current accounts, fixed deposits, recurring deposits.
Computes: total liquid, total locked, maturity calendar.

Called by FinancialProfileBuilder — not used standalone.
"""

from datetime import date


def analyze_accounts(aa_data: dict) -> dict:
    """
    Compute totals from bank accounts and deposits.
    Also infers account roles (salary/savings/current) and idle balances.

    Returns:
        {
            "total":     float,  total assets across all account types
            "breakdown": {
                "bank_balances":       float,
                "fixed_deposits":      float,
                "recurring_deposits":  float,
            },
            "liquid_balance":   float,   savings + current (accessible cash)
            "locked_balance":   float,   FDs + RDs (not immediately liquid)
            "maturity_calendar": list,   [{deposit_id, deposit_type, principal, days_to_maturity}]
            "account_roles":    list,    [{account_id, account_type, inferred_role, balance, idle_balance}]
            "total_idle_balance": float, sum of idle balances across all liquid accounts
        }
    """
    accounts  = aa_data.get("accounts",  [])
    deposits  = aa_data.get("deposits",  [])
    
    # Needs income/expenses for idle balance and salary account detection
    monthly_income = aa_data.get("monthly_income", 0.0)
    monthly_expenses = aa_data.get("monthly_expenses", 0.0)
    # Cash is only "idle" once the emergency fund is genuinely covered.
    #
    # This reserved 1 month while every other part of the engine treats FOUR
    # months as the emergency target (EMERGENCY_FUND_MONTHS in wealth_engine and
    # profile_builder). With a 1-month buffer, a customer holding 3 months of
    # expenses was told to lock the surplus into a fixed deposit — money they
    # would need before the FD matured. Reserve the full target instead.
    EMERGENCY_FUND_MONTHS = 4.0
    emergency_buffer = monthly_expenses * EMERGENCY_FUND_MONTHS
    

    # Bank account balances
    bank_total  = sum(a["balance"] for a in accounts)
    liquid      = sum(
        a["balance"] for a in accounts
        if a["account_type"] in ("savings", "current")
    )

    # Deposits: split FD and RD
    fds = [d for d in deposits if d.get("deposit_type") == "FD"]
    rds = [d for d in deposits if d.get("deposit_type") == "RD"]

    fd_total = sum(d["principal"] for d in fds)
    rd_total = sum(d["principal"] for d in rds)

    total = bank_total + fd_total + rd_total

    # Account roles and idle balance logic
    account_roles = []
    total_idle_balance = 0.0

    for a in accounts:
        acc_type = a.get("account_type", "savings")
        balance = a.get("balance", 0.0)
        
        inferred_role = "savings"
        idle_balance = 0.0
        
        if acc_type in ("savings", "current"):
            idle_balance = max(0.0, balance - emergency_buffer)
        
        # Check for salary account (assuming credits might be passed or heuristic)
        monthly_credits = a.get("monthly_credits", 0.0)
        if monthly_credits > 0 and monthly_credits > (monthly_income * 0.80):
            inferred_role = "salary_account"
        elif acc_type == "current":
            inferred_role = "current"
        elif idle_balance > (monthly_expenses * 2):
            inferred_role = "idle"
            
        account_roles.append({
            "account_id": a.get("account_id"),
            "account_type": acc_type,
            "inferred_role": inferred_role,
            "balance": balance,
            "idle_balance": idle_balance,
        })
        total_idle_balance += idle_balance

    # Maturity calendar — useful for wealth engine's product awareness layer
    maturity_calendar = []
    for d in deposits:
        days = _days_to_maturity(d.get("maturity_date"))
        maturity_calendar.append({
            "deposit_id":       d["deposit_id"],
            "deposit_type":     d.get("deposit_type", "FD"),
            "principal":        d["principal"],
            "interest_rate":    d.get("interest_rate", 0),
            "days_to_maturity": days,
        })

    # Sort soonest first so wealth engine can easily find upcoming maturities
    maturity_calendar.sort(key=lambda x: x["days_to_maturity"])

    return {
        "total":    total,
        "breakdown": {
            "bank_balances":      bank_total,
            "fixed_deposits":     fd_total,
            "recurring_deposits": rd_total,
        },
        "liquid_balance":   liquid,
        "locked_balance":   fd_total + rd_total,
        "maturity_calendar": maturity_calendar,
        "account_roles":    account_roles,
        "total_idle_balance": total_idle_balance,
    }


def _days_to_maturity(maturity_date_str: str | None) -> int:
    """
    Compute calendar days from today to a deposit maturity date.
    Returns 9999 if maturity_date_str is missing/invalid (treat as far future).
    """
    if not maturity_date_str:
        return 9999
    try:
        maturity = date.fromisoformat(maturity_date_str)
        delta = (maturity - date.today()).days
        return max(0, delta)   # 0 if already matured
    except ValueError:
        return 9999
