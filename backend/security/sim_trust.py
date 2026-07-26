"""
security/sim_trust.py
=====================
MODULE 8 — SIM Trust Service (FUTURE PLACEHOLDER)

Status: PLACEHOLDER ONLY — NOT part of the Finals MVP runtime chain.

Purpose (from execution plan):
  Future telecom integration support. Finals MVP does NOT use real telecom APIs.

Why this file exists:
  - It is one of the promised deliverables.
  - It demonstrates future extensibility for planned telecom integration.
  - It lets the architecture add SIM verification later WITHOUT structural
    changes: risk_engine.py already carries a static "sim" block, so wiring
    this module in later is a drop-in.

IMPORTANT (architecture revision):
  SIM has been REMOVED from the runtime dependency chain. risk_engine.py does
  NOT import this module. Instead, risk_engine.py inlines a static, disabled
  block:
      {"available": False, "sim_risk": 0, "reason": "telecom_integration_unavailable"}

  When telecom integration becomes available, replace that static block with a
  call to evaluate_sim_trust() below.

Owner: Vishwas — future telecom integration
Zero third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


# Current Finals MVP behaviour — telecom integration unavailable.
SIM_UNAVAILABLE = {
    "available": False,
    "sim_risk": 0,
    "reason": "telecom_integration_unavailable",
}


@dataclass
class SimTrustResult:
    """Future SIM trust output. Mirrors the static block risk_engine.py inlines."""
    available: bool = False
    sim_risk: int = 0
    reason: str = "telecom_integration_unavailable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "sim_risk":  self.sim_risk,
            "reason":    self.reason,
        }


def evaluate_sim_trust(msisdn: str | None = None) -> Dict[str, Any]:
    """
    FUTURE entry point for SIM trust evaluation.

    In the Finals MVP this always reports telecom integration as unavailable
    and contributes zero risk. When a real telecom / TRAI feed is integrated,
    this function will perform SIM-swap recency checks, carrier validation,
    and porting-history analysis, then return a populated risk block.

    Returns
    -------
    { "available": bool, "sim_risk": int, "reason": str }
    """
    # Placeholder: no telecom feed wired in Finals MVP.
    return dict(SIM_UNAVAILABLE)


if __name__ == "__main__":
    print("=== sim_trust.py (FUTURE PLACEHOLDER) self-test ===\n")
    print("This module is NOT imported by risk_engine.py in the Finals MVP.")
    print("Current behaviour:")
    print(f"  evaluate_sim_trust() -> {evaluate_sim_trust()}")
    print(f"  SimTrustResult()     -> {SimTrustResult().to_dict()}")
