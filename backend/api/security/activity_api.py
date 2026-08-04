"""
api/security/activity_api.py — customer-facing security activity

    GET /api/v1/security/my-activity

Returns the signed-in customer's OWN security events (one per investment
decision), in plain, customer-safe terms. This is NOT the admin audit feed:
no hashes, no signatures, no other customers, no internal signal names.

Backed by the immutable audit chain, so what the customer sees and what the
bank's auditors see come from the same source of truth.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.audit import AuditLog
from models.transaction import Transaction
from models.user import User

router = APIRouter(
    prefix="/api/v1/security",
    tags=["My Security Activity"],
)

# Plain-language, customer-facing wording for each decision.
_DECISION_COPY: dict[str, dict[str, str]] = {
    "ALLOW": {
        "title": "Investment approved",
        "detail": "This matched your usual activity, so we approved it straight away.",
        "status": "SAFE",
    },
    "WARN": {
        "title": "Investment flagged for review",
        "detail": "A few details looked slightly unusual, so we highlighted it for you.",
        "status": "REVIEWED",
    },
    "CHALLENGE": {
        "title": "Extra verification requested",
        "detail": "This looked different from your normal pattern, so we asked you to confirm it was really you.",
        "status": "VERIFIED",
    },
    "BLOCK": {
        "title": "Investment blocked",
        "detail": "This showed strong signs of fraud, so we stopped it. No money left your account.",
        "status": "BLOCKED",
    },
}

# Some events need wording of their own — the decision alone would mislead.
# A customer-reported fraud is recorded as BLOCK, but "we blocked it" hides the
# fact that the CUSTOMER stopped it. Getting this right matters: it is the one
# entry a worried customer will look for after reporting something.
_EVENT_COPY: dict[str, dict[str, str]] = {
    "CUSTOMER_REPORTED_FRAUD": {
        "title": "You stopped this investment",
        "detail": (
            "You told us you did not start this, so we cancelled it immediately. "
            "No money left your account and we are watching your account more closely."
        ),
        "status": "REPORTED",
    },
}


@router.get("/my-activity")
def get_my_security_activity(
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The customer's own security history, newest first."""
    audits = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == str(current_user.user_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    # Resolve fund names in one extra query (audit_logs stores IDs as strings,
    # so this avoids a fragile cross-type join).
    txn_ids = [a.transaction_id for a in audits if a.transaction_id]
    fund_names: dict[str, str] = {}
    if txn_ids:
        for txn in (
            db.query(Transaction)
            .filter(Transaction.user_id == current_user.user_id)
            .all()
        ):
            fund_names[str(txn.transaction_id)] = txn.merchant_name

    activities = []
    for audit in audits:
        decision = (audit.final_decision or "ALLOW").upper()
        copy = _EVENT_COPY.get(
            (audit.event_type or "").upper(),
            _DECISION_COPY.get(decision, _DECISION_COPY["ALLOW"]),
        )
        activities.append(
            {
                "id": str(audit.audit_id),
                "timestamp": audit.created_at.isoformat() if audit.created_at else None,
                "decision": decision,
                "title": copy["title"],
                "detail": copy["detail"],
                "status": copy["status"],
                "amount": float(audit.amount) if audit.amount is not None else None,
                "fund_name": fund_names.get(str(audit.transaction_id)),
                # Confirms to the customer that this record cannot be altered.
                "tamper_protected": audit.record_status == "VALID",
            }
        )

    return {"count": len(activities), "activities": activities}
