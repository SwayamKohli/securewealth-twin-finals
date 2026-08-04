from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from audit.hash_chain import (
    ChainStatus,
    HashChainService,
)
from audit.signature_service import (
    SignatureService,
    SignatureStatus,
)
from audit.replica_verifier import ReplicaVerifier
from audit.recovery_service import RecoveryService

from models.audit import AuditLog

from schemas.audit_schema import IntegrityReport

from services.audit_service import AuditService


class TamperMonitor:

    def __init__(
        self,
        hash_service: HashChainService,
        signature_service: SignatureService,
        replica_verifier: ReplicaVerifier,
        recovery_service: RecoveryService,
        audit_service: AuditService,
        public_key,
    ):
        self._hash = hash_service
        self._signature = signature_service
        self._verifier = replica_verifier
        self._recovery = recovery_service
        self._audit = audit_service
        self._public_key = public_key

    def run(
        self,
    ) -> IntegrityReport:

        chain = self._audit.get_audit_chain()

        chain_dict = [
            self._to_dict(record)
            for record in chain
        ]

        chain_result = self._hash.verify_chain(
            chain_dict,
        )

        signatures_valid = 0
        signatures_invalid = 0

        replicas_valid = 0
        replicas_invalid = 0

        recoveries_attempted = 0
        recoveries_succeeded = 0

        findings = []

        started_at = datetime.now(
            timezone.utc,
        )

        for record in chain:

            record_dict = self._to_dict(
                record,
            )

            signature_status = self._signature.verify_signature(
                audit_record=record_dict,
                signature_b64=record.digital_signature,
                public_key=self._public_key,
            )

            if signature_status == SignatureStatus.VALID:

                signatures_valid += 1

            else:

                signatures_invalid += 1

                findings.append(
                    {
                        "audit_id": str(record.audit_id),
                        "type": "INVALID_SIGNATURE",
                    }
                )

            verification = self._verifier.verify(
                record.audit_id,
            )

            if verification.recovery_required:

                replicas_invalid += 1

                recoveries_attempted += 1

                # Record the ATTACK itself before repairing it, so the
                # dashboard shows both "what was attempted" and "how the
                # system responded".
                self._audit.log_tamper_event(
                    audit_id=record.audit_id,
                    corrupted_copies=verification.corrupted_copies,
                    detail=verification.comparison,
                )

                recovery = self._recovery.recover(
                    verification,
                )

                if recovery.recovered:

                    recoveries_succeeded += 1

                    self._audit.log_recovery_event(
                        audit_id=record.audit_id,
                        recovery_note=recovery.message,
                        recovered_from=recovery.source_copy,
                    )

                # Repairs and their audit entries are only flushed to the
                # session by the repositories — persist them, otherwise every
                # sweep re-detects the same tamper and no evidence survives.
                self._commit()

                findings.append(
                    {
                        "audit_id": str(record.audit_id),
                        "type": "REPLICA_CORRUPTION",
                        "repaired": recovery.recovered,
                    }
                )

            else:

                replicas_valid += 1

        completed_at = datetime.now(
            timezone.utc,
        )

        overall_status = (
            "HEALTHY"
            if (
                chain_result.status == ChainStatus.VALID
                and signatures_invalid == 0
                and recoveries_attempted == recoveries_succeeded
            )
            else "COMPROMISED"
        )

        return IntegrityReport(
            started_at=started_at,
            completed_at=completed_at,

            overall_status=overall_status,

            hash_chain_valid=(
                chain_result.status == ChainStatus.VALID
            ),

            checked_records=chain_result.checked_records,

            signatures_valid=signatures_valid,
            signatures_invalid=signatures_invalid,

            replicas_valid=replicas_valid,
            replicas_invalid=replicas_invalid,

            recoveries_attempted=recoveries_attempted,
            recoveries_succeeded=recoveries_succeeded,

            findings=findings,
        )

    def _commit(self) -> None:
        """Persist repairs + audit entries written during this sweep."""
        session = getattr(self._verifier, "_repo", None)
        session = getattr(session, "db", None)
        if session is not None:
            try:
                session.commit()
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _to_dict(
        audit: AuditLog,
    ) -> dict[str, Any]:

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

            "previous_hash": audit.previous_hash,
            "current_hash": audit.current_hash,

            "created_at": audit.created_at,
        }