"""
device_trust.py
================
SecureWealth Twin — Security Layer
Module 7:  Device Trust Service
Owner:     Aayat (Security Engineer) / Mahak (Repository + Schema)
Phase:     Finals Implementation — Schema v3.0 Alignment

Purpose
-------
Determine device trust level for the device initiating a transaction.
Produces a structured DeviceTrustResult consumed directly by risk_engine.py.

Module 7 spec (outputs):
    - device_status      : KNOWN | NEW | TRUSTED | INACTIVE
                            (+ SUSPICIOUS / ZERO_DAY as fraud-detection
                              extensions layered on top of the spec — see
                              "Fraud extension" note below)
    - device_age_days    : current_date - first_seen_date
    - device_confidence  : 0-100, derived from first_seen, last_seen,
                            login frequency, and successful transaction
                            history
        100 = Trusted Device
        70  = Known Device
        40  = Previously Seen But Inactive
        10  = New Device

Interface note — FIRST_TIME_USER vs NEW_DEVICE:
    Internally this module tracks a genuine FIRST_TIME_USER state (a user
    with zero devices at all — the bootstrap case). This distinction is
    useful for internal logging/trust_status, but it is NOT part of the
    agreed external interface, which only exposes: NEW | KNOWN | TRUSTED |
    INACTIVE (plus the SUSPICIOUS/ZERO_DAY fraud extensions). So at the
    to_dict() boundary, FIRST_TIME_USER is collapsed into NEW_DEVICE before
    it ever reaches risk_engine.py or any other consumer. Nothing outside
    this module ever sees "FIRST_TIME_USER".

Interface note — risk_penalty removed:
    device_trust.py no longer computes or returns a risk penalty. This
    module's job is to evaluate TRUST, not to assign RISK. Converting a
    trust classification into a numeric penalty is security_rules.py's
    job (same separation already used for the Fraud Engine — AI doesn't
    assign risk, Security does). DeviceTrustResult therefore only reports
    device_status, device_age_days, device_confidence, and
    security_signals. Risk Engine / security_rules.py is expected to map
    device_status -> penalty on its own side.

Fraud extension (not in the original Module 7 list, added deliberately):
    SUSPICIOUS_DEVICE and ZERO_DAY_DEVICE are kept as additional statuses
    so this module can still warn risk_engine.py about spoofed / rooted /
    emulated / deactivated devices. Without these, device_trust.py would
    have no way to surface a fraud signal at all, which conflicts with
    the project's stated Fraud Prevention objective. These two statuses
    take priority over the three ordinary Module 7 statuses — a device is
    only classified TRUSTED/KNOWN/INACTIVE/NEW once it has passed the
    suspicion checks.

Pipeline position:
    Mobile App → Device Trust Service → Risk Engine → Decision Engine → Audit Service

    NOTE: "SIM Trust Service" has been intentionally removed from this
    pipeline. SIM verification is out of scope for the Finals MVP.
    Nothing in this module reads or writes `sim_id`.

Architecture
------------
This module contains ZERO persistence logic. All device state is read and
written exclusively through a DeviceRepository protocol (dependency
injected at construction time). This service performs pure evaluation
logic only — no in-memory registries, no module-level dicts, no Map().

Schema v3.0 — devices table (owned by database/security_repository.py):

    devices
    ----------------
    device_id            UUID PK, backend-generated (gen_random_uuid())
    user_id               UUID FK -> users.user_id
    device_identifier     VARCHAR(255) UNIQUE — client-supplied stable ID
                           (React Native: DeviceInfo.getUniqueId())
    device_name           VARCHAR(100)
    device_type           VARCHAR(30)
    fingerprint_hash        TEXT — SERVER-COMPUTED, never trusted from client
    trust_score            NUMERIC(3,2) DEFAULT 0.40 — internal fraud signal,
                           NOT the same thing as device_confidence
    login_count             INTEGER DEFAULT 0
    trust_status            VARCHAR(20) — OUTPUT ONLY, mirrors device_status,
                           written by this service, never read as an input
    is_active              BOOLEAN DEFAULT TRUE
    first_seen              TIMESTAMPTZ
    last_seen               TIMESTAMPTZ
    created_at              TIMESTAMPTZ
    updated_at              TIMESTAMPTZ

Schema v3.0 — transactions table addition required by this module:

    transactions.device_id  UUID FK -> devices.device_id (nullable)

    Without this column, "successful transaction history" (a required
    input to device_confidence per Module 7) is not reachable from any
    table. This module calls repository.get_successful_transaction_count()
    which is expected to filter transactions by this column.

trust_score vs. device_confidence — these are deliberately two different
numbers with two different jobs:
    trust_score        : a slow-moving internal float (0.0-1.0), nudged
                          +0.02 on clean logins and -0.15 on suspicious
                          ones. Used ONLY to detect fraud (LOW_TRUST_SCORE
                          signal, SUSPICIOUS_DEVICE classification).
    device_confidence  : the Module-7-mandated 0-100 output, computed
                          fresh each call from first_seen / last_seen /
                          login_count / transaction history. This is what
                          risk_engine.py actually consumes.

The repository is expected to expose (at minimum):
    get_user_devices(user_id)                          -> list[DeviceRow]
    get_device_by_identifier(user_id, device_identifier) -> DeviceRow | None
    save_device(device_row)                             -> DeviceRow
    update_device(device_row)                            -> DeviceRow
    get_successful_transaction_count(device_id)          -> int

This module defines a `DeviceRepository` Protocol describing this contract.
The concrete repository implementation lives in
`database/security_repository.py` and is NOT implemented here.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class DeviceStatus(str, Enum):
    """
    All possible device trust states.

    Module 7 core statuses:
        FIRST_TIME_USER  — User has no device history at all. Bootstrap
                            case; not suspicious, expected for genuinely
                            new customers. (Not explicitly named in the
                            Module 7 spec, but required — there has to be
                            SOME status for the very first device ever
                            registered on an account.)
        NEW_DEVICE        — User has prior devices, but this specific
                            device has never been registered before.
        KNOWN_DEVICE      — Device exists and is active, but has not yet
                            met the bar for TRUSTED.
        TRUSTED_DEVICE    — Device has sufficient age, login frequency,
                            and successful transaction history.
        INACTIVE_DEVICE   — Device was seen before but has gone quiet
                            beyond the inactivity threshold ("previously
                            seen but inactive").

    Fraud-extension statuses (take priority over the above):
        SUSPICIOUS_DEVICE — Fingerprint mismatch, root/emulator/automation
                            indicators, deactivated device, or trust_score
                            below threshold.
        ZERO_DAY_DEVICE   — Unknown platform or impossible attribute
                            combinations. Highest device risk category.
    """
    FIRST_TIME_USER   = "FIRST_TIME_USER"
    NEW_DEVICE        = "NEW_DEVICE"
    KNOWN_DEVICE      = "KNOWN_DEVICE"
    TRUSTED_DEVICE    = "TRUSTED_DEVICE"
    INACTIVE_DEVICE   = "INACTIVE_DEVICE"
    SUSPICIOUS_DEVICE = "SUSPICIOUS_DEVICE"
    ZERO_DAY_DEVICE   = "ZERO_DAY_DEVICE"


class DeviceSignal(str, Enum):
    """Security signals attachable to a DeviceTrustResult (explainability)."""
    FIRST_TIME_USER       = "FIRST_TIME_USER"
    NEW_DEVICE            = "NEW_DEVICE"
    KNOWN_DEVICE          = "KNOWN_DEVICE"
    TRUSTED_DEVICE        = "TRUSTED_DEVICE"
    INACTIVE_DEVICE       = "INACTIVE_DEVICE"
    LOW_TRUST_SCORE       = "LOW_TRUST_SCORE"
    FINGERPRINT_MISMATCH  = "FINGERPRINT_MISMATCH"
    ROOT_DETECTED         = "ROOT_DETECTED"
    EMULATOR_DETECTED     = "EMULATOR_DETECTED"
    AUTOMATION_DETECTED   = "AUTOMATION_DETECTED"
    DEVICE_DEACTIVATED    = "DEVICE_DEACTIVATED"
    ZERO_DAY_DEVICE       = "ZERO_DAY_DEVICE"
    UNKNOWN_FINGERPRINT   = "UNKNOWN_FINGERPRINT"
    UNKNOWN_PLATFORM      = "UNKNOWN_PLATFORM"
    LOW_CONFIDENCE        = "LOW_CONFIDENCE"
    HIGH_CONFIDENCE       = "HIGH_CONFIDENCE"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DeviceTrustConfig:
    """
    Centralised, immutable configuration for all device trust thresholds
    and penalty scores.
    """

    # ── Risk penalties: REMOVED. ─────────────────────────────────────────
    # Penalty scoring now lives in security_rules.py, which maps
    # device_status -> penalty on its own side. device_trust.py evaluates
    # trust only; it does not assign risk.

    # ── device_confidence bands (Module 7 spec, 0-100) ──────────────────────
    confidence_first_time_user: int = 60   # bootstrap case, not in spec list
    confidence_new:              int = 10
    confidence_known:            int = 70
    confidence_trusted:          int = 100
    confidence_inactive:         int = 40
    confidence_suspicious_min:   int = 10
    confidence_suspicious_max:   int = 30
    confidence_zero_day_min:     int = 0
    confidence_zero_day_max:     int = 20

    # ── device_confidence classification thresholds ─────────────────────────
    trusted_min_login_count:       int = 5
    trusted_min_transaction_count: int = 3
    trusted_min_age_days:          int = 7
    inactivity_threshold_days:     int = 30

    # ── trust_score (internal fraud signal, 0.0-1.0) ─────────────────────────
    initial_trust_score_first_device: float = 0.40
    initial_trust_score_new_device:   float = 0.30
    trust_score_penalty_step:         float = 0.15
    trust_score_reward_step:          float = 0.02
    low_trust_cutoff:                 float = 0.35

    # ── fingerprint drift tolerance (unused fields don't count against it) ──
    fingerprint_similarity_threshold: float = 0.70

    # ── confidence annotation cutoffs ────────────────────────────────────────
    low_confidence_cutoff:  int = 50
    high_confidence_cutoff: int = 95


DEFAULT_CONFIG = DeviceTrustConfig()

# Hardware-constant attribute keys only. Anything that legitimately changes
# session to session on the SAME physical device (OS version, timezone,
# language, screen scaling, etc.) must NEVER go in here — including it
# would cause false FINGERPRINT_MISMATCH hits on genuine users.
FINGERPRINT_FIELDS: tuple[str, ...] = ("brand", "model", "platform", "is_tablet", "total_memory_gb")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DeviceRow:
    """In-flight representation of a row from the `devices` table (schema v3.0)."""
    user_id:           str
    device_identifier: str
    device_id:         str | None = None   # backend-generated UUID, None until persisted
    device_name:       str | None = None
    device_type:       str | None = None
    fingerprint_hash:  str | None = None
    trust_score:       float = 0.30
    login_count:       int = 0
    trust_status:      str | None = None
    is_active:         bool = True
    first_seen:        str = ""
    last_seen:         str = ""


@dataclass
class DeviceContext:
    """
    Incoming payload describing the current transaction's device.
    Populated by the backend AFTER authentication, before calling
    evaluate_device_trust(). user_id must come from the authenticated
    session, never from the client body.
    """
    user_id:           str
    device_identifier: str
    attributes: dict[str, Any] = field(default_factory=dict)
    # attributes (raw, from React Native, see integration notes at bottom):
    #   brand, model, platform, is_tablet, total_memory_gb   <- fingerprint inputs
    #   system_version, timezone_offset_minutes, language,
    #   screen_width, user_agent                              <- context only
    #   is_rooted, is_emulator, automation_flags               <- suspicion inputs


@dataclass
class DeviceTrustResult:
    """
    Structured output returned by DeviceTrustService.evaluate().

    NOTE: no risk_penalty field here on purpose. Trust evaluation and risk
    scoring are separate concerns — security_rules.py / risk_engine.py owns
    converting device_status into a penalty.
    """
    device_status:     DeviceStatus
    device_age_days:   int
    device_confidence: int
    security_signals:  list[DeviceSignal]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise to the Risk Engine's expected JSON format.

        FIRST_TIME_USER is deliberately collapsed to NEW_DEVICE here — it's
        an internal-only distinction, not part of the agreed external
        interface (NEW | KNOWN | TRUSTED | INACTIVE, + fraud extensions).
        """
        external_status = self.device_status
        if external_status == DeviceStatus.FIRST_TIME_USER:
            external_status = DeviceStatus.NEW_DEVICE

        return {
            "device_status":     external_status.value,
            "device_age_days":   self.device_age_days,
            "device_confidence": self.device_confidence,
            "security_signals":  [s.value for s in self.security_signals],
        }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — REPOSITORY CONTRACT (Protocol — NOT an implementation)
# ─────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class DeviceRepository(Protocol):
    """
    Structural contract for device persistence. Concrete implementation
    lives in `database/security_repository.py`.
    """

    def get_user_devices(self, user_id: str) -> list[DeviceRow]:
        """Return all DeviceRows registered for a given user_id."""
        ...

    def get_device_by_identifier(self, user_id: str, device_identifier: str) -> DeviceRow | None:
        """
        Look up a device by the client-supplied device_identifier
        (React Native DeviceInfo.getUniqueId()), scoped to a user.
        This is the primary lookup used on every evaluation.
        """
        ...

    def save_device(self, device: DeviceRow) -> DeviceRow:
        """Insert a new DeviceRow (backend generates device_id) and return it."""
        ...

    def update_device(self, device: DeviceRow) -> DeviceRow:
        """Persist changes to an existing DeviceRow and return it."""
        ...

    def get_successful_transaction_count(self, device_id: str) -> int:
        """
        Count successful transactions associated with this device_id via
        transactions.device_id. Required input for device_confidence.
        """
        ...


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — INTERNAL PURE HELPERS (no I/O, no persistence)
# ─────────────────────────────────────────────────────────────────────────────

def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 timestamp, defaulting to epoch if empty/invalid."""
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _days_between(earlier: str, later: datetime) -> int:
    """Whole days between an ISO timestamp and a datetime, floor at 0."""
    delta = later.date() - _parse_iso(earlier).date()
    return max(0, delta.days)


def _compute_fingerprint_hash(attributes: dict[str, Any]) -> str:
    """
    Server-side fingerprint, built ONLY from hardware-constant fields
    (see FINGERPRINT_FIELDS). Never accepts a pre-computed hash from the
    client — always recomputed here from raw attributes so a client can't
    forge or replay a stale hash.
    """
    parts = [str(attributes.get(f, "unknown")) for f in FINGERPRINT_FIELDS]
    source = "|".join(parts)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _detect_root_or_emulator_or_automation(attributes: dict[str, Any]) -> list[DeviceSignal]:
    """Inspect device attributes for root, emulator, or automation indicators."""
    found: list[DeviceSignal] = []

    if bool(attributes.get("is_rooted", False)):
        found.append(DeviceSignal.ROOT_DETECTED)

    if bool(attributes.get("is_emulator", False)):
        found.append(DeviceSignal.EMULATOR_DETECTED)

    automation_flags = attributes.get("automation_flags") or []
    if isinstance(automation_flags, list) and len(automation_flags) > 0:
        found.append(DeviceSignal.AUTOMATION_DETECTED)

    return found


def _detect_impossible_attributes(attributes: dict[str, Any]) -> bool:
    """
    Detect internally inconsistent attribute combinations suggesting a
    spoofed or fabricated environment.
    """
    platform = str(attributes.get("platform", "")).strip()
    if not platform:
        return True

    ua = str(attributes.get("user_agent", "")).lower()
    is_mobile_ua = any(tok in ua for tok in ("mobile", "android", "iphone", "ipad"))
    try:
        screen_width = int(attributes.get("screen_width", 0))
        if is_mobile_ua and screen_width > 480:
            return True
    except (TypeError, ValueError):
        return True

    try:
        tz_offset = int(attributes.get("timezone_offset_minutes", 0))
        if not (-720 <= tz_offset <= 840):
            return True
    except (TypeError, ValueError):
        return True

    return False


def _is_unknown_platform(attributes: dict[str, Any]) -> bool:
    platform = str(attributes.get("platform", "")).strip().lower()
    return platform in ("", "unknown", "null", "none")


def _classify_ordinary_status(
    recency_days: int,
    login_count: int,
    transaction_count: int,
    age_days: int,
    config: DeviceTrustConfig,
) -> DeviceStatus:
    """
    Classify a non-suspicious, previously-registered device into
    TRUSTED / KNOWN / INACTIVE per Module 7's four inputs.
    """
    if recency_days > config.inactivity_threshold_days:
        return DeviceStatus.INACTIVE_DEVICE

    if (
        login_count >= config.trusted_min_login_count
        and transaction_count >= config.trusted_min_transaction_count
        and age_days >= config.trusted_min_age_days
    ):
        return DeviceStatus.TRUSTED_DEVICE

    return DeviceStatus.KNOWN_DEVICE


def _confidence_for_ordinary_status(status: DeviceStatus, config: DeviceTrustConfig) -> int:
    return {
        DeviceStatus.TRUSTED_DEVICE:  config.confidence_trusted,
        DeviceStatus.KNOWN_DEVICE:    config.confidence_known,
        DeviceStatus.INACTIVE_DEVICE: config.confidence_inactive,
    }[status]


def _confidence_for_fraud_status(status: DeviceStatus, trust_score: float, config: DeviceTrustConfig) -> int:
    """SUSPICIOUS/ZERO_DAY confidence scales with how far trust_score has fallen."""
    t = max(0.0, min(1.0, trust_score))
    if status == DeviceStatus.SUSPICIOUS_DEVICE:
        ratio = max(0.0, min(1.0, t / config.low_trust_cutoff)) if config.low_trust_cutoff else 0.0
        span = config.confidence_suspicious_max - config.confidence_suspicious_min
        return int(config.confidence_suspicious_min + ratio * span)
    if status == DeviceStatus.ZERO_DAY_DEVICE:
        return config.confidence_zero_day_min
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — DEVICE TRUST SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class DeviceTrustService:
    """
    Stateless evaluation service for device trust. Holds no device state
    itself — all reads/writes go through the injected DeviceRepository.

    Usage
    -----
        service = DeviceTrustService(repository=my_device_repo)
        result  = service.evaluate(DeviceContext(
            user_id="U123", device_identifier="IDFV-...", attributes={...}
        ))
        payload = result.to_dict()  # → risk_engine.py
    """

    def __init__(self, repository: DeviceRepository, config: DeviceTrustConfig | None = None) -> None:
        self._repository: DeviceRepository = repository
        self._config: DeviceTrustConfig = config or DEFAULT_CONFIG

    # ──────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────

    def evaluate(self, context: DeviceContext) -> DeviceTrustResult:
        """
        Main entry point.

        Decision flow
        -------------
        1. No devices at all for this user  → FIRST_TIME_USER
        2. This device_identifier not found → NEW_DEVICE
        3. Device found, deactivated        → SUSPICIOUS_DEVICE
        4. Device found, suspicion checks    → SUSPICIOUS_DEVICE
           (root / emulator / automation / fingerprint mismatch / low trust_score)
        5. Device found, impossible attrs    → ZERO_DAY_DEVICE
        6. Otherwise classify TRUSTED / KNOWN / INACTIVE using
           first_seen, last_seen, login_count, transaction history.
        """
        cfg = self._config
        now = _utc_now()
        signals: list[DeviceSignal] = []

        # ── Step 1: First-time user ──────────────────────────────────────
        user_devices = self._repository.get_user_devices(context.user_id)
        if not user_devices:
            self._register_new_device(
                context, now, initial_trust_score=cfg.initial_trust_score_first_device,
                trust_status=DeviceStatus.FIRST_TIME_USER.value,
            )
            signals.append(DeviceSignal.FIRST_TIME_USER)
            return self._finalise(
                DeviceStatus.FIRST_TIME_USER, cfg.confidence_first_time_user,
                signals, age_days=0,
            )

        # ── Step 2: Specific device lookup ──────────────────────────────
        device_row = self._repository.get_device_by_identifier(context.user_id, context.device_identifier)
        if device_row is None:
            self._register_new_device(
                context, now, initial_trust_score=cfg.initial_trust_score_new_device,
                trust_status=DeviceStatus.NEW_DEVICE.value,
            )
            signals.append(DeviceSignal.NEW_DEVICE)
            return self._finalise(
                DeviceStatus.NEW_DEVICE, cfg.confidence_new, signals, age_days=0,
            )

        age_days = _days_between(device_row.first_seen, now)
        fingerprint_now = _compute_fingerprint_hash(context.attributes)

        # ── Step 3: Deactivated device ──────────────────────────────────
        if not device_row.is_active:
            signals.append(DeviceSignal.DEVICE_DEACTIVATED)
            updated = self._touch_device(device_row, context, now, fingerprint_now, penalise=True,
                                          status_label=DeviceStatus.SUSPICIOUS_DEVICE.value)
            confidence = _confidence_for_fraud_status(DeviceStatus.SUSPICIOUS_DEVICE, updated.trust_score, cfg)
            return self._finalise(DeviceStatus.SUSPICIOUS_DEVICE, confidence, signals, age_days)

        # ── Step 4: Suspicion checks ─────────────────────────────────────
        suspicious = False

        ram_signals = _detect_root_or_emulator_or_automation(context.attributes)
        if ram_signals:
            signals.extend(ram_signals)
            suspicious = True

        if device_row.fingerprint_hash and fingerprint_now != device_row.fingerprint_hash:
            signals.append(DeviceSignal.FINGERPRINT_MISMATCH)
            suspicious = True

        if device_row.trust_score < cfg.low_trust_cutoff:
            signals.append(DeviceSignal.LOW_TRUST_SCORE)
            suspicious = True

        if suspicious:
            updated = self._touch_device(device_row, context, now, fingerprint_now, penalise=True,
                                          status_label=DeviceStatus.SUSPICIOUS_DEVICE.value)
            confidence = _confidence_for_fraud_status(DeviceStatus.SUSPICIOUS_DEVICE, updated.trust_score, cfg)
            return self._finalise(DeviceStatus.SUSPICIOUS_DEVICE, confidence, signals, age_days)

        # ── Step 5: Zero-day attribute check ─────────────────────────────
        if _detect_impossible_attributes(context.attributes):
            signals.append(DeviceSignal.ZERO_DAY_DEVICE)
            signals.append(DeviceSignal.UNKNOWN_FINGERPRINT)
            if _is_unknown_platform(context.attributes):
                signals.append(DeviceSignal.UNKNOWN_PLATFORM)
            updated = self._touch_device(device_row, context, now, fingerprint_now, penalise=True,
                                          status_label=DeviceStatus.ZERO_DAY_DEVICE.value)
            confidence = _confidence_for_fraud_status(DeviceStatus.ZERO_DAY_DEVICE, updated.trust_score, cfg)
            return self._finalise(DeviceStatus.ZERO_DAY_DEVICE, confidence, signals, age_days)

        # ── Step 6: TRUSTED / KNOWN / INACTIVE classification ────────────
        recency_days = _days_between(device_row.last_seen, now)  # gap BEFORE this login
        transaction_count = self._repository.get_successful_transaction_count(device_row.device_id or "")
        login_count_after = device_row.login_count + 1

        status = _classify_ordinary_status(recency_days, login_count_after, transaction_count, age_days, cfg)
        signal_map = {
            DeviceStatus.TRUSTED_DEVICE:  DeviceSignal.TRUSTED_DEVICE,
            DeviceStatus.KNOWN_DEVICE:    DeviceSignal.KNOWN_DEVICE,
            DeviceStatus.INACTIVE_DEVICE: DeviceSignal.INACTIVE_DEVICE,
        }
        signals.append(signal_map[status])

        self._touch_device(device_row, context, now, fingerprint_now, penalise=False, status_label=status.value)

        confidence = _confidence_for_ordinary_status(status, cfg)
        return self._finalise(status, confidence, signals, age_days)

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _finalise(
        self,
        status: DeviceStatus,
        confidence: int,
        signals: list[DeviceSignal],
        age_days: int,
    ) -> DeviceTrustResult:
        cfg = self._config
        if confidence < cfg.low_confidence_cutoff:
            signals.append(DeviceSignal.LOW_CONFIDENCE)
        elif confidence >= cfg.high_confidence_cutoff:
            signals.append(DeviceSignal.HIGH_CONFIDENCE)

        seen: set[DeviceSignal] = set()
        unique_signals: list[DeviceSignal] = []
        for sig in signals:
            if sig not in seen:
                seen.add(sig)
                unique_signals.append(sig)

        logger.info(
            "device_trust evaluated: status=%s age_days=%d confidence=%d signals=%s",
            status.value, age_days, confidence, [s.value for s in unique_signals],
        )

        return DeviceTrustResult(
            device_status=status,
            device_age_days=age_days,
            device_confidence=confidence,
            security_signals=unique_signals,
        )

    def _register_new_device(
        self,
        context: DeviceContext,
        now: datetime,
        initial_trust_score: float,
        trust_status: str,
    ) -> DeviceRow:
        """Persist a brand-new DeviceRow. Used for FIRST_TIME_USER and NEW_DEVICE."""
        now_iso = now.isoformat()
        row = DeviceRow(
            user_id=context.user_id,
            device_identifier=context.device_identifier,
            device_name=context.attributes.get("device_name"),
            device_type=context.attributes.get("platform"),
            fingerprint_hash=_compute_fingerprint_hash(context.attributes),
            trust_score=initial_trust_score,
            login_count=1,
            trust_status=trust_status,
            is_active=True,
            first_seen=now_iso,
            last_seen=now_iso,
        )
        return self._repository.save_device(row)

    def _touch_device(
        self,
        device_row: DeviceRow,
        context: DeviceContext,
        now: datetime,
        fingerprint_now: str,
        penalise: bool,
        status_label: str,
    ) -> DeviceRow:
        """
        Update last_seen, login_count, trust_score, and trust_status on an
        existing DeviceRow, then persist via repository.update_device().
        Called exactly once per evaluate() call, at login time — NOT at
        session end. device_trust must reflect the CURRENT session before
        risk_engine.py makes its decision, so the update happens up front.
        """
        cfg = self._config
        device_row.last_seen = now.isoformat()
        device_row.login_count += 1
        device_row.trust_status = status_label

        if penalise:
            device_row.trust_score = max(0.0, device_row.trust_score - cfg.trust_score_penalty_step)
        else:
            device_row.trust_score = min(1.0, device_row.trust_score + cfg.trust_score_reward_step)

        # Only backfill a missing fingerprint. Never overwrite an existing
        # one on the clean path — a real change should have been caught by
        # the mismatch check upstream, not silently accepted here.
        if not device_row.fingerprint_hash:
            device_row.fingerprint_hash = fingerprint_now

        return self._repository.update_device(device_row)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — MODULE-LEVEL CONVENIENCE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_device_trust(
    repository: DeviceRepository,
    user_id: str,
    device_identifier: str,
    attributes: dict[str, Any] | None = None,
    config: DeviceTrustConfig | None = None,
) -> dict[str, Any]:
    """
    Module-level convenience wrapper — this is the function called by
    security_service.py / security_middleware.py in the production pipeline.

    Parameters
    ----------
    repository        : Injected repository implementation.
    user_id            : Authenticated user id (from session/JWT — NEVER
                         from the client request body).
    device_identifier  : Client-supplied stable device id
                         (React Native DeviceInfo.getUniqueId()).
    attributes         : Raw device metadata dict (see DeviceContext docstring).
    config             : Optional DeviceTrustConfig override.

    Returns
    -------
    {
        "device_status":     str,   # NEW | KNOWN | TRUSTED | INACTIVE
                                     # (+ SUSPICIOUS_DEVICE / ZERO_DAY_DEVICE
                                     # fraud extensions). Internal
                                     # FIRST_TIME_USER is always collapsed
                                     # to NEW_DEVICE before it gets here.
        "device_age_days":   int,
        "device_confidence": int,
        "security_signals":  list[str]
    }

    NOTE: no "risk_penalty" key. Converting device_status into a numeric
    penalty is security_rules.py's responsibility, not this module's.
    """
    service = DeviceTrustService(repository=repository, config=config)
    context = DeviceContext(
        user_id=user_id,
        device_identifier=device_identifier,
        attributes=attributes or {},
    )
    return service.evaluate(context).to_dict()
