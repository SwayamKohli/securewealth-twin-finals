"""
security/decision_engine.py
===========================
MODULE 2 — Decision Engine (Vishwas)

Purpose: Generate final security action. Outputs: ALLOW / WARN / CHALLENGE / BLOCK
This is the ONLY module allowed to make final transaction decisions.

Orchestration (matches the architecture: Behavior -> Risk -> Decision):
  1. Take risk_score + security_signals from the Risk Engine
  2. If the AI Team flagged UNKNOWN_RISK, fold in the Unknown Risk Handler's
     recommendation (take the stricter of the two decisions)
  3. Map risk_score -> ALLOW / WARN / CHALLENGE / BLOCK
  4. If CHALLENGE, ask the Challenge Engine (via ChallengeContext) which
     challenge to require, and carry the FULL ChallengeRequirement forward
  5. Emit the final decision record

REVIEW CHANGE APPLIED:
  DecisionRecord now carries the complete ChallengeRequirement as
  `challenge_details` (not just challenge_type). Swayam's frontend still gets
  challenge_required + challenge_type at the top level; Mahak's middleware gets
  the full object when it needs it. More extensible.

All thresholds/rules come from security_rules.py.

Owner     : Vishwas
Compliance: RBI/2025-26/219 §7(iii), §7(iv)
Zero third-party dependencies.

Run:  python decision_engine.py
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .security_rules import (
    Challenge, RISK_BANDS, COMPLIANCE_NOTE,
    DECISION_ALLOW, DECISION_WARN, DECISION_CHALLENGE, DECISION_BLOCK,
)
from .risk_engine import RiskEvaluationInput, RiskEvaluationOutput, evaluate_risk
from .challenge_engine import ChallengeEngine, ChallengeContext, ChallengeRequirement
from .unknown_risk_handler import UnknownRiskHandler, UnknownRiskEvent


_DECISION_RANK = {
    DECISION_ALLOW:     0,
    DECISION_WARN:      1,
    DECISION_CHALLENGE: 2,
    DECISION_BLOCK:     3,
}


@dataclass
class TransactionContext:
    transaction_id: str
    account_id: str
    amount: float
    channel: str
    risk_input: RiskEvaluationInput
    unknown_risk_event: Optional[UnknownRiskEvent] = None


@dataclass
class DecisionRecord:
    transaction_id: str
    account_id: str
    amount: float
    channel: str
    decision: str                          # ALLOW | WARN | CHALLENGE | BLOCK
    risk_score: int
    security_signals: Dict[str, Any]
    # Frontend-friendly top-level fields (Swayam)
    challenge_required: bool = False
    challenge_type: str = ""
    # Full challenge object for middleware (Mahak) — the review change
    challenge_details: Optional[Dict[str, Any]] = None
    unknown_risk_applied: bool = False
    unknown_risk_decision: str = ""
    unknown_risk_reason_code: str = ""
    report: str = ""
    audit_note: str = ""
    decision_timestamp: str = ""
    compliance_ref: str = ""


class DecisionEngine:
    """The ONLY module that makes final ALLOW/WARN/CHALLENGE/BLOCK decisions."""

    def __init__(self, audit_sink=None) -> None:
        self.challenge_engine = ChallengeEngine()
        self.unknown_risk_handler = UnknownRiskHandler(audit_sink=audit_sink)

    @staticmethod
    def _mask(account_id: str) -> str:
        if not account_id or len(account_id) < 8:
            return "****"
        return account_id[:3] + "****" + account_id[-4:]

    @staticmethod
    def _band_for(score: int) -> str:
        for decision, band in RISK_BANDS.items():
            if band["min"] <= score <= band["max"]:
                return decision
        return DECISION_BLOCK

    @staticmethod
    def _stricter(a: str, b: str) -> str:
        return a if _DECISION_RANK[a] >= _DECISION_RANK[b] else b

    def decide(self, ctx: TransactionContext) -> DecisionRecord:
        # STEP 1 — risk evaluation
        risk: RiskEvaluationOutput = evaluate_risk(ctx.risk_input)

        # STEP 2 — base decision from risk band
        decision = self._band_for(risk.risk_score)

        # STEP 2b — mandatory step-up signals (task 4.2/4.3).
        # Certain behaviours must be verified by the customer regardless of the
        # numeric band; the score alone can under-react when every other
        # signal (trusted device, known fund, normal hour) looks clean.
        active_signals = set(risk.security_signals.get("active_behavior", []))
        mandatory = active_signals & Challenge.MANDATORY_CHALLENGE_SIGNALS
        if mandatory:
            decision = self._stricter(decision, DECISION_CHALLENGE)

        # STEP 3 — fold in UNKNOWN_RISK recommendation (stricter wins)
        unknown_applied = False
        unknown_decision = ""
        unknown_reason_code = ""
        if ctx.unknown_risk_event is not None:
            ur = self.unknown_risk_handler.handle(ctx.unknown_risk_event)
            unknown_applied = True
            unknown_decision = ur.decision
            unknown_reason_code = ur.reason_code
            decision = self._stricter(decision, ur.decision)

        # STEP 4 — if CHALLENGE, get the full ChallengeRequirement
        challenge_req: Optional[ChallengeRequirement] = None
        if decision == DECISION_CHALLENGE:
            challenge_req = self.challenge_engine.generate(ChallengeContext(
                active_behavior=risk.security_signals.get("active_behavior", []),
                device=risk.security_signals.get("device", {}),
                risk_score=risk.risk_score,
                unknown_risk=unknown_decision or None,
            ))

        # STEP 5 — build record
        return self._build_record(
            ctx, risk, decision, challenge_req,
            unknown_applied, unknown_decision, unknown_reason_code,
        )

    def _build_record(
        self, ctx, risk, decision, challenge_req,
        unknown_applied, unknown_decision, unknown_reason_code,
    ) -> DecisionRecord:

        # Map device NEW into the reported active-signal set for clarity
        lines = [
            f"Transaction {ctx.transaction_id} | Rs.{ctx.amount:,.0f} via {ctx.channel}",
            f"Risk score: {risk.risk_score}/100  ->  Decision: {decision}",
        ]
        active = risk.security_signals.get("active_behavior", [])
        lines.append(f"Active signals: {', '.join(active) if active else 'none'}")
        if unknown_applied:
            lines.append(f"UNKNOWN_RISK handler recommended: {unknown_decision} "
                         f"[{unknown_reason_code}] (stricter outcome applied)")
        if challenge_req and challenge_req.challenge_required:
            lines.append(f"Challenge required: {challenge_req.challenge_type} "
                         f"(trigger: {challenge_req.trigger_signal})")
        report = "\n".join(lines)

        audit_map = {
            DECISION_ALLOW:     "Low risk - approved. (RBI/2025-26/219 §7(iii))",
            DECISION_WARN:      "Mild risk - user warned, proceeds with advisory. (§7(iii))",
            DECISION_CHALLENGE: "Medium risk - challenge required before proceeding. (§7(iv))",
            DECISION_BLOCK:     "High risk - transaction blocked. (§7(iii))",
        }

        return DecisionRecord(
            transaction_id=ctx.transaction_id,
            account_id=self._mask(ctx.account_id),
            amount=ctx.amount,
            channel=ctx.channel,
            decision=decision,
            risk_score=risk.risk_score,
            security_signals=risk.security_signals,
            challenge_required=bool(challenge_req and challenge_req.challenge_required),
            challenge_type=challenge_req.challenge_type if challenge_req else "",
            challenge_details=challenge_req.as_dict() if challenge_req else None,
            unknown_risk_applied=unknown_applied,
            unknown_risk_decision=unknown_decision,
            unknown_risk_reason_code=unknown_reason_code,
            report=report,
            audit_note=audit_map.get(decision, "Decision issued."),
            decision_timestamp=datetime.now(timezone.utc).isoformat(),
            compliance_ref=COMPLIANCE_NOTE,
        )


# ============================================================
# DEMO
# ============================================================
def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _demo() -> None:
    from behavior_engine import BehaviorEngine, BehaviorInput
    from risk_engine import RiskEvaluationInput, EnvironmentInput

    behavior_engine = BehaviorEngine()   # runs UPSTREAM of the Risk Engine
    engine = DecisionEngine()

    def show(title, rec):
        print("=" * 64)
        print(f"  {title}")
        print("=" * 64)
        print(rec.report)
        if rec.challenge_details:
            print(f"challenge_details: {rec.challenge_details}")
        print(f"\nAudit: {rec.audit_note}\n")

    N20 = [1492,879,2341,567,4321,1103,782,2253,917,1657,
           3402,451,2783,1231,893,3157,673,1987,2101,763]

    def device(status, confidence, age_days=100):
        # Aayat's device_trust.to_dict() shape
        return {"device_status": status, "device_confidence": confidence,
                "device_age_days": age_days, "security_signals": [status]}

    def build(tid, acc, amount, channel, hour, median, std, recip, known, ts, amts, otp,
              ip, lastip, net, dev_status, dev_conf, fraud, aiconf, ur=None):
        sig = behavior_engine.analyze(BehaviorInput(hour, amount, median, std, recip, known, ts, amts, otp))
        return TransactionContext(tid, acc, amount, channel,
            risk_input=RiskEvaluationInput(
                behavior_signals=sig,
                environment=EnvironmentInput(ip, lastip,
                    600000 if ip != lastip else 8*3600000, net),
                device_trust=device(dev_status, dev_conf),
                ai_fraud_probability=fraud, ai_confidence=aiconf),
            unknown_risk_event=ur)

    # ALLOW
    show("Persona 2 - Routine, trusted device (expect ALLOW)", engine.decide(build(
        "TXN-002","PSB1122334455",1250,"UPI",14,1500,800,"mom@upi",["mom@upi"],
        [_now_ms()-24*3600000],N20,4200,"Ludhiana","Ludhiana","HOME_WIFI","TRUSTED_DEVICE",100,0.05,0.80)))

    # ALLOW (single night-owl flag, known device)
    show("Persona 3 - Night owl + spike, known device (expect ALLOW)", engine.decide(build(
        "TXN-003","PSB9988776655",14971,"NEFT",23,4500,2500,"mom@upi",["mom@upi"],
        [_now_ms()-24*3600000],N20,4500,"Ludhiana","Ludhiana","HOME_WIFI","KNOWN_DEVICE",70,0.10,0.60)))

    # CHALLENGE
    show("Persona 6 - New device medium risk (expect CHALLENGE)", engine.decide(build(
        "TXN-006","PSB7766554433",14971,"NEFT",23,4500,2500,"vendor@neft",["mom@upi"],
        [_now_ms()-24*3600000],N20,4500,"Mumbai","Ludhiana","MOBILE_DATA","NEW_DEVICE",10,0.55,0.75)))

    # BLOCK
    show("Persona 1 - Social engineering, zero-day device (expect BLOCK)", engine.decide(build(
        "TXN-001","PSB3920048291",50000,"UPI",1,1500,800,"attacker@upi",["mom@upi"],
        [_now_ms()-60000,_now_ms()-120000,_now_ms()-180000],[10000]*20,1800,
        "Dubai","Ludhiana","VPN","ZERO_DAY_DEVICE",5,0.97,0.95)))

    # BLOCK via UNKNOWN_RISK
    show("Persona 5 - Low rule risk BUT AI UNKNOWN_RISK 0.91 (expect BLOCK)", engine.decide(build(
        "TXN-005","PSB0011223344",5000,"UPI",14,4500,2500,"mom@upi",["mom@upi"],
        [_now_ms()-24*3600000],N20,4200,"Ludhiana","Ludhiana","HOME_WIFI","TRUSTED_DEVICE",100,0.20,0.50,
        ur=UnknownRiskEvent("UNKNOWN_RISK",0.91,"TXN-005"))))


if __name__ == "__main__":
    _demo()
