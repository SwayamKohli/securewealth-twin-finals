from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol

from models.audit import AuditLog

logger = logging.getLogger("guardian.hash_chaining")

# ==========================================================
# GENESIS HASH
# ==========================================================

GENESIS_HASH: str = "0" * 64


# ==========================================================
# ENUMS
# ==========================================================

class ChainStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


# ==========================================================
# RESPONSE MODEL
# ==========================================================

@dataclass
class ChainVerificationResult:
    status: ChainStatus
    checked_records: int
    broken_at: Optional[str] = None


# ==========================================================
# REPOSITORY CONTRACT
# ==========================================================

class _LatestRecordRepo(Protocol):

    def get_latest_before(
        self,
        current_audit_id,
    ) -> AuditLog | None: ...


# ==========================================================
# HASH CHAIN SERVICE
# ==========================================================

class HashChainService:
    """
    Generates and verifies the SHA-256 hash chain for audit records.

    current_hash = SHA256(
        canonical_record +
        previous_hash +
        created_at
    )

    The canonical record contains only immutable business fields.
    Cryptographic fields (current_hash, digital_signature, etc.)
    are intentionally excluded.
    """

    # ------------------------------------------------------
    # Canonical Serialization
    # ------------------------------------------------------

    @staticmethod
    def _canonical(
        record: dict[str, Any],
    ) -> str:
        """
        Deterministically serialize immutable audit fields.

        IMPORTANT:
        Do NOT include:
            previous_hash
            current_hash
            digital_signature
            signature_algorithm
            record_status

        because those are either generated later or may legitimately
        change during recovery.
        """

        canonical_record = {
            "audit_id": str(record["audit_id"]),
            "transaction_id": (
                str(record["transaction_id"])
                if record["transaction_id"] is not None
                else None
            ),
            "user_id": (
                str(record["user_id"])
                if record["user_id"] is not None
                else None
            ),
            "device_id": (
                str(record["device_id"])
                if record["device_id"] is not None
                else None
            ),
            "account_id": (
                str(record["account_id"])
                if record["account_id"] is not None
                else None
            ),
            "event_type": record["event_type"],
            "final_decision": record["final_decision"],
            "risk_score": record["risk_score"],
            "amount": (
                str(record["amount"])
                if record["amount"] is not None
                else None
            ),
            "channel": record["channel"],
            "ai_status": record["ai_status"],
            "ai_confidence": (
                str(record["ai_confidence"])
                if record["ai_confidence"] is not None
                else None
            ),
            "unknown_risk_severity": record["unknown_risk_severity"],
            "unknown_risk_applied": record["unknown_risk_applied"],
            "unknown_risk_decision": record["unknown_risk_decision"],
            "unknown_risk_reason_code": record["unknown_risk_reason_code"],
            "challenge_required": record["challenge_required"],
            "challenge_type": record["challenge_type"],
            "challenge_trigger_signal": record["challenge_trigger_signal"],
            "security_signals": record["security_signals"],
            "audit_note": record["audit_note"],
            "compliance_reference": record["compliance_reference"],
        }

        return json.dumps(
            canonical_record,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    # ------------------------------------------------------
    # Core Hashing
    # ------------------------------------------------------

    @staticmethod
    def generate_hash(
        payload: str,
    ) -> str:
        """
        Returns the SHA-256 hash of the supplied payload.
        """
        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    def generate_current_hash(
        self,
        record: dict[str, Any],
        previous_hash: str,
        timestamp: str,
    ) -> str:
        """
        Generates the current hash for an audit record.

        current_hash =
            SHA256(
                canonical_record +
                previous_hash +
                created_at
            )
        """

        payload = (
            f"{self._canonical(record)}"
            f"{previous_hash}"
            f"{timestamp}"
        )

        digest = self.generate_hash(payload)

        logger.debug(
            "Generated hash=%s previous=%s",
            digest,
            previous_hash,
        )

        return digest

    # ------------------------------------------------------
    # Previous Hash
    # ------------------------------------------------------

    def get_previous_hash(
        self,
        repo: _LatestRecordRepo,
        current_audit_id,
    ) -> str:
        """
        Returns the latest current_hash in the chain.

        If no records exist,
        returns the Genesis Hash.
        """

        latest = repo.get_latest_before(
        current_audit_id,
    )

        if latest is None:
            logger.info(
                "No previous audit record found. Using Genesis Hash."
            )
            return GENESIS_HASH

        return latest.current_hash

    # ------------------------------------------------------
    # Verification
    # ------------------------------------------------------

    def verify_record(
        self,
        record: dict[str, Any],
    ) -> bool:
        """
        Recompute the hash for a single audit record and compare it with
        the stored current_hash.

        Returns
        -------
        True  -> Record hash is valid.
        False -> Record has been modified.
        """

        recomputed_hash = self.generate_current_hash(
            record=record,
            previous_hash=record["previous_hash"],
            timestamp=str(record["created_at"]),
        )

        is_valid = (
            recomputed_hash == record["current_hash"]
        )

        if not is_valid:
            logger.warning(
                "Hash verification failed for audit_id=%s",
                record.get("audit_id"),
            )

        return is_valid

    def verify_chain(
        self,
        chain: list[dict[str, Any]],
    ) -> ChainVerificationResult:
        """
        Verify the integrity of the complete audit chain.

        Validation Steps
        ----------------
        1. Verify previous_hash linkage.
        2. Verify each record's current_hash.
        3. Ensure uninterrupted chain from Genesis Hash.

        Returns
        -------
        ChainVerificationResult
        """

        expected_previous_hash = GENESIS_HASH

        checked_records = 0

        for record in chain:

            checked_records += 1

            # ----------------------------------------------
            # Check previous hash linkage
            # ----------------------------------------------

            if record["previous_hash"] != expected_previous_hash:

                logger.error(
                    "Chain broken at audit_id=%s",
                    record.get("audit_id"),
                )

                return ChainVerificationResult(
                    status=ChainStatus.INVALID,
                    checked_records=checked_records,
                    broken_at=record.get("audit_id"),
                )

            # ----------------------------------------------
            # Verify current hash
            # ----------------------------------------------

            if not self.verify_record(record):

                logger.error(
                    "Hash mismatch detected at audit_id=%s",
                    record.get("audit_id"),
                )

                return ChainVerificationResult(
                    status=ChainStatus.INVALID,
                    checked_records=checked_records,
                    broken_at=record.get("audit_id"),
                )

            expected_previous_hash = record["current_hash"]

        logger.info(
            "Audit hash chain verification successful. Records verified=%d",
            checked_records,
        )

        return ChainVerificationResult(
            status=ChainStatus.VALID,
            checked_records=checked_records,
        )