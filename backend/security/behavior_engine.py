"""
security/behavior_engine.py
===========================
MODULE 3 — Behavior Analysis Engine (Vishwas)

Purpose (from execution plan):
  Evaluate: Night Owl Activity, Velocity Burst, Large Amount Spike,
            New Recipient Risk, Behavioral Deviations.

Output: BEHAVIORAL SIGNALS ONLY (booleans).
  Example: { night_owl:true, amount_spike:true, new_recipient:false }

IMPORTANT: This module outputs booleans only. It does NOT produce a risk score
and does NOT make ALLOW/WARN/CHALLENGE/BLOCK decisions. The Risk Engine turns
these booleans into a score; the Decision Engine makes the final decision.

Owner     : Vishwas
Compliance: RBI/2025-26/219 §4 | NIST SP 800-63B | FATF Rec.16
Zero third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any

from .security_rules import Behavior


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _is_round_number(amount: float) -> bool:
    return float(amount).is_integer() and int(amount) % 10 == 0


@dataclass
class BehaviorInput:
    """Raw inputs the behavior engine evaluates."""
    transaction_hour_ist: int                 # 0-23
    amount: float
    ninety_day_median: float
    ninety_day_std: float                      # std of amount history
    recipient_id: str
    known_recipients: List[str] = field(default_factory=list)
    recent_transaction_timestamps: List[int] = field(default_factory=list)  # unix ms
    last_20_amounts: List[float] = field(default_factory=list)
    otp_entry_ms: int = 9500                   # default ~human avg
    burst_window_ms: int = Behavior.VELOCITY_BURST_WINDOW_MS


@dataclass
class BehaviorSignals:
    """Boolean behavioural signals — the ONLY output of this module."""
    night_owl: bool = False
    velocity_burst: bool = False
    amount_spike: bool = False
    extreme_amount_spike: bool = False
    new_recipient: bool = False
    otp_distress: bool = False
    otp_relay: bool = False
    round_number_anomaly: bool = False

    def as_dict(self) -> Dict[str, bool]:
        return {
            "night_owl":            self.night_owl,
            "velocity_burst":       self.velocity_burst,
            "amount_spike":         self.amount_spike,
            "extreme_amount_spike": self.extreme_amount_spike,
            "new_recipient":        self.new_recipient,
            "otp_distress":         self.otp_distress,
            "otp_relay":            self.otp_relay,
            "round_number_anomaly": self.round_number_anomaly,
        }

    def active(self) -> List[str]:
        """Names of the signals that are True."""
        return [k for k, v in self.as_dict().items() if v]


class BehaviorEngine:
    """Evaluates behavioural signals and returns booleans only."""

    def analyze(self, inp: BehaviorInput) -> BehaviorSignals:
        sig = BehaviorSignals()

        # --- Night Owl activity ---
        h = inp.transaction_hour_ist
        sig.night_owl = (h >= Behavior.NIGHT_OWL_START_HOUR or h < Behavior.NIGHT_OWL_END_HOUR)

        # --- Velocity burst ---
        now = _now_ms()
        window = inp.burst_window_ms or Behavior.VELOCITY_BURST_WINDOW_MS
        burst = [ts for ts in inp.recent_transaction_timestamps if now - ts <= window]
        sig.velocity_burst = len(burst) >= Behavior.VELOCITY_BURST_COUNT

        # --- Large amount spike (z-score OR multiple of median) ---
        median = max(inp.ninety_day_median, 1.0)
        std    = max(inp.ninety_day_std, 1.0)
        z      = (inp.amount - median) / std
        sig.amount_spike = (z >= Behavior.AMOUNT_SPIKE_ZSCORE) or \
                           (inp.amount > median * Behavior.AMOUNT_SPIKE_MULTIPLE)
        # Severity tier: a far larger outlier is its own, stronger signal.
        sig.extreme_amount_spike = (
            inp.amount > median * Behavior.AMOUNT_SPIKE_EXTREME_MULTIPLE
        )

        # --- New recipient risk ---
        sig.new_recipient = bool(inp.recipient_id) and inp.recipient_id not in inp.known_recipients

        # --- OTP behavioural deviations ---
        sig.otp_distress = inp.otp_entry_ms < Behavior.OTP_DISTRESS_MS
        sig.otp_relay    = inp.otp_entry_ms > Behavior.OTP_HIJACK_MS

        # --- Round-number anomaly (mule indicator) ---
        if inp.last_20_amounts:
            round_pct = sum(_is_round_number(a) for a in inp.last_20_amounts) / len(inp.last_20_amounts)
            sig.round_number_anomaly = round_pct > Behavior.ROUND_HIGH_RISK_PCT

        return sig


if __name__ == "__main__":
    engine = BehaviorEngine()
    print("=== behavior_engine.py self-test ===\n")

    # Fraud-like: 1 AM, huge amount, new recipient, fast OTP
    fraud = BehaviorInput(
        transaction_hour_ist=1, amount=50000, ninety_day_median=1500, ninety_day_std=800,
        recipient_id="attacker@upi", known_recipients=["mom@upi", "shop@upi"],
        recent_transaction_timestamps=[_now_ms()-60000, _now_ms()-120000, _now_ms()-180000],
        last_20_amounts=[10000]*20, otp_entry_ms=1800,
    )
    print("Fraud-like transaction:")
    print(" ", engine.analyze(fraud).as_dict())
    print("  active signals:", engine.analyze(fraud).active(), "\n")

    # Normal: 2 PM, routine amount, known recipient, normal OTP
    normal = BehaviorInput(
        transaction_hour_ist=14, amount=1250, ninety_day_median=1500, ninety_day_std=800,
        recipient_id="mom@upi", known_recipients=["mom@upi", "shop@upi"],
        recent_transaction_timestamps=[_now_ms()-24*3600000],
        last_20_amounts=[1492,879,2341,567,4321,1103,782,2253,917,1657,
                         3402,451,2783,1231,893,3157,673,1987,2101,763],
        otp_entry_ms=4200,
    )
    print("Normal transaction:")
    print(" ", engine.analyze(normal).as_dict())
    print("  active signals:", engine.analyze(normal).active() or "none")
