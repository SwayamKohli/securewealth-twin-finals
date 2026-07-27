"""
Goal Analyzer — Aggregation Component
======================================
Handles: financial goal tracking, gap calculation, feasibility analysis.
Computes: progress, required monthly savings, feasibility, priority.

Called by FinancialProfileBuilder — not used standalone.
"""

from datetime import date

def analyze_goals(aa_data: dict, investable_surplus: float) -> dict:
    """
    Analyze user's financial goals and compute progress and feasibility.
    
    Returns:
        {
            "goals": [
                {
                    "goal_type":        str,
                    "target_amount":    float,
                    "target_date":      str,
                    "current_progress": float,
                    "gap":              float,
                    "completion_pct":   float,
                    "months_remaining": int,
                    "monthly_required": float,
                    "feasibility":      str, ("achievable" | "stretch" | "unrealistic")
                    "priority":         str, ("high" | "medium" | "low")
                }
            ],
            "has_emergency_fund_goal": bool,
            "total_goal_gap":          float,
        }
    """
    raw_goals = aa_data.get("goals", [])
    analyzed_goals = []
    
    has_emergency_fund = False
    total_gap = 0.0
    
    for g in raw_goals:
        goal_type = g.get("goal_type", "custom")
        target_amount = g.get("target_amount", 0.0)
        target_date_str = g.get("target_date")
        current_progress = g.get("current_progress", 0.0)
        
        if goal_type == "emergency_fund":
            has_emergency_fund = True
            
        gap = max(0.0, target_amount - current_progress)
        total_gap += gap
        
        completion_pct = round((current_progress / target_amount * 100), 1) if target_amount > 0 else 0.0
        months_remaining = _months_to_date(target_date_str)
        
        monthly_required = round(gap / months_remaining, 2) if months_remaining > 0 else gap
        
        # Feasibility check based on investable surplus
        if monthly_required <= investable_surplus * 0.30:
            feasibility = "achievable"
        elif monthly_required <= investable_surplus * 0.60:
            feasibility = "stretch"
        else:
            feasibility = "unrealistic"
            
        # Priority check based on timeline
        if goal_type == "emergency_fund":
            priority = "high"  # Emergency fund is always high priority
        elif months_remaining <= 12:
            priority = "high"
        elif months_remaining <= 36:
            priority = "medium"
        else:
            priority = "low"
            
        analyzed_goals.append({
            "goal_type":        goal_type,
            "target_amount":    target_amount,
            "target_date":      target_date_str,
            "current_progress": current_progress,
            "gap":              gap,
            "completion_pct":   completion_pct,
            "months_remaining": months_remaining,
            "monthly_required": monthly_required,
            "feasibility":      feasibility,
            "priority":         priority,
        })
        
    # Sort by priority (high -> medium -> low) then by months remaining
    priority_order = {"high": 0, "medium": 1, "low": 2}
    analyzed_goals.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["months_remaining"]))

    return {
        "goals": analyzed_goals,
        "has_emergency_fund_goal": has_emergency_fund,
        "total_goal_gap": total_gap,
    }

def _months_to_date(target_date_str: str | None) -> int:
    """
    Compute months from today to a target date.
    Returns 999 if missing/invalid.
    """
    if not target_date_str:
        return 999
    try:
        target = date.fromisoformat(target_date_str)
        delta_days = (target - date.today()).days
        if delta_days <= 0:
            return 0
        return max(1, delta_days // 30)
    except ValueError:
        return 999
