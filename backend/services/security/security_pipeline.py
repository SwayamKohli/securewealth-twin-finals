"""
services/security/security_pipeline.py
======================================
Unified backend security pipeline for investment transactions.

This is the ONLY place the transaction flow talks to the security/AI stack
(task 2.4: frontend must never orchestrate AI modules; task 2.6: every
investment is fraud-checked in real time before completion).

Pipeline (Behavior -> Fraud ML -> Zero-Day -> Risk -> Decision):

    Investment Request
        -> Behavior Engine      (signals from the user's real history)
        -> Fraud Engine         (XGBoost + rule fusion, loaded from disk)
        -> Zero-Day Detector    (autoencoder novelty, loaded from disk)
        -> Risk Engine          (score fusion incl. device trust)
        -> Decision Engine      (ALLOW / WARN / CHALLENGE / BLOCK)

Degradation policy:
  - ML engines load lazily, once per process. If artifacts/deps are missing
    the pipeline logs it and continues with rule-based signals only
    (loosely coupled AI — the demo never hard-fails on a missing .pkl).
  - Any unexpected internal error produces a FAIL-SAFE decision record
    (CHALLENGE), never a silent ALLOW.
"""

from __future__ import annotations

import logging
import statistics
import uuid as uuid_lib
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from database.repositories.behavioural_profile_repository import (
    BehaviouralProfileRepository,
)
from database.repositories.device_repository import DeviceRepository
from database.repositories.transaction_repository import TransactionRepository
from models.device import Device
from models.enums import TrustStatus
from security.behavior_engine import BehaviorEngine, BehaviorInput
from security.decision_engine import (
    DecisionEngine,
    DecisionRecord,
    TransactionContext,
)
from security.risk_engine import EnvironmentInput, RiskEvaluationInput
from security.unknown_risk_handler import UnknownRiskEvent

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

# Defaults used only when the user has no history yet (cold start).
_DEFAULT_MEDIAN_AMOUNT = 5000.0
_DEFAULT_STD_AMOUNT = 2000.0
_DEFAULT_OTP_ENTRY_MS = 9500

# ──────────────────────────────────────────────────────────────────────────────
# Lazy ML engine singletons (loaded once per process, degrade gracefully)
# ──────────────────────────────────────────────────────────────────────────────

_fraud_engine: Any = None
_fraud_engine_failed = False
_zero_day_detector: Any = None
_zero_day_failed = False

# Which zero-day detector is live, and why. Exposed via /health/services so the
# answer to "is the autoencoder actually running?" is checkable rather than a
# claim. Same reasoning as llm_source for the explainers: a silent fallback and
# a working model look identical from the outside.
_zero_day_status: dict = {
    "detector": "none",
    "engine": "unavailable",
    "detail": "not initialised yet",
}


def zero_day_status() -> dict:
    """Snapshot of which novelty detector is in use. Safe to call anytime."""
    get_zero_day_detector()          # force lazy init
    return dict(_zero_day_status)


def get_fraud_engine():
    """Return the shared FraudIntelligenceEngine, or None if unavailable."""
    global _fraud_engine, _fraud_engine_failed
    if _fraud_engine is None and not _fraud_engine_failed:
        try:
            from ai.engines.fraud_engine import FraudIntelligenceEngine

            _fraud_engine = FraudIntelligenceEngine.from_disk()
            logger.info("SecurityPipeline: Fraud ML engine loaded.")
        except Exception as exc:  # missing artifacts / deps
            _fraud_engine_failed = True
            logger.warning(
                "SecurityPipeline: Fraud ML engine unavailable (%s). "
                "Continuing with rule-based signals only.",
                exc,
            )
    return _fraud_engine


def get_zero_day_detector():
    """
    Return the shared zero-day detector.

    Preference order:
      1. ZeroDayDetector — PyTorch autoencoder (needs torch + autoencoder.pth)
      2. StatisticalZeroDayDetector — numpy baseline-deviation detector

    The fallback means Unknown-Risk classification is ALWAYS active; the
    architecture never silently loses a layer because an optional ML artifact
    is missing.
    """
    global _zero_day_detector, _zero_day_failed
    if _zero_day_detector is None and not _zero_day_failed:
        try:
            from ai.engines.zero_day_detector import ZeroDayDetector

            _zero_day_detector = ZeroDayDetector.from_disk()
            _zero_day_status.update(
                detector="autoencoder",
                engine="PyTorch autoencoder (22 features, reconstruction error)",
                detail="ai/engines/models/autoencoder.pth",
            )
            logger.info("SecurityPipeline: Zero-Day autoencoder loaded.")
        except Exception as exc:
            logger.info(
                "SecurityPipeline: autoencoder unavailable (%s) — "
                "falling back to the statistical zero-day detector.",
                exc,
            )
            try:
                from ai.engines.statistical_zero_day import (
                    StatisticalZeroDayDetector,
                )

                _zero_day_detector = StatisticalZeroDayDetector.from_disk()
                _zero_day_status.update(
                    detector="statistical",
                    engine="numpy baseline-deviation detector",
                    detail=f"autoencoder unavailable: {exc}",
                )
                logger.info(
                    "SecurityPipeline: statistical Zero-Day detector active."
                )
            except Exception as exc2:
                _zero_day_failed = True
                _zero_day_status.update(
                    detector="none", engine="unavailable", detail=str(exc2)
                )
                logger.warning(
                    "SecurityPipeline: no zero-day detector available (%s). "
                    "Continuing without novelty detection.",
                    exc2,
                )
    return _zero_day_detector


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────────────


class SecurityPipeline:
    """Evaluates one investment request and returns a DecisionRecord."""

    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.behavior_engine = BehaviorEngine()
        self.decision_engine = DecisionEngine()

    # ── public ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        *,
        user_id: UUID,
        account_id: UUID,
        amount: float,
        channel: str,
        recipient_id: str,
        transaction_id: str | None = None,
    ) -> DecisionRecord:
        """
        Run the full pipeline. Never raises: on internal error a fail-safe
        CHALLENGE record is returned instead of a silent ALLOW.
        """
        txn_id = transaction_id or str(uuid_lib.uuid4())
        try:
            return self._evaluate(
                user_id=user_id,
                account_id=account_id,
                amount=amount,
                channel=channel,
                recipient_id=recipient_id,
                txn_id=txn_id,
            )
        except Exception:
            logger.exception(
                "SecurityPipeline: evaluation failed for txn %s — "
                "returning FAIL-SAFE CHALLENGE.",
                txn_id,
            )
            return self._fail_safe_record(
                txn_id=txn_id,
                account_id=account_id,
                amount=amount,
                channel=channel,
            )

    # ── internals ─────────────────────────────────────────────────────────

    def _evaluate(
        self,
        *,
        user_id: UUID,
        account_id: UUID,
        amount: float,
        channel: str,
        recipient_id: str,
        txn_id: str,
    ) -> DecisionRecord:
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST)

        # 1) Real history (last 30 days)
        recent = self.transaction_repository.get_filtered(
            user_id=user_id,
            from_date=now_utc - timedelta(days=30),
            to_date=now_utc,
        )
        amounts = [float(t.amount) for t in recent]
        median_amount = (
            statistics.median(amounts) if len(amounts) >= 3 else _DEFAULT_MEDIAN_AMOUNT
        )
        std_amount = (
            statistics.pstdev(amounts) if len(amounts) >= 3 else _DEFAULT_STD_AMOUNT
        )

        profile = BehaviouralProfileRepository.get_by_user_id(self.db, user_id)
        otp_entry_ms = _DEFAULT_OTP_ENTRY_MS
        if profile is not None and getattr(profile, "average_otp_time", None):
            try:
                otp_entry_ms = int(float(profile.average_otp_time) * 1000)
            except (TypeError, ValueError):
                pass

        # 2) Behavior Engine
        behavior_signals = self.behavior_engine.analyze(
            BehaviorInput(
                transaction_hour_ist=now_ist.hour,
                amount=amount,
                ninety_day_median=median_amount,
                ninety_day_std=std_amount,
                recipient_id=recipient_id,
                known_recipients=[t.merchant_name for t in recent],
                recent_transaction_timestamps=[
                    int(t.transaction_time.timestamp() * 1000) for t in recent[-5:]
                ],
                last_20_amounts=amounts[-20:],
                otp_entry_ms=otp_entry_ms,
            )
        )

        # 3) Fraud ML + Zero-Day (shared raw transaction dict)
        device = self._current_device(user_id)
        raw_txn = self._build_raw_transaction(
            user_id=user_id,
            device=device,
            recipient_id=recipient_id,
            amount=amount,
            now_ist=now_ist,
            recent=recent,
            now_utc=now_utc,
        )

        ai_fraud_probability = 0.0
        ai_confidence = 0.0
        fraud_result: dict[str, Any] | None = None
        engine = get_fraud_engine()
        if engine is not None:
            try:
                fraud_result = engine.evaluate(raw_txn)
                ai_fraud_probability = float(fraud_result["fraud_probability"])
                ai_confidence = float(fraud_result["confidence"])
            except Exception:
                logger.exception("SecurityPipeline: fraud engine evaluate failed.")

        unknown_risk_event: UnknownRiskEvent | None = None
        detector = get_zero_day_detector()
        if detector is not None:
            try:
                zd = detector.detect(raw_txn)
                if zd.get("status") in ("ANOMALOUS", "UNKNOWN_RISK"):
                    unknown_risk_event = UnknownRiskEvent(
                        status=zd["status"],
                        confidence=float(zd.get("confidence", 0.0)),
                        transaction_id=txn_id,
                        detail={
                            "error_percentile": zd.get("error_percentile"),
                            "anomalous_dimensions": zd.get("anomalous_dimensions"),
                        },
                    )
            except Exception:
                logger.exception("SecurityPipeline: zero-day detection failed.")

        # 4) Risk + Decision
        risk_input = RiskEvaluationInput(
            behavior_signals=behavior_signals,
            environment=self._environment_input(),
            device_trust=self._device_trust(device),
            ai_fraud_probability=ai_fraud_probability,
            ai_confidence=ai_confidence,
        )

        record = self.decision_engine.decide(
            TransactionContext(
                transaction_id=txn_id,
                account_id=str(account_id),
                amount=amount,
                channel=channel,
                risk_input=risk_input,
                unknown_risk_event=unknown_risk_event,
            )
        )

        # Attach ML + context detail so downstream consumers (audit,
        # explainability) see exactly what the models saw.
        if isinstance(record.security_signals, dict):
            record.security_signals["context"] = {
                "device_id": str(device.device_id) if device is not None else None,
                "recipient": recipient_id,
            }
            if fraud_result is not None:
                record.security_signals["ai_fraud"] = {
                    "fraud_probability": fraud_result["fraud_probability"],
                    "confidence": fraud_result["confidence"],
                    "baseline_used": fraud_result.get("baseline_used"),
                    "top_risk_factors": (fraud_result.get("risk_factors") or [])[:3],
                }
        return record

    def _current_device(self, user_id: UUID) -> Device | None:
        try:
            devices = DeviceRepository.get_user_devices(self.db, user_id)
        except Exception:
            logger.exception("SecurityPipeline: device lookup failed.")
            return None
        if not devices:
            return None
        return max(devices, key=lambda d: d.last_seen or d.first_seen)

    @staticmethod
    def _device_trust(device: Device | None) -> dict[str, Any]:
        """Map the Device model onto the Risk Engine's device-trust contract."""
        if device is None:
            return {
                "device_status": "NEW_DEVICE",
                "device_confidence": 30,
                "device_age_days": 0,
                "security_signals": ["NO_REGISTERED_DEVICE"],
            }

        age_days = 0
        if device.first_seen is not None:
            first_seen = device.first_seen
            if first_seen.tzinfo is None:
                first_seen = first_seen.replace(tzinfo=timezone.utc)
            age_days = max(0, (datetime.now(timezone.utc) - first_seen).days)

        status_map = {
            TrustStatus.TRUSTED: "TRUSTED_DEVICE",
            TrustStatus.PENDING: "NEW_DEVICE",
            TrustStatus.UNTRUSTED: "SUSPICIOUS_DEVICE",
        }
        device_status = status_map.get(device.trust_status, "NEW_DEVICE")

        # Confidence heuristic: trusted devices gain confidence with age.
        if device.trust_status == TrustStatus.TRUSTED:
            confidence = min(100, 60 + age_days)
        elif device.trust_status == TrustStatus.PENDING:
            confidence = 40
        else:
            confidence = 10

        return {
            "device_status": device_status,
            "device_confidence": confidence,
            "device_age_days": age_days,
            "security_signals": [device.trust_status.value],
        }

    @staticmethod
    def _environment_input() -> EnvironmentInput:
        # Environmental capture (IP geo / network type) is not yet wired from
        # the mobile client; use neutral values so environment neither inflates
        # nor masks risk. Extended when the client starts sending context.
        return EnvironmentInput(
            ip_region="UNKNOWN",
            last_login_region="UNKNOWN",
            time_since_last_login_ms=0,
            network_type="MOBILE_DATA",
        )

    @staticmethod
    def _build_raw_transaction(
        *,
        user_id: UUID,
        device: Device | None,
        recipient_id: str,
        amount: float,
        now_ist: datetime,
        now_utc: datetime,
        recent: list,
    ) -> dict[str, Any]:
        """Raw dict contract shared by FraudIntelligenceEngine and ZeroDayDetector."""
        one_hour_ago = now_utc - timedelta(hours=1)
        one_day_ago = now_utc - timedelta(hours=24)

        def _aware(ts: datetime) -> datetime:
            return ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)

        txns_last_1h = sum(1 for t in recent if _aware(t.transaction_time) >= one_hour_ago)
        txns_last_24h = sum(1 for t in recent if _aware(t.transaction_time) >= one_day_ago)

        return {
            "user_id": str(user_id),
            "device_id": str(device.device_id) if device is not None else "unknown",
            "recipient_id": recipient_id,
            "amount": amount,
            "hour": now_ist.hour,
            "day_of_week": now_ist.weekday(),
            "otp_time_sec": 8.0,
            "session_duration": 120.0,
            "txns_last_1h": txns_last_1h,
            "txns_last_24h": txns_last_24h,
            "in_active_window": 6 <= now_ist.hour <= 23,
        }

    @staticmethod
    def _fail_safe_record(
        *,
        txn_id: str,
        account_id: UUID,
        amount: float,
        channel: str,
    ) -> DecisionRecord:
        """Security must FAIL SAFE: an internal error means extra verification,
        never a silent approval."""
        return DecisionRecord(
            transaction_id=txn_id,
            account_id=str(account_id),
            amount=amount,
            channel=channel,
            decision="CHALLENGE",
            risk_score=60,
            security_signals={"pipeline_error": True},
            challenge_required=True,
            challenge_type="OTP",
            report=(
                "We could not fully verify this investment automatically, "
                "so an extra identity check is required."
            ),
            audit_note="FAIL_SAFE: security pipeline error — defaulted to CHALLENGE.",
            decision_timestamp=datetime.now(timezone.utc).isoformat(),
        )
