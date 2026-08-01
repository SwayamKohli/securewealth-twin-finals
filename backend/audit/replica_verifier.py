from __future__ import annotations

from typing import Any
from uuid import UUID

from models.audit import AuditLog
from models.audit_replica import (
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
)
from database.repositories.audit_repository import AuditRepository
from schemas.audit_schema import ReplicaVerificationResult


class ReplicaVerifier:

    def __init__(
        self,
        repository: AuditRepository,
    ):
        self._repo = repository

    def verify(
        self,
        audit_id: UUID,
    ) -> ReplicaVerificationResult:

        master = self._repo.get_by_id(audit_id)

        if master is None:
            raise ValueError(f"Audit record {audit_id} does not exist.")

        replicas = self._repo.get_all_replicas(audit_id)

        comparison = {}

        comparison["master"] = {
            "status": "HEALTHY",
            "mismatched_fields": [],
        }

        healthy = 1
        corrupted = []
        behind = []

        master_dict = self._to_dict(master)

        for replica_name, replica in replicas.items():

            # Replica hasn't received the record yet.
            if replica is None:

                comparison[replica_name] = {
                    "status": "REPLICA_BEHIND",
                    "mismatched_fields": [],
                }

                behind.append(replica_name)
                continue

            mismatches = self._compare(
                master_dict,
                self._to_dict(replica),
            )

            if mismatches:

                comparison[replica_name] = {
                    "status": "CORRUPTED",
                    "mismatched_fields": mismatches,
                }

                corrupted.append(replica_name)

            else:

                comparison[replica_name] = {
                    "status": "HEALTHY",
                    "mismatched_fields": [],
                }

                healthy += 1

        return ReplicaVerificationResult(
            audit_id=audit_id,

            comparison=comparison,

            healthy_copies=healthy,

            corrupted_copies=corrupted,

            replicas_behind=behind,

            recovery_required=len(corrupted) > 0,

            recovery_possible=healthy >= 2,
        )

    @staticmethod
    def _compare(
        source: dict[str, Any],
        target: dict[str, Any],
    ) -> list[str]:

        mismatches = []

        for key, value in source.items():

            if target.get(key) != value:
                mismatches.append(key)

        return mismatches

    @staticmethod
    def _to_dict(
        record: AuditLog
        | AuditReplica1
        | AuditReplica2
        | AuditReplica3,
    ) -> dict[str, Any]:

        # excluded = {
        #     "_sa_instance_state",
        #     "replica_record_id",
        #     "replica_name",
        #     "created_at",
        #     "updated_at",
        #     "chain_index",
        # }
        
        FIELDS_TO_COMPARE = {
            "audit_id",
            "transaction_id",
            "user_id",
            "device_id",
            "account_id",
            "event_type",
            "final_decision",
            "risk_score",
            "amount",
            "channel",
            "ai_status",
            "ai_confidence",
            "unknown_risk_severity",
            "unknown_risk_applied",
            "unknown_risk_decision",
            "unknown_risk_reason_code",
            "challenge_required",
            "challenge_type",
            "challenge_trigger_signal",
            "security_signals",
            "audit_note",
            "compliance_reference",
            "previous_hash",
            "current_hash",
            "digital_signature",
            "signature_algorithm",
            "record_status",
        }
        return {
            key: value
            for key, value in vars(record).items()
            if key in FIELDS_TO_COMPARE
        }