"""
security/security_rules.py
==========================
MODULE 6 — Security Rules Registry (Vishwas)

Purpose (from execution plan):
  Store risk thresholds, risk weights, penalty scores, challenge thresholds,
  and decision rules. NO hardcoded values should exist elsewhere.

This is the single source of truth for every tunable number in the security
layer. Every other module imports from here.

Owner     : Vishwas — Risk Evaluation & Security Decision Layer
Compliance: RBI/2025-26/219 | NIST SP 800-63B | FATF
Zero third-party dependencies.
"""

from __future__ import annotations


# ============================================================
# 1. RISK EVALUATION WEIGHTS  (risk_engine.py) — must sum to 1.0
# ============================================================
# Inputs to the Risk Engine per the plan:
#   fraud probability (AI), device trust, SIM trust (future), behavioral
#   signals, transaction attributes, environmental signals.
RISK_WEIGHTS = {
    "ai_fraud":      0.35,   # fraud probability from AI Team (primary signal)
    "behavioral":    0.25,   # behavior_engine boolean signals -> score
    "device":        0.25,   # device trust (AAYAT): status penalty + confidence modifier
    "environmental": 0.15,   # environmental signals
    # SIM removed from the runtime dependency chain (Finals MVP). It remains a
    # future placeholder module (sim_trust.py) but contributes no weight here.
}


# ============================================================
# 2. RISK BANDS  (decision_engine.py)
# ============================================================
# Final decision states — the plan requires FOUR:
DECISION_ALLOW     = "ALLOW"
DECISION_WARN      = "WARN"
DECISION_CHALLENGE = "CHALLENGE"
DECISION_BLOCK     = "BLOCK"

# score (0-100) -> decision band
RISK_BANDS = {
    "ALLOW":     {"min": 0,  "max": 30},   # low risk       -> ALLOW
    "WARN":      {"min": 31, "max": 55},   # mild risk      -> WARN (advisory)
    "CHALLENGE": {"min": 56, "max": 79},   # medium risk    -> CHALLENGE (step-up)
    "BLOCK":     {"min": 80, "max": 100},  # high risk      -> BLOCK
}


# ============================================================
# 3. BEHAVIOR ANALYSIS THRESHOLDS  (behavior_engine.py)
# ============================================================
# The Behavior Engine outputs BOOLEAN signals (not scores). These thresholds
# decide when each boolean flips to true.
class Behavior:
    # Night Owl window (Fed Reserve CFI 2022 / RBI 2025-26/219 §4(iv))
    NIGHT_OWL_START_HOUR = 23      # 11:01 PM IST
    NIGHT_OWL_END_HOUR   = 6       # 05:59 AM IST

    # Velocity burst (RBI Velocity Ceiling)
    VELOCITY_BURST_WINDOW_MS = 300000   # 5 minutes
    VELOCITY_BURST_COUNT     = 3        # >= 3 txns in window -> burst

    # Large amount spike (z-score vs user's own history)
    AMOUNT_SPIKE_ZSCORE   = 3.0    # amount > mean + 3*std -> spike
    AMOUNT_SPIKE_MULTIPLE = 3.0    # OR amount > 3x the 90-day median

    # OTP behavioural deviation (IJIS 2021 / NIST SP 800-63B)
    OTP_DISTRESS_MS = 2500         # < 2.5s -> coercion / bot
    OTP_HIJACK_MS   = 60000        # > 60s  -> relay attack

    # Round-number frequency (Benford / FATF Rec.16) — mule indicator
    ROUND_BASELINE_PCT  = 0.15
    ROUND_HIGH_RISK_PCT = 0.35


# ============================================================
# 4. BEHAVIOR SIGNAL -> RISK PENALTY SCORES  (risk_engine.py)
# ============================================================
# When a behavioural boolean is true, how many risk points it adds.
BEHAVIOR_PENALTY = {
    "night_owl":            25,
    "velocity_burst":       50,
    "amount_spike":         40,
    "new_recipient":        20,
    "otp_distress":         60,
    "otp_relay":            40,
    "round_number_anomaly": 45,
}
BEHAVIOR_PENALTY_CAP = 100   # behavioural sub-score capped at 100


# ============================================================
# 5. DEVICE TRUST SCORING  (risk_engine.py consumes AAYAT's device_trust)
# ============================================================
class Device:
    # Aayat's device_trust.py no longer returns risk_penalty. The Risk Engine
    # now OWNS the device_status -> penalty mapping (per the architecture
    # revision). device_confidence then acts as a modifier on top.
    #
    # Aayat's to_dict() device_status values (external interface):
    #   NEW_DEVICE | KNOWN_DEVICE | TRUSTED_DEVICE | INACTIVE_DEVICE
    #   + fraud extensions: SUSPICIOUS_DEVICE | ZERO_DAY_DEVICE
    #   (FIRST_TIME_USER is collapsed to NEW_DEVICE at her boundary)

    # 1. Category penalty by device_status (base device risk).
    STATUS_PENALTY = {
        "TRUSTED_DEVICE":    0,
        "KNOWN_DEVICE":      10,
        "INACTIVE_DEVICE":   25,
        "NEW_DEVICE":        50,
        "SUSPICIOUS_DEVICE": 75,    # high penalty
        "ZERO_DAY_DEVICE":   95,    # very high penalty
    }
    STATUS_PENALTY_DEFAULT = 50     # unknown status -> treat as NEW-level risk

    # 2. device_confidence (0-100) acts as a MODIFIER on the base penalty.
    #    Low confidence amplifies risk; high confidence dampens it.
    #    modifier = 1 + (CONF_MOD_STRENGTH * (50 - confidence) / 50)
    #    e.g. confidence=100 -> 0.7x, confidence=50 -> 1.0x, confidence=0 -> 1.3x
    CONF_MOD_STRENGTH = 0.30
    CONF_MOD_MIN = 0.70            # clamp so a trusted device never hits 0
    CONF_MOD_MAX = 1.30

    @staticmethod
    def confidence_modifier(confidence: float) -> float:
        """
        Compute the device_confidence modifier applied on top of the
        STATUS_PENALTY base penalty.

        modifier = 1 + (CONF_MOD_STRENGTH * (50 - confidence) / 50)
        e.g. confidence=100 -> 0.7x, confidence=50 -> 1.0x, confidence=0 -> 1.3x

        Result is clamped to [CONF_MOD_MIN, CONF_MOD_MAX] so this is the
        single source of truth for the formula — risk_engine.py should call
        this helper rather than reimplementing the equation.
        """
        modifier = 1 + (Device.CONF_MOD_STRENGTH * (50 - confidence) / 50)
        return max(Device.CONF_MOD_MIN, min(Device.CONF_MOD_MAX, modifier))


# ============================================================
# 6. SIM TRUST  (FUTURE — NOT in runtime chain; documentation only)
# ============================================================
# SIM has been removed from the runtime dependency chain. risk_engine.py no
# longer imports this class — it inlines a static disabled SIM block instead.
# This class is kept purely as documentation of the future feature; the live
# placeholder module is sim_trust.py.
class SIM:
    # Finals MVP: telecom integration unavailable. SIM trust returns
    # { available:false, sim_risk:0 } and contributes NOTHING to risk.
    ENABLED = False
    PENALTY = 0


# ============================================================
# 7. ENVIRONMENTAL THRESHOLDS  (risk_engine.py)
# ============================================================
class Environmental:
    IMPOSSIBLE_TRAVEL_WINDOW_MS = 3 * 60 * 60 * 1000
    IMPOSSIBLE_TRAVEL_PENALTY   = 60
    REGION_CHANGE_PENALTY       = 25
    NETWORK_RISK = {"HOME_WIFI": 0, "MOBILE_DATA": 5, "PUBLIC_WIFI": 15, "VPN": 20}
    NETWORK_RISK_DEFAULT = 10


# ============================================================
# 8. CHALLENGE ENGINE RULES  (challenge_engine.py)
# ============================================================
# Challenge TYPES (the plan's exact list). The Challenge Engine outputs a
# challenge TYPE only — never ALLOW/WARN/CHALLENGE/BLOCK.
class Challenge:
    OTP_RECONFIRMATION      = "OTP_RECONFIRMATION"
    TRANSACTION_CONFIRMATION = "TRANSACTION_CONFIRMATION"
    RISK_WARNING_ACCEPTANCE = "RISK_WARNING_ACCEPTANCE"
    DEVICE_CONFIRMATION     = "DEVICE_CONFIRMATION"

    # Which challenge type to pick, by dominant risk reason.
    # Evaluated top-to-bottom; first match wins.
    #   reason flag           -> challenge type
    #
    # NOTE: "new_device" here refers to the behavior/security reason flag
    # consumed by the Decision Engine (i.e. a derived signal indicating an
    # unrecognized device contributed to the risk score), NOT the literal
    # NEW_DEVICE string returned by device_trust.py's device_status field
    # (see Device.STATUS_PENALTY above). The mapping from device_status to
    # this reason flag happens in risk_engine.py.
    SELECTION_ORDER = [
        ("new_device",    DEVICE_CONFIRMATION),
        ("otp_distress",  OTP_RECONFIRMATION),
        ("amount_spike",  TRANSACTION_CONFIRMATION),
        ("night_owl",     RISK_WARNING_ACCEPTANCE),
    ]
    DEFAULT = RISK_WARNING_ACCEPTANCE


# ============================================================
# 9. UNKNOWN RISK HANDLER RULES  (unknown_risk_handler.py)
# ============================================================
# The AI Team sends UNKNOWN_RISK events: { status, confidence }.
# Handler maps severity (derived from confidence) -> decision.
class UnknownRisk:
    # confidence -> severity
    LOW_SEVERITY_MAX    = 0.60   # confidence <= 0.60 -> LOW    -> WARN
    MEDIUM_SEVERITY_MAX = 0.85   # 0.60 < conf <= 0.85 -> MEDIUM -> CHALLENGE
    # confidence > 0.85 -> HIGH -> BLOCK

    SEVERITY_TO_DECISION = {
        "LOW":    DECISION_WARN,
        "MEDIUM": DECISION_CHALLENGE,
        "HIGH":   DECISION_BLOCK,
    }


# ============================================================
# 10. AI FRAUD PROBABILITY FUSION  (risk_engine.py)
# ============================================================
class AIFusion:
    # fraud_probability (0-1) from AI Team -> risk points (0-100).
    # Direct scaling; the RISK_WEIGHTS["ai_fraud"] weight handles blending.
    MIN_CONFIDENCE = 0.40   # ignore AI fraud prob below this confidence


# ============================================================
# 11. COMPLIANCE REFERENCE
# ============================================================
COMPLIANCE_NOTE = (
    "Evaluated per RBI/2025-26/219, NIST SP 800-63B (AAL3), "
    "FATF Layering Guidelines."
)


# ── sanity check on import ─────────────────────────────────────
assert abs(sum(RISK_WEIGHTS.values()) - 1.0) < 1e-9, "RISK_WEIGHTS must sum to 1.0"
