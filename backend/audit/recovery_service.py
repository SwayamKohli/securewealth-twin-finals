from __future__ import annotations

from typing import Any

from models.audit import AuditLog
from models.audit_replica import (
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
)
from database.repositories.audit_repository import AuditRepository
from schemas.audit_schema import (
    ReplicaVerificationResult,
    RecoveryResult,
)


REPLICA_MODELS = {
    "audit_replica_1": AuditReplica1,
    "audit_replica_2": AuditReplica2,
    "audit_replica_3": AuditReplica3,
}


class RecoveryService:

    def __init__(
        self,
        repository: AuditRepository,
    ):
        self._repo = repository

    def recover(
        self,
        verification: ReplicaVerificationResult,
    ) -> RecoveryResult:

        if not verification.recovery_required:
            return RecoveryResult(
                audit_id=verification.audit_id,
                recovered=True,
                repaired_copies=[],
                source_copy=None,
                message="Recovery not required.",
            )

        if not verification.recovery_possible:
            return RecoveryResult(
                audit_id=verification.audit_id,
                recovered=False,
                repaired_copies=[],
                source_copy=None,
                message="Majority consensus unavailable.",
            )

        source_name = self._select_source(verification)

        source_record = self._fetch_copy(
            verification.audit_id,
            source_name,
        )

        repaired = []

        if "master" in verification.corrupted_copies:
            print(">>> Repairing MASTER", verification.audit_id)
            self._repo.replace_master_record(
                verification.audit_id,
                source_record,
            )

            repaired.append("master")

        for replica_name in verification.corrupted_copies:

            if replica_name == "master":
                continue

            model = REPLICA_MODELS[replica_name]

            self._repo.replace_replica(
                model=model,
                audit_id=verification.audit_id,
                replacement=source_record,
            )

            repaired.append(replica_name)

        return RecoveryResult(
            audit_id=verification.audit_id,
            recovered=True,
            repaired_copies=repaired,
            source_copy=source_name,
            message="Recovery completed successfully.",
        )

    def _select_source(
        self,
        verification: ReplicaVerificationResult,
    ) -> str:

        if verification.comparison["master"]["status"] == "HEALTHY":
            return "master"

        for replica_name in (
            "audit_replica_1",
            "audit_replica_2",
            "audit_replica_3",
        ):

            if (
                verification.comparison[replica_name]["status"]
                == "HEALTHY"
            ):
                return replica_name

        raise ValueError("No healthy copy available.")

    def _fetch_copy(
        self,
        audit_id,
        source_name,
    ):

        if source_name == "master":
            return self._repo.get_by_id(audit_id)

        model = REPLICA_MODELS[source_name]

        return self._repo.get_replica(
            model,
            audit_id,
        )