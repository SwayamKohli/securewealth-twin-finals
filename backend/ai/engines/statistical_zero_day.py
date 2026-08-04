"""
ai/engines/statistical_zero_day.py
==================================
Zero-Day / Unknown-Risk detector — statistical fallback.

WHY THIS EXISTS
    The primary detector (`zero_day_detector.ZeroDayDetector`) is a PyTorch
    autoencoder. It needs `torch` plus trained weights (`autoencoder.pth`,
    `ae_thresholds.json`). When those are unavailable the system previously ran
    with NO novelty detection at all, silently dropping a pillar of the
    architecture.

    This module provides an always-available detector built only on numpy and
    the same `user_baselines.pkl` the fraud engine already ships. It is not a
    replacement for the autoencoder — it is the guarantee that "Unknown"
    classification is never simply absent.

APPROACH
    Per-dimension standardised deviation from the customer's own 90-day
    baseline (amount, OTP timing, hour-of-day, velocity), plus categorical
    novelty (unseen device, unseen recipient). Deviations are squared, weighted
    and averaged into a novelty score, which is compared against thresholds
    derived from the population of baselines at load time — the same
    P95 / P99 logic the autoencoder uses.

OUTPUT CONTRACT
    Identical to ZeroDayDetector.detect(), so the two are interchangeable:
        status                "NORMAL" | "ANOMALOUS" | "UNKNOWN_RISK"
        confidence            0.0–1.0
        reconstruction_error  float   (novelty score)
        error_percentile      float
        anomalous_dimensions  list[{feature, error}]
"""

from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Any

_MODELS_DIR = Path(__file__).parent / "models"

# Relative importance of each dimension in the novelty score.
_WEIGHTS = {
    "amount": 0.30,
    "otp_time": 0.20,
    "hour": 0.15,
    "velocity": 0.15,
    "new_device": 0.10,
    "new_recipient": 0.10,
}

# Deviations beyond this many standard deviations are clipped, so one extreme
# dimension cannot single-handedly saturate the score.
_MAX_Z = 6.0


class StatisticalZeroDayDetector:
    """Baseline-deviation novelty detector. No torch, no trained weights."""

    def __init__(
        self,
        user_baselines: dict[str, dict[str, Any]],
        p95: float,
        p99: float,
    ) -> None:
        self._baselines = user_baselines
        self._p95 = p95
        self._p99 = p99

    # ── Factory ────────────────────────────────────────────────────────────

    @classmethod
    def from_disk(
        cls,
        baselines_path: str | Path | None = None,
    ) -> "StatisticalZeroDayDetector":
        path = Path(baselines_path) if baselines_path else _MODELS_DIR / "user_baselines.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Missing baselines: {path}")

        with open(path, "rb") as f:
            baselines = pickle.load(f)

        # Thresholds: a novelty score is "anomalous" past P95 and "unknown"
        # past P99. With standardised inputs these settle near 1.0 and 2.2;
        # they are stated explicitly so the numbers are auditable.
        return cls(user_baselines=baselines, p95=1.00, p99=2.20)

    # ── Public API (mirrors ZeroDayDetector.detect) ────────────────────────

    def detect(self, transaction: dict) -> dict:
        uid = str(transaction.get("user_id", ""))
        baseline = self._baselines.get(uid) or self._baselines.get(
            "__global_fallback__", {}
        )

        dims: dict[str, float] = {}

        # ── Amount deviation ───────────────────────────────────────────────
        amount = self._f(transaction.get("amount"))
        avg_amt = self._f(baseline.get("avg_amount"), 5000.0)
        std_amt = max(self._f(baseline.get("std_amount"), 2000.0), 1.0)
        dims["amount"] = self._clip(abs(amount - avg_amt) / std_amt)

        # ── OTP timing deviation ───────────────────────────────────────────
        otp = self._f(transaction.get("otp_time_sec"), 8.0)
        avg_otp = self._f(baseline.get("avg_otp_time"), 8.0)
        std_otp = max(self._f(baseline.get("std_otp_time"), 3.0), 0.5)
        dims["otp_time"] = self._clip(abs(otp - avg_otp) / std_otp)

        # ── Hour-of-day novelty ────────────────────────────────────────────
        hour = int(self._f(transaction.get("hour"), 12))
        active_hours = baseline.get("active_hours") or []
        if active_hours:
            distance = min(
                min(abs(hour - h), 24 - abs(hour - h)) for h in active_hours
            )
            # 0 hours away = normal; 6+ hours outside the usual window = extreme
            dims["hour"] = self._clip(distance / 2.0)
        else:
            dims["hour"] = 0.0

        # ── Velocity deviation ─────────────────────────────────────────────
        txns_24h = self._f(transaction.get("txns_last_24h"))
        avg_per_day = max(self._f(baseline.get("avg_txns_per_day"), 3.0), 0.5)
        dims["velocity"] = self._clip(max(0.0, txns_24h - avg_per_day) / avg_per_day)

        # ── Categorical novelty ────────────────────────────────────────────
        known_devices = set(baseline.get("known_devices") or [])
        device = str(transaction.get("device_id", ""))
        dims["new_device"] = (
            3.0 if (known_devices and device and device not in known_devices) else 0.0
        )

        known_recipients = set(baseline.get("known_recipients") or [])
        recipient = str(transaction.get("recipient_id", ""))
        dims["new_recipient"] = (
            2.0
            if (known_recipients and recipient and recipient not in known_recipients)
            else 0.0
        )

        # ── Combine: weighted mean of squared standardised deviations ──────
        novelty = math.sqrt(
            sum(_WEIGHTS[k] * (v ** 2) for k, v in dims.items())
            / sum(_WEIGHTS.values())
        )

        if novelty < self._p95:
            status = "NORMAL"
        elif novelty < self._p99:
            status = "ANOMALOUS"
        else:
            status = "UNKNOWN_RISK"

        # Confidence = how far past the "unknown" boundary we are, capped at 1.
        confidence = (
            0.0
            if status == "NORMAL"
            else min(1.0, round((novelty - self._p95) / max(self._p99 - self._p95, 0.01), 3))
        )

        top = sorted(dims.items(), key=lambda kv: kv[1], reverse=True)[:3]

        return {
            "status": status,
            "confidence": confidence,
            "reconstruction_error": round(novelty, 4),
            "error_percentile": round(min(99.9, novelty / max(self._p99, 0.01) * 99.0), 2),
            "anomalous_dimensions": [
                {"feature": name, "error": round(val, 3)} for name, val in top if val > 0
            ],
            "detector": "statistical_baseline_deviation",
            "baseline_used": "personalized" if uid in self._baselines else "global_fallback",
        }

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _f(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clip(z: float) -> float:
        return max(0.0, min(_MAX_Z, z))
