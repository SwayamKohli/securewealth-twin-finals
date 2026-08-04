"""
api/admin.py — Admin Dashboard backend APIs (task 2.7)
======================================================
Powers the STANDALONE web-based Admin Dashboard (admin-dashboard/).

Endpoints
    GET /api/v1/admin/stats          — decision counts, risk stats, volumes
    GET /api/v1/admin/audit          — audit records w/ search + filters
    GET /api/v1/admin/alerts         — live WARN/CHALLENGE/BLOCK feed (polling)
    GET /api/v1/admin/investments    — investment history w/ filters

Auth: X-Admin-Key header checked against settings.ADMIN_API_KEY.
(Demo-grade admin auth — customers use JWT; admins are out-of-band.)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_db
from models.audit import AuditLog
from models.transaction import Transaction
from models.user import User

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin Dashboard"],
)

ALERT_DECISIONS = ("WARN", "CHALLENGE", "BLOCK")


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key.",
        )


def _audit_to_dict(a: AuditLog) -> dict:
    return {
        "audit_id": str(a.audit_id),
        "chain_index": a.chain_index,
        "transaction_id": a.transaction_id,
        "user_id": a.user_id,
        "device_id": a.device_id,
        "account_id": a.account_id,
        "event_type": a.event_type,
        "final_decision": a.final_decision,
        "risk_score": a.risk_score,
        "amount": a.amount,
        "channel": a.channel,
        "ai_status": a.ai_status,
        "ai_confidence": a.ai_confidence,
        "unknown_risk_applied": a.unknown_risk_applied,
        "challenge_required": a.challenge_required,
        "challenge_type": a.challenge_type,
        "audit_note": a.audit_note,
        "record_status": a.record_status,
        "current_hash": a.current_hash,
        "previous_hash": a.previous_hash,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("/stats", dependencies=[Depends(require_admin)])
def admin_stats(db: Session = Depends(get_db)):
    """Headline numbers for the dashboard cards."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    decision_counts = dict(
        db.query(AuditLog.final_decision, func.count(AuditLog.audit_id))
        .group_by(AuditLog.final_decision)
        .all()
    )
    total_audits = sum(decision_counts.values())
    avg_risk = db.query(func.avg(AuditLog.risk_score)).scalar() or 0
    last_24h = (
        db.query(func.count(AuditLog.audit_id))
        .filter(AuditLog.created_at >= day_ago)
        .scalar()
        or 0
    )
    blocked_amount = (
        db.query(func.coalesce(func.sum(AuditLog.amount), 0))
        .filter(AuditLog.final_decision == "BLOCK")
        .scalar()
    )
    invested_amount = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.status == "SUCCESS")
        .scalar()
    )

    return {
        "generated_at": now.isoformat(),
        "total_audit_records": total_audits,
        "decisions": {
            d: decision_counts.get(d, 0)
            for d in ("ALLOW", "WARN", "CHALLENGE", "BLOCK")
        },
        "average_risk_score": round(float(avg_risk), 1),
        "audits_last_24h": last_24h,
        "blocked_amount": float(blocked_amount or 0),
        "total_invested_amount": float(invested_amount or 0),
    }


# ── Red Team / Adversarial Resilience Console ────────────────────────────────

@router.get("/redteam/scenarios", dependencies=[Depends(require_admin)])
def redteam_scenarios():
    """Attack scenarios available to run against the live system."""
    from services.redteam_service import SCENARIOS

    return {"enabled": settings.REDTEAM_ENABLED, "scenarios": SCENARIOS}


@router.post("/redteam/run/{scenario_id}", dependencies=[Depends(require_admin)])
def redteam_run(scenario_id: str, db: Session = Depends(get_db)):
    """
    Execute one attack scenario for real and return a step-by-step result.

    These are genuine attacks against the running system (direct database
    writes, live transactions, live engine calls) — nothing is simulated at
    the result level.
    """
    if not settings.REDTEAM_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Red Team console is disabled (set REDTEAM_ENABLED=true).",
        )

    from services.redteam_service import RedTeamService

    return RedTeamService(db).run(scenario_id)


@router.get("/security-events", dependencies=[Depends(require_admin)])
def admin_security_events(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Tamper and recovery events — the audit system defending itself.

    Powers the dashboard's "Audit Defence" panel: any detected tampering and
    every self-healing recovery, newest first.
    """
    events = (
        db.query(AuditLog)
        .filter(AuditLog.event_type.in_(("TAMPER_EVENT", "RECOVERY_EVENT")))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "total": len(events),
        "events": [
            {
                "audit_id": str(e.audit_id),
                "event_type": e.event_type,
                "audit_note": e.audit_note,
                "record_status": e.record_status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/audit", dependencies=[Depends(require_admin)])
def admin_audit_search(
    search: str | None = Query(default=None, description="Matches txn/user/audit id or note"),
    decision: str | None = Query(default=None),
    min_risk: int | None = Query(default=None, ge=0, le=100),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Searchable, filterable audit log (task 2.7: Search + Filters)."""
    q = db.query(AuditLog)

    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                AuditLog.transaction_id.ilike(like),
                AuditLog.user_id.ilike(like),
                AuditLog.audit_id.ilike(like),
                AuditLog.audit_note.ilike(like),
                AuditLog.challenge_type.ilike(like),
            )
        )
    if decision:
        q = q.filter(AuditLog.final_decision == decision.upper())
    if min_risk is not None:
        q = q.filter(AuditLog.risk_score >= min_risk)
    if from_date:
        q = q.filter(AuditLog.created_at >= from_date)
    if to_date:
        q = q.filter(AuditLog.created_at <= to_date)

    total = q.count()
    records = (
        q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": [_audit_to_dict(a) for a in records],
    }


@router.get("/alerts", dependencies=[Depends(require_admin)])
def admin_live_alerts(
    since: datetime | None = Query(
        default=None, description="Only alerts after this time (for polling)."
    ),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Live fraud feed: WARN / CHALLENGE / BLOCK decisions, newest first."""
    q = db.query(AuditLog).filter(AuditLog.final_decision.in_(ALERT_DECISIONS))
    if since:
        q = q.filter(AuditLog.created_at > since)
    records = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "alerts": [_audit_to_dict(a) for a in records],
    }


@router.get("/investments", dependencies=[Depends(require_admin)])
def admin_investments(
    decision: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, description="Fund name search"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Investment history across all customers (task 2.7)."""
    q = db.query(Transaction, User.full_name, User.customer_id).join(
        User, Transaction.user_id == User.user_id
    )
    if decision:
        q = q.filter(Transaction.decision == decision.upper())
    if status_filter:
        q = q.filter(Transaction.status == status_filter.upper())
    if search:
        q = q.filter(Transaction.merchant_name.ilike(f"%{search}%"))

    total = q.count()
    rows = (
        q.order_by(Transaction.transaction_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "investments": [
            {
                "transaction_id": str(t.transaction_id),
                "customer_name": name,
                "customer_id": cust,
                "fund_name": t.merchant_name,
                "fund_category": t.merchant_category,
                "amount": float(t.amount),
                "channel": t.channel.value,
                "status": t.status.value,
                "decision": t.decision,
                "transaction_time": t.transaction_time.isoformat()
                if t.transaction_time
                else None,
            }
            for (t, name, cust) in rows
        ],
    }
