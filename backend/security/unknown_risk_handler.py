"""
security/unknown_risk_handler.py
================================
MODULE 5 — Unknown Risk Handler (Vishwas)

Purpose: Handle UNKNOWN_RISK events from the AI Team.

Input: { status: "UNKNOWN_RISK", confidence: 0.91 }

Severity mapping:
  Low    -> WARN
  Medium -> CHALLENGE
  High   -> BLOCK

All UNKNOWN_RISK events generate an audit entry, increase monitoring, and
record a reason_code. No human review workflow in Finals MVP.

REVIEW CHANGES APPLIED:
  1. No customer sentences here. The handler emits a machine-readable
     `reason_code` (e.g. "UNKNOWN_RISK_HIGH"). Archit's Explainability Engine
     converts reason_code -> customer wording. Keeps security language-agnostic.
  2. `status` is validated against VALID_STATUS. An invalid status raises
     ValueError instead of being silently accepted.

All thresholds come from security_rules.UnknownRisk.

Owner     : Vishwas
Compliance: RBI/2025-26/219
Zero third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List

from .security_rules import UnknownRisk


# Valid AI-team statuses this handler accepts.
VALID_STATUS = {"NORMAL", "ANOMALOUS", "UNKNOWN_RISK"}


@dataclass
class UnknownRiskEvent:
    """Input from the AI Team."""
    status: str                 # must be in VALID_STATUS
    confidence: float           # 0-1
    transaction_id: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnknownRiskDecision:
    """
    Handler output — a recommended decision + the audit entry it generated.
    `reason_code` is machine-readable (NOT English). Archit converts it.
    """
    severity: str               # LOW | MEDIUM | HIGH
    decision: str               # WARN | CHALLENGE | BLOCK
    reason_code: str            # e.g. "UNKNOWN_RISK_HIGH"
    increase_monitoring: bool
    audit_entry: Dict[str, Any]
    timestamp: str


class UnknownRiskHandler:
    """
    Converts an UNKNOWN_RISK event into a recommended decision
    (WARN / CHALLENGE / BLOCK) and always emits an audit entry.
    Never executes the transaction itself.
    """

    def __init__(self, audit_sink: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        self._audit_sink = audit_sink
        self.audit_log: List[Dict[str, Any]] = []

    @staticmethod
    def _severity(confidence: float) -> str:
        if confidence <= UnknownRisk.LOW_SEVERITY_MAX:
            return "LOW"
        if confidence <= UnknownRisk.MEDIUM_SEVERITY_MAX:
            return "MEDIUM"
        return "HIGH"

    def handle(self, event: UnknownRiskEvent) -> UnknownRiskDecision:
        # --- Change 2: validate the incoming status ---
        if event.status not in VALID_STATUS:
            raise ValueError(
                f"Invalid AI status '{event.status}'. "
                f"Expected one of {sorted(VALID_STATUS)}."
            )

        severity = self._severity(event.confidence)
        decision = UnknownRisk.SEVERITY_TO_DECISION[severity]
        now = datetime.now(timezone.utc).isoformat()

        # --- Change 1: machine-readable reason_code, not English ---
        # e.g. "UNKNOWN_RISK_HIGH", "ANOMALOUS_LOW"
        reason_code = f"{event.status}_{severity}"

        audit_entry = {
            "event_type":     "UNKNOWN_RISK",
            "transaction_id": event.transaction_id,
            "ai_status":      event.status,
            "ai_confidence":  event.confidence,
            "severity":       severity,
            "decision":       decision,
            "reason_code":    reason_code,      # machine-readable
            "monitoring":     "INCREASED",
            "timestamp":      now,
        }
        self._emit_audit(audit_entry)

        return UnknownRiskDecision(
            severity=severity,
            decision=decision,
            reason_code=reason_code,
            increase_monitoring=True,
            audit_entry=audit_entry,
            timestamp=now,
        )

    def _emit_audit(self, entry: Dict[str, Any]) -> None:
        self.audit_log.append(entry)
        if self._audit_sink is not None:
            try:
                self._audit_sink(entry)
            except Exception:  # noqa: BLE001 - audit must never crash the flow
                pass


if __name__ == "__main__":
    handler = UnknownRiskHandler()
    print("=== unknown_risk_handler.py self-test ===\n")

    events = [
        ("Low severity",    UnknownRiskEvent("UNKNOWN_RISK", 0.55, "TXN-1")),
        ("Medium severity", UnknownRiskEvent("UNKNOWN_RISK", 0.75, "TXN-2")),
        ("High severity",   UnknownRiskEvent("UNKNOWN_RISK", 0.91, "TXN-3")),
        ("Anomalous status", UnknownRiskEvent("ANOMALOUS",   0.50, "TXN-4")),
    ]
    for title, ev in events:
        d = handler.handle(ev)
        print(f"{title}  (status={ev.status}, confidence={ev.confidence})")
        print(f"  severity    : {d.severity}")
        print(f"  decision    : {d.decision}")
        print(f"  reason_code : {d.reason_code}")
        print(f"  audit entry : event_type={d.audit_entry['event_type']}, decision={d.audit_entry['decision']}\n")

    # Invalid status -> ValueError
    print("Invalid status test:")
    try:
        handler.handle(UnknownRiskEvent("HELLO", 0.90, "TXN-BAD"))
    except ValueError as e:
        print(f"  raised ValueError: {e}")

    print(f"\nTotal audit entries recorded: {len(handler.audit_log)}")
