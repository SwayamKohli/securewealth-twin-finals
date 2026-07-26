"""
security/challenge_engine.py
============================
MODULE 4 — Challenge Engine (Vishwas)

Purpose: Generate additional verification requirements for medium-risk txns.

Challenge Types:
  OTP_RECONFIRMATION | TRANSACTION_CONFIRMATION |
  RISK_WARNING_ACCEPTANCE | DEVICE_CONFIRMATION

Output: { challenge_required, challenge_type, trigger_signal }

IMPORTANT: The Challenge Engine does NOT output ALLOW/WARN/CHALLENGE/BLOCK.
Only the Decision Engine makes final decisions.

REVIEW CHANGES APPLIED:
  1. No English sentences here. This module emits a machine-readable
     `trigger_signal` (reason code) instead of a human explanation. Archit's
     Explainability Engine converts trigger_signal -> customer wording.
  2. generate() takes a ChallengeContext (not a bare list[str]), so future
     inputs (device, risk_score, unknown_risk) can drive challenge selection
     without changing the signature.

Owner     : Vishwas
Compliance: RBI/2025-26/219 §7(iv)
Zero third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .security_rules import Challenge


@dataclass
class ChallengeContext:
    """
    Future-proof input to the Challenge Engine. Only active_behavior is needed
    today, but device / risk_score / unknown_risk are already carried so the
    signature never has to change when they start driving selection.
    """
    active_behavior: List[str] = field(default_factory=list)
    device: Dict[str, Any] = field(default_factory=dict)          # {status, confidence, ...}
    risk_score: Optional[int] = None
    unknown_risk: Optional[str] = None                            # severity or status


@dataclass
class ChallengeRequirement:
    """
    The ONLY output of this module — a challenge requirement, never a decision.
    `trigger_signal` is a machine-readable reason code (NOT English). Archit's
    Explainability Engine turns it into customer-facing text.
    """
    challenge_required: bool
    challenge_type: str          # one of Challenge.* type strings ("" if none)
    trigger_signal: str          # reason code, e.g. "new_device" ("" if none)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "challenge_required": self.challenge_required,
            "challenge_type":     self.challenge_type,
            "trigger_signal":     self.trigger_signal,
        }


class ChallengeEngine:
    """Picks a challenge TYPE from a ChallengeContext. Never decides."""

    def generate(self, context: ChallengeContext) -> ChallengeRequirement:
        """
        Parameters
        ----------
        context : ChallengeContext with active_behavior (and optionally device,
                  risk_score, unknown_risk for future rules).

        Returns
        -------
        ChallengeRequirement with challenge_type + machine-readable trigger_signal.
        """
        active = set(context.active_behavior)

        # A NEW device is derived from the device context, not just behaviour.
        # Aayat's device_trust.to_dict() uses key "device_status" with value
        # "NEW_DEVICE" (also accept legacy "status"/"NEW" for safety).
        device_status = context.device.get("device_status") or context.device.get("status")
        if device_status in ("NEW_DEVICE", "NEW"):
            active.add("new_device")

        # First matching signal in the priority order (defined in security_rules).
        for flag, ctype in Challenge.SELECTION_ORDER:
            if flag in active:
                return ChallengeRequirement(
                    challenge_required=True,
                    challenge_type=ctype,
                    trigger_signal=flag,          # machine-readable, no English
                )

        # Default challenge when a challenge is needed but no specific flag matched.
        return ChallengeRequirement(
            challenge_required=True,
            challenge_type=Challenge.DEFAULT,
            trigger_signal="default",
        )

    def none_required(self) -> ChallengeRequirement:
        return ChallengeRequirement(
            challenge_required=False,
            challenge_type="",
            trigger_signal="",
        )


if __name__ == "__main__":
    engine = ChallengeEngine()
    print("=== challenge_engine.py self-test ===\n")

    scenarios = [
        ("New device (via device ctx)", ChallengeContext(active_behavior=["night_owl"],
                                                          device={"device_status": "NEW_DEVICE"})),
        ("OTP distress",                ChallengeContext(active_behavior=["otp_distress", "amount_spike"])),
        ("Amount spike only",           ChallengeContext(active_behavior=["amount_spike"])),
        ("Night owl only",             ChallengeContext(active_behavior=["night_owl"])),
        ("No specific flag -> default", ChallengeContext(active_behavior=["some_other_flag"])),
    ]
    for title, ctx in scenarios:
        r = engine.generate(ctx)
        print(f"{title}")
        print(f"  {r.as_dict()}\n")

    print("No challenge needed:")
    print(f"  {engine.none_required().as_dict()}")
