"""
ai/utils/legacy_feature_adapter.py
==================================
Feature adapter for the SHIPPED XGBoost model.

THE PROBLEM THIS SOLVES
    `xgboost_fraud.pkl` / `scaler.pkl` were trained on one feature set, while
    `feature_engineering.FEATURE_COLS` (the current code) defines a different
    one. Both happen to have 22 columns, so nothing crashed — the model was
    silently being fed values in the wrong semantic positions (`amount` where
    it expected `hour_sin`, and so on). Its probability output was noise.

    Rather than ignore the model or retrain it, this adapter computes the
    exact features the saved model was trained on, from the same raw
    transaction dict, so the shipped weights become genuinely usable.

MODEL'S TRAINED FEATURE ORDER (from feature_cols.pkl):
    hour_sin, hour_cos, day_of_week, is_off_hours, in_active_window,
    is_new_device, otp_time_sec, otp_z_score, fast_otp_flag, slow_otp_flag,
    amount, amount_ratio, amount_z_score, amount_is_large, round_amount_flag,
    is_new_recipient, session_duration, txns_last_1h, txns_last_24h,
    burst_flag, new_device_and_recipient, round_and_new_recipient
"""

from __future__ import annotations

import math
from typing import Any

LEGACY_FEATURE_COLS = [
    "hour_sin", "hour_cos", "day_of_week", "is_off_hours", "in_active_window",
    "is_new_device", "otp_time_sec", "otp_z_score", "fast_otp_flag",
    "slow_otp_flag", "amount", "amount_ratio", "amount_z_score",
    "amount_is_large", "round_amount_flag", "is_new_recipient",
    "session_duration", "txns_last_1h", "txns_last_24h", "burst_flag",
    "new_device_and_recipient", "round_and_new_recipient",
]

# Thresholds mirroring the training-time definitions.
FAST_OTP_SEC = 4.0        # suspiciously fast — likely relayed/automated
SLOW_OTP_SEC = 20.0       # suspiciously slow — likely coerced/confused
LARGE_AMOUNT = 50_000.0   # "large" transaction flag
BURST_TXNS_1H = 3         # more than this in an hour = burst
OFF_HOURS = set(range(0, 6))  # 00:00–05:59


class LegacyFeatureAdapter:
    """Derives the shipped model's original feature vector."""

    def __init__(self, user_baselines: dict[str, Any]):
        self.baselines = user_baselines

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _f(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    # ── public API ─────────────────────────────────────────────────────────

    def derive_features(self, transaction: dict[str, Any]) -> dict[str, float]:
        uid = str(transaction.get("user_id", ""))
        baseline = self.baselines.get(uid) or self.baselines.get(
            "__global_fallback__", {}
        )

        hour = int(self._f(transaction.get("hour"), 12))
        amount = self._f(transaction.get("amount"))
        otp_time = self._f(transaction.get("otp_time_sec"), 9.5)

        avg_amount = self._f(baseline.get("avg_amount"), 5000.0)
        std_amount = max(self._f(baseline.get("std_amount"), 2000.0), 1.0)
        avg_otp = self._f(baseline.get("avg_otp_time"), 8.0)
        std_otp = max(self._f(baseline.get("std_otp_time"), 3.0), 0.5)
        active_hours = set(baseline.get("active_hours") or [])
        known_devices = set(baseline.get("known_devices") or [])
        known_recipients = set(baseline.get("known_recipients") or [])

        txns_1h = self._f(transaction.get("txns_last_1h"))
        txns_24h = self._f(transaction.get("txns_last_24h"))

        is_new_device = float(
            bool(known_devices)
            and str(transaction.get("device_id", "")) not in known_devices
        )
        is_new_recipient = float(
            bool(known_recipients)
            and str(transaction.get("recipient_id", "")) not in known_recipients
        )
        round_flag = float(amount > 0 and amount % 1000 == 0)

        hour_rad = hour * 2 * math.pi / 24

        features = {
            "hour_sin": math.sin(hour_rad),
            "hour_cos": math.cos(hour_rad),
            "day_of_week": self._f(transaction.get("day_of_week"), 2),
            "is_off_hours": float(hour in OFF_HOURS),
            "in_active_window": float(
                bool(transaction.get("in_active_window", hour in active_hours))
            ),
            "is_new_device": is_new_device,
            "otp_time_sec": otp_time,
            "otp_z_score": (otp_time - avg_otp) / std_otp,
            "fast_otp_flag": float(otp_time < FAST_OTP_SEC),
            "slow_otp_flag": float(otp_time > SLOW_OTP_SEC),
            "amount": amount,
            "amount_ratio": amount / avg_amount if avg_amount > 0 else 0.0,
            "amount_z_score": (amount - avg_amount) / std_amount,
            "amount_is_large": float(amount > LARGE_AMOUNT),
            "round_amount_flag": round_flag,
            "is_new_recipient": is_new_recipient,
            "session_duration": self._f(transaction.get("session_duration"), 120.0),
            "txns_last_1h": txns_1h,
            "txns_last_24h": txns_24h,
            "burst_flag": float(txns_1h > BURST_TXNS_1H),
            "new_device_and_recipient": is_new_device * is_new_recipient,
            "round_and_new_recipient": round_flag * is_new_recipient,
        }
        return features

    def derive_features_as_row(self, transaction: dict[str, Any]) -> list[float]:
        """Ordered vector matching the saved model's training column order."""
        f = self.derive_features(transaction)
        return [float(f[col]) for col in LEGACY_FEATURE_COLS]
