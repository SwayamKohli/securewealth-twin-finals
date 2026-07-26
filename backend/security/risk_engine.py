"""
security/risk_engine.py
=======================
MODULE 1 — Risk Evaluation Engine (Vishwas)

Purpose (from execution plan): Calculate transaction risk.

Inputs:
  - Behavioral signals   (BehaviorSignals — booleans, produced UPSTREAM by
                          behavior_engine.py; the Risk Engine does NOT invoke
                          the Behavior Engine itself)
  - Fraud probability    (from AI Team)
  - Device trust output  (from AAYAT's device_trust.py, consumed as a plain
                          dict: device_status, device_confidence,
                          device_age_days, security_signals)
  - Environmental signals

Output: { risk_score, security_signals }

DEVICE TRUST CONSUMPTION (architecture revision):
  Aayat's device_trust.py no longer returns risk_penalty. The Risk Engine now
  OWNS the device_status -> penalty mapping and applies device_confidence as a
  modifier on top:

      device_status      -> base category penalty   (security_rules.Device.STATUS_PENALTY)
      device_confidence  -> modifier (0.70x .. 1.30x) on that penalty
      device_sub_score   = clamp(base_penalty * confidence_modifier, 0, 100)

  This produces a robust device risk score:
      NEW_DEVICE        -> new-device penalty
      INACTIVE_DEVICE   -> inactive penalty
      SUSPICIOUS_DEVICE -> high penalty
      ZERO_DAY_DEVICE   -> very high penalty

SIM TRUST (architecture revision):
  SIM is REMOVED from the runtime dependency chain. sim_trust.py remains only
  as a future placeholder module (not imported). The Risk Engine inlines a
  static, disabled SIM block in security_signals for forward-compatibility:
      {"available": False, "sim_risk": 0, "reason": "telecom_integration_unavailable"}

ARCHITECTURE:
      Transaction -> Behavior Engine -> Behavior Signals -> Risk Engine -> Decision Engine
  Device Trust (Aayat) -> device dict ----------------------^

All thresholds/weights come from security_rules.py.

Owner     : Vishwas
Compliance: RBI/2025-26/219 | NIST SP 800-63B | FATF
Zero third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any

from .security_rules import (
    RISK_WEIGHTS, BEHAVIOR_PENALTY, BEHAVIOR_PENALTY_CAP,
    Device, Environmental, AIFusion, COMPLIANCE_NOTE,
)
from .behavior_engine import BehaviorSignals


# Static SIM block — SIM is out of the runtime chain (future placeholder only).
_SIM_STATIC = {
    "available": False,
    "sim_risk": 0,
    "reason": "telecom_integration_unavailable",
}


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(v, hi))


# ============================================================
# INPUT STRUCTURES
# ============================================================
@dataclass
class EnvironmentInput:
    ip_region: str
    last_login_region: str
    time_since_last_login_ms: int
    network_type: str                 # HOME_WIFI | MOBILE_DATA | PUBLIC_WIFI | VPN


@dataclass
class RiskEvaluationInput:
    """
    Everything the Risk Engine needs to score one transaction.

    device_trust is Aayat's device_trust.py output as a plain dict:
        {
          "device_status":     "NEW_DEVICE" | "KNOWN_DEVICE" | "TRUSTED_DEVICE"
                               | "INACTIVE_DEVICE" | "SUSPICIOUS_DEVICE" | "ZERO_DAY_DEVICE",
          "device_confidence": 0-100,
          "device_age_days":   int,
          "security_signals":  [str, ...]
        }

    behavior_signals is a BehaviorSignals object already computed upstream by
    the Behavior Engine — the Risk Engine does not run the Behavior Engine.
    """
    behavior_signals: BehaviorSignals                 # produced upstream
    environment: EnvironmentInput
    device_trust: Dict[str, Any]                      # Aayat's device_trust.to_dict()
    ai_fraud_probability: float = 0.0                 # 0-1 from AI Team
    ai_confidence: float = 0.0                        # 0-1 from AI Team


@dataclass
class RiskEvaluationOutput:
    """The plan's required output: { risk_score, security_signals }."""
    risk_score: int                                   # 0-100
    security_signals: Dict[str, Any]
    timestamp: str = ""
    compliance_note: str = ""


# ============================================================
# SUB-SCORERS
# ============================================================
def _behavioral_score(signals: BehaviorSignals) -> int:
    """Turn behaviour booleans into a 0-100 behavioural sub-score."""
    score = 0
    for name, is_on in signals.as_dict().items():
        if is_on:
            score += BEHAVIOR_PENALTY.get(name, 0)
    return int(_clamp(score, 0, BEHAVIOR_PENALTY_CAP))


def _confidence_modifier(device_confidence: int) -> float:
    """
    device_confidence (0-100) -> multiplier on the base device penalty.
      confidence=100 -> ~0.70x  (trusted, dampen risk)
      confidence=50  -> 1.00x   (neutral)
      confidence=0   -> ~1.30x  (amplify risk)
    """
    conf = _clamp(device_confidence, 0, 100)
    modifier = 1.0 + (Device.CONF_MOD_STRENGTH * (50 - conf) / 50.0)
    return max(Device.CONF_MOD_MIN, min(Device.CONF_MOD_MAX, modifier))


def _device_score(device: Dict[str, Any]) -> int:
    """
    Fully consume Aayat's device output.

    device_status -> base category penalty (STATUS_PENALTY)
    device_confidence -> modifier on that penalty
    -> device sub-score (0-100)
    """
    status = device.get("device_status", "NEW_DEVICE")
    confidence = int(device.get("device_confidence", 0))

    base_penalty = Device.STATUS_PENALTY.get(status, Device.STATUS_PENALTY_DEFAULT)
    modifier = _confidence_modifier(confidence)
    return int(_clamp(round(base_penalty * modifier), 0, 100))


def _environmental_score(env: EnvironmentInput) -> int:
    score = 0
    if env.ip_region != env.last_login_region and \
            env.time_since_last_login_ms < Environmental.IMPOSSIBLE_TRAVEL_WINDOW_MS:
        score += Environmental.IMPOSSIBLE_TRAVEL_PENALTY
    elif env.ip_region != env.last_login_region:
        score += Environmental.REGION_CHANGE_PENALTY
    score += Environmental.NETWORK_RISK.get(env.network_type, Environmental.NETWORK_RISK_DEFAULT)
    return int(_clamp(score))


def _ai_fraud_score(prob: float, confidence: float) -> int:
    if confidence < AIFusion.MIN_CONFIDENCE:
        return 0
    return int(_clamp(prob * 100))


# ============================================================
# MASTER ENTRY POINT
# ============================================================
def evaluate_risk(inp: RiskEvaluationInput) -> RiskEvaluationOutput:
    """Calculate transaction risk. Returns { risk_score, security_signals }."""

    behavior_signals = inp.behavior_signals   # already computed upstream

    sub = {
        "behavioral":    _behavioral_score(behavior_signals),
        "device":        _device_score(inp.device_trust),
        "environmental": _environmental_score(inp.environment),
        "ai_fraud":      _ai_fraud_score(inp.ai_fraud_probability, inp.ai_confidence),
    }

    risk_score = 0.0
    contributions = {}
    for key, weight in RISK_WEIGHTS.items():
        contribution = sub[key] * weight
        contributions[key] = {
            "sub_score": sub[key],
            "weight": weight,
            "contribution": round(contribution, 2),
        }
        risk_score += contribution
    risk_score = int(round(_clamp(risk_score)))

    security_signals = {
        "behavior_flags":  behavior_signals.as_dict(),
        "active_behavior": behavior_signals.active(),
        "device": {
            "device_status":     inp.device_trust.get("device_status"),
            "device_confidence": inp.device_trust.get("device_confidence"),
            "device_age_days":   inp.device_trust.get("device_age_days"),
            "security_signals":  inp.device_trust.get("security_signals", []),
        },
        # SIM is out of the runtime chain — static, disabled block for
        # forward-compatibility (future telecom integration).
        "sim": dict(_SIM_STATIC),
        "ai": {
            "fraud_probability": inp.ai_fraud_probability,
            "confidence":        inp.ai_confidence,
        },
        "environment": {
            "region_changed": inp.environment.ip_region != inp.environment.last_login_region,
            "network_type":   inp.environment.network_type,
        },
        "sub_scores":    sub,
        "contributions": contributions,
    }

    return RiskEvaluationOutput(
        risk_score=risk_score,
        security_signals=security_signals,
        timestamp=datetime.now(timezone.utc).isoformat(),
        compliance_note=COMPLIANCE_NOTE,
    )


if __name__ == "__main__":
    from behavior_engine import BehaviorEngine, BehaviorInput

    behavior_engine = BehaviorEngine()   # runs UPSTREAM, not inside Risk Engine
    print("=== risk_engine.py self-test ===\n")

    def _now_ms(): return int(datetime.now(timezone.utc).timestamp()*1000)

    # Fraud-like: behaviour computed FIRST, device trust is Aayat's dict shape
    fraud_signals = behavior_engine.analyze(BehaviorInput(
        1, 50000, 1500, 800, "attacker@upi", ["mom@upi"], [], [10000]*20, 1800))
    fraud = RiskEvaluationInput(
        behavior_signals=fraud_signals,
        environment=EnvironmentInput("Dubai, AE", "Ludhiana, PB, IN", 600000, "VPN"),
        device_trust={"device_status": "ZERO_DAY_DEVICE", "device_confidence": 5,
                      "device_age_days": 0, "security_signals": ["ZERO_DAY_DEVICE"]},
        ai_fraud_probability=0.88, ai_confidence=0.90,
    )
    out = evaluate_risk(fraud)
    print(f"Fraud-like (ZERO_DAY device) -> risk_score = {out.risk_score}/100")
    print(f"  device sub-score: {out.security_signals['sub_scores']['device']}")
    print(f"  active behavior : {out.security_signals['active_behavior']}")
    print(f"  sub_scores      : {out.security_signals['sub_scores']}")
    print(f"  sim block       : {out.security_signals['sim']}\n")

    N20 = [1492,879,2341,567,4321,1103,782,2253,917,1657,
           3402,451,2783,1231,893,3157,673,1987,2101,763]
    normal_signals = behavior_engine.analyze(BehaviorInput(
        14, 1250, 1500, 800, "mom@upi", ["mom@upi"], [], N20, 4200))
    normal = RiskEvaluationInput(
        behavior_signals=normal_signals,
        environment=EnvironmentInput("Ludhiana, PB, IN", "Ludhiana, PB, IN", 8*3600000, "HOME_WIFI"),
        device_trust={"device_status": "TRUSTED_DEVICE", "device_confidence": 100,
                      "device_age_days": 151, "security_signals": ["TRUSTED_DEVICE", "HIGH_CONFIDENCE"]},
        ai_fraud_probability=0.05, ai_confidence=0.80,
    )
    out2 = evaluate_risk(normal)
    print(f"Normal (TRUSTED device) -> risk_score = {out2.risk_score}/100")
    print(f"  device sub-score: {out2.security_signals['sub_scores']['device']}")
    print(f"  active behavior : {out2.security_signals['active_behavior'] or 'none'}")
    print(f"  sub_scores      : {out2.security_signals['sub_scores']}\n")

    # Device status penalty demonstration
    print("Device status -> sub-score (confidence held at 50 = neutral):")
    for st in ["TRUSTED_DEVICE","KNOWN_DEVICE","INACTIVE_DEVICE","NEW_DEVICE","SUSPICIOUS_DEVICE","ZERO_DAY_DEVICE"]:
        s = _device_score({"device_status": st, "device_confidence": 50})
        print(f"  {st:18} -> {s}")
