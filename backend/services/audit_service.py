from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol
from uuid import UUID
from models.base import Base

from audit.hash_chain import HashChainService
from audit.signature_service import SignatureService
from models.audit import AuditLog
from models.audit_replica import (
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
)

logger = logging.getLogger("guardian.audit_service")


# ==========================================================
# AUDIT EVENT TYPES
# ==========================================================

class AuditEventType(str, Enum):
    TRANSACTION_SECURITY = "TRANSACTION_SECURITY"
    UNKNOWN_RISK = "UNKNOWN_RISK"
    CHALLENGE = "CHALLENGE"
    TAMPER_EVENT = "TAMPER_EVENT"
    RECOVERY_EVENT = "RECOVERY_EVENT"


# ==========================================================
# INPUT MODEL
# ==========================================================

@dataclass
class AuditLogData:
    transaction_id: UUID | None
    user_id: UUID | None
    device_id: UUID | None
    account_id: UUID | None

    event_type: str

    final_decision: str
    risk_score: int

    amount: Decimal | None
    channel: str | None

    ai_status: str | None
    ai_confidence: Decimal | None
    unknown_risk_severity: str | None
    unknown_risk_applied: bool
    unknown_risk_decision: str | None
    unknown_risk_reason_code: str | None

    challenge_required: bool
    challenge_type: str | None
    challenge_trigger_signal: str | None

    security_signals: dict[str, Any] | None

    audit_note: str | None
    compliance_reference: str | None


# ==========================================================
# REPOSITORY CONTRACT
# ==========================================================

class AuditRepository(Protocol):

    def create(
        self,
        audit: AuditLog,
    ) -> AuditLog:
        ...

    def create_replica(
        self,
        replica: Base,
    ) -> Base:
        ...

    def get_latest(
        self,
    ) -> AuditLog | None:
        ...

    def get_by_id(
        self,
        audit_id: UUID,
    ) -> AuditLog | None:
        ...

    def get_chain(
        self,
    ) -> list[AuditLog]:
        ...


# ==========================================================
# AUDIT SERVICE
# ==========================================================

class AuditService:

    def __init__(
        self,
        audit_repo: AuditRepository,
        hash_service: HashChainService,
        signature_service: SignatureService,
    ) -> None:

        self._repo = audit_repo
        self._hash = hash_service
        self._signature = signature_service

    # ======================================================
    # PRIVATE HELPERS
    # ======================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _resolve_event_type(
        event_type: AuditEventType | str,
    ) -> str:

        if isinstance(event_type, AuditEventType):
            return event_type.value

        return str(event_type)

    @staticmethod
    def _record_to_dict(
        audit: AuditLog,
    ) -> dict[str, Any]:
        """
        Converts an AuditLog ORM object into the canonical dictionary
        expected by HashChainService and SignatureService.
        """

        return {
            "audit_id": audit.audit_id,
            "transaction_id": audit.transaction_id,
            "user_id": audit.user_id,
            "device_id": audit.device_id,
            "account_id": audit.account_id,

            "event_type": audit.event_type,

            "final_decision": audit.final_decision,
            "risk_score": audit.risk_score,

            "amount": audit.amount,
            "channel": audit.channel,

            "ai_status": audit.ai_status,
            "ai_confidence": audit.ai_confidence,
            "unknown_risk_severity": audit.unknown_risk_severity,
            "unknown_risk_applied": audit.unknown_risk_applied,
            "unknown_risk_decision": audit.unknown_risk_decision,
            "unknown_risk_reason_code": audit.unknown_risk_reason_code,

            "challenge_required": audit.challenge_required,
            "challenge_type": audit.challenge_type,
            "challenge_trigger_signal": audit.challenge_trigger_signal,

            "security_signals": audit.security_signals,

            "audit_note": audit.audit_note,
            "compliance_reference": audit.compliance_reference,
        }

    def _build_audit_model(
        self,
        data: AuditLogData,
    ) -> AuditLog:
        """
        Creates an AuditLog ORM object before hashing and signing.
        Hashes and signatures are populated later in the pipeline.
        """

        return AuditLog(
            transaction_id=data.transaction_id,
            user_id=data.user_id,
            device_id=data.device_id,
            account_id=data.account_id,

            event_type=self._resolve_event_type(data.event_type),

            final_decision=data.final_decision,
            risk_score=data.risk_score,

            amount=data.amount,
            channel=data.channel,

            ai_status=data.ai_status,
            ai_confidence=data.ai_confidence,
            unknown_risk_severity=data.unknown_risk_severity,
            unknown_risk_applied=data.unknown_risk_applied,
            unknown_risk_decision=data.unknown_risk_decision,
            unknown_risk_reason_code=data.unknown_risk_reason_code,

            challenge_required=data.challenge_required,
            challenge_type=data.challenge_type,
            challenge_trigger_signal=data.challenge_trigger_signal,

            security_signals=data.security_signals,

            audit_note=data.audit_note,
            compliance_reference=data.compliance_reference,

            previous_hash="",
            current_hash="",
            digital_signature=b"",
            signature_algorithm="Ed25519",
            record_status="VALID",
        )
    
    def _generate_hash(
        self,
        audit: AuditLog,
    ) -> None:
        """
        Generate the hash chain values for an audit record.
        """

        previous_hash = self._hash.get_previous_hash(
            repo=self._repo,
            current_audit_id=audit.audit_id,
        )

        audit.previous_hash = previous_hash

        audit.current_hash = self._hash.generate_current_hash(
            record=self._record_to_dict(audit),
            previous_hash=previous_hash,
            timestamp=str(audit.created_at),
        )

    def _generate_signature(
        self,
        audit: AuditLog,
    ) -> None:
        """
        Generate the Ed25519 digital signature for the audit record.
        """

        signature = self._signature.sign_audit_record(
            self._record_to_dict(audit),
        )

        audit.digital_signature = signature

    def _build_replica(
        self,
        replica_model,
        audit: AuditLog,
    ):
        """
        Builds a replica object from an AuditLog.

        This method only constructs the ORM object.
        No database operations are performed.
        """
        replica_name = {
            AuditReplica1: "REPLICA_1",
            AuditReplica2: "REPLICA_2",
            AuditReplica3: "REPLICA_3",
        }[replica_model]
        return replica_model(
            audit_id=audit.audit_id,
            replica_name=replica_name,
            transaction_id=audit.transaction_id,
            user_id=audit.user_id,
            device_id=audit.device_id,
            account_id=audit.account_id,

            event_type=audit.event_type,

            final_decision=audit.final_decision,
            risk_score=audit.risk_score,

            amount=audit.amount,
            channel=audit.channel,

            ai_status=audit.ai_status,
            ai_confidence=audit.ai_confidence,
            unknown_risk_severity=audit.unknown_risk_severity,
            unknown_risk_applied=audit.unknown_risk_applied,
            unknown_risk_decision=audit.unknown_risk_decision,
            unknown_risk_reason_code=audit.unknown_risk_reason_code,

            challenge_required=audit.challenge_required,
            challenge_type=audit.challenge_type,
            challenge_trigger_signal=audit.challenge_trigger_signal,

            security_signals=audit.security_signals,

            audit_note=audit.audit_note,
            compliance_reference=audit.compliance_reference,

            previous_hash=audit.previous_hash,
            current_hash=audit.current_hash,

            digital_signature=audit.digital_signature,
            signature_algorithm=audit.signature_algorithm,

            record_status=audit.record_status,
        )

    def _replicate_record(
        self,
        audit: AuditLog,
    ) -> None:
        """
        Creates identical replicas of an audit record
        across all replica tables.
        """

        replica_models = [
            AuditReplica1,
            AuditReplica2,
            AuditReplica3,
        ]

        for model in replica_models:

            replica = self._build_replica(
                model,
                audit,
            )

            self._repo.create_replica(
                replica,
            )
    # ======================================================
    # PUBLIC API
    # ======================================================

    def log_security_decision(
        self,
        data: AuditLogData,
    ) -> AuditLog:
        """
        Creates a complete audit record.

        Pipeline

            Build ORM Model
                    ↓
            Generate Previous Hash
                    ↓
            Generate Current Hash
                    ↓
            Generate Digital Signature
                    ↓
            Persist Master Record
                    ↓
            Replicate Record
                    ↓
            Return Persisted Record
        """

        audit = self._build_audit_model(data)

        persisted = self._repo.create(audit)

        self._generate_hash(persisted)

        self._generate_signature(persisted)

        persisted = self._repo.update(persisted)

        self._replicate_record(persisted)

        logger.info(
            "Audit record %s created successfully.",
            persisted.audit_id,
        )

        return persisted
    
    def log_recovery_event(
        self,
        audit_id: UUID,
        recovery_note: str,
        recovered_from: str,
    ) -> AuditLog:
        """
        Creates a recovery audit entry after a corrupted audit
        record has been restored.

        Recovery events themselves are immutable and become part
        of the audit chain.
        """

        recovery_data = AuditLogData(
            transaction_id=None,
            user_id=None,
            device_id=None,
            account_id=None,

            event_type=AuditEventType.RECOVERY_EVENT,

            final_decision="RECOVERED",
            risk_score=0,

            amount=None,
            channel=None,

            ai_status=None,
            ai_confidence=None,
            unknown_risk_severity=None,
            unknown_risk_applied=False,
            unknown_risk_decision=None,
            unknown_risk_reason_code=None,

            challenge_required=False,
            challenge_type=None,
            challenge_trigger_signal=None,

            security_signals={
                "recovered_audit_id": str(audit_id),
                "recovered_from": recovered_from,
            },

            audit_note=recovery_note,
            compliance_reference=None,
        )

        return self.log_security_decision(
            recovery_data,
        )

    # ======================================================
    # QUERY OPERATIONS
    # ======================================================

    def get_audit_record(
        self,
        audit_id: UUID,
    ) -> AuditLog | None:
        """
        Returns a single audit record.
        """

        return self._repo.get_by_id(
            audit_id,
        )

    def get_audit_chain(
        self,
    ) -> list[AuditLog]:
        """
        Returns the complete audit chain ordered
        from oldest to newest.
        """

        return self._repo.get_chain()

    ###############################################################
    #   RECOVERY OPERATIONS
    ###############################################################

    def get_recovery_history(
        self,
    ) -> list[AuditLog]:
        """
        Returns all recovery audit events.
        """

        return self._repo.get_by_event_type(
            AuditEventType.RECOVERY_EVENT.value,
        )

    def get_audit_summary(
        self,
    ):
        """
        Returns summary statistics for the audit subsystem.
        """

        return self._repo.get_summary()