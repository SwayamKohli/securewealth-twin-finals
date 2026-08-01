from __future__ import annotations

from pyexpat import model
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.audit import AuditLog
from models.audit_replica import (
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
)

REPLICA_MODELS = [
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
]

class AuditRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ==========================================================
    # MASTER AUDIT OPERATIONS
    # ==========================================================
    def create(
        self,
        audit: AuditLog,
    ) -> AuditLog:
        self.db.add(audit)
        self.db.flush()
        self.db.refresh(audit)

        return audit

    def get_by_id(
        self,
        audit_id: UUID,
    ) -> AuditLog | None:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.audit_id == audit_id)
            .first()
        )

    def get_latest(
        self,
    ) -> AuditLog | None:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.chain_index.desc())
            .first()
        )

    def get_latest_before(
        self,
        current_audit_id,
    ) -> AuditLog | None:

        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.audit_id != current_audit_id,
            )
            .order_by(
                AuditLog.chain_index.desc(),
                AuditLog.updated_at.desc(),
            )
            .first()
        )

    def get_chain(
        self,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.asc())
            .all()
        )

    def get_all(
        self,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def update(
        self,
        audit: AuditLog,
    ) -> AuditLog:
        self.db.flush()
        self.db.refresh(audit)

        return audit

    def delete(
        self,
        audit: AuditLog,
    ) -> None:
        self.db.delete(audit)
        self.db.flush()

    def exists(
        self,
        audit_id: UUID,
    ) -> bool:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.audit_id == audit_id)
            .first()
            is not None
        )

    def get_by_user(
        self,
        user_id: UUID,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_transaction(
        self,
        transaction_id: UUID,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.transaction_id == transaction_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_event_type(
        self,
        event_type: str,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_decision(
        self,
        decision: str,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.final_decision == decision)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def get_by_record_status(
        self,
        status: str,
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.record_status == status)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    # ==========================================================
    # REPLICA OPERATIONS
    # ==========================================================
    def create_replica(
        self,
        replica,
    ):
        self.db.add(replica)
        self.db.flush()
        self.db.refresh(replica)

        return replica

    def get_replica(
        self,
        model,
        audit_id: UUID,
    ):
        return (
            self.db.query(model)
            .filter(model.audit_id == audit_id)
            .first()
        )

    def get_all_replicas(
        self,
        audit_id: UUID,
    ):
        return {
            model.__tablename__: self.get_replica(model, audit_id)
            for model in REPLICA_MODELS
        }

    def update_replica(
        self,
        replica,
    ):
        self.db.flush()
        self.db.refresh(replica)

        return replica

    def delete_replica(
        self,
        replica,
    ):
        self.db.delete(replica)
        self.db.flush()

    def get_replica_chain(
        self,
        model,
    ):
        return (
            self.db.query(model)
            .order_by(model.created_at.asc())
            .all()
        )

    def replica_exists(
        self,
        model,
        audit_id: UUID,
    ):
        return (
            self.db.query(model)
            .filter(model.audit_id == audit_id)
            .first()
            is not None
        )

    # ==========================================================
    # RECOVERY
    # ==========================================================
    def replace_replica(
        self,
        model,
        audit_id: UUID,
        replacement,
    ):
        """
        Replaces the contents of a replica record with a healthy copy.

        Used by RecoveryService after majority consensus determines
        the correct version of the audit record.

        Only the audit data is replaced.
        Replica-specific metadata is preserved.
        """

        replica = self.get_replica(
            model=model,
            audit_id=audit_id,
        )

        if replica is None:
            raise ValueError(
                f"Replica for audit record {audit_id} not found."
            )

        excluded_fields = {
            "_sa_instance_state",
            "replica_record_id",
            "replica_name",
            "created_at",
            "updated_at",
        }

        for field, value in vars(replacement).items():

            if field in excluded_fields:
                continue

            setattr(
                replica,
                field,
                value,
            )

        self.db.flush()
        self.db.refresh(replica)

        return replica

    def replace_master_record(
        self,
        audit_id: UUID,
        replacement: AuditLog,
    ) -> AuditLog:
        audit = self.get_by_id(audit_id)

        print(">>> replace_master_record called")

        if audit is None:
            raise ValueError(f"Audit record {audit_id} not found.")

        audit.transaction_id = replacement.transaction_id
        audit.user_id = replacement.user_id
        audit.device_id = replacement.device_id
        audit.account_id = replacement.account_id

        audit.event_type = replacement.event_type
        audit.final_decision = replacement.final_decision
        audit.risk_score = replacement.risk_score

        audit.amount = replacement.amount
        audit.channel = replacement.channel

        audit.ai_status = replacement.ai_status
        audit.ai_confidence = replacement.ai_confidence
        audit.unknown_risk_severity = replacement.unknown_risk_severity
        audit.unknown_risk_applied = replacement.unknown_risk_applied
        audit.unknown_risk_decision = replacement.unknown_risk_decision
        audit.unknown_risk_reason_code = replacement.unknown_risk_reason_code

        audit.challenge_required = replacement.challenge_required
        audit.challenge_type = replacement.challenge_type
        audit.challenge_trigger_signal = replacement.challenge_trigger_signal

        audit.security_signals = replacement.security_signals

        audit.audit_note = replacement.audit_note
        audit.compliance_reference = replacement.compliance_reference

        audit.previous_hash = replacement.previous_hash
        audit.current_hash = replacement.current_hash

        audit.digital_signature = replacement.digital_signature
        audit.signature_algorithm = replacement.signature_algorithm

        audit.record_status = replacement.record_status

        self.db.flush()
        self.db.refresh(audit)

        return audit

    def get_by_event_type(
        self,
        event_type: str,
    ) -> list[AuditLog]:
        """
        Returns all audit records of a given event type,
        ordered from newest to oldest.
        """

        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.event_type == event_type
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .all()
        )


    def get_summary(
        self,
    ) -> dict:
        """
        Returns aggregate statistics for the audit subsystem.
        """

        total_records = (
            self.db.query(func.count(AuditLog.audit_id))
            .scalar()
        )

        valid_records = (
            self.db.query(func.count(AuditLog.audit_id))
            .filter(
                AuditLog.record_status == "VALID"
            )
            .scalar()
        )

        recovered_records = (
            self.db.query(func.count(AuditLog.audit_id))
            .filter(
                AuditLog.event_type == "RECOVERY_EVENT"
            )
            .scalar()
        )

        corrupted_records = (
            self.db.query(func.count(AuditLog.audit_id))
            .filter(
                AuditLog.record_status == "CORRUPTED"
            )
            .scalar()
        )

        latest_record_time = (
            self.db.query(func.max(AuditLog.created_at))
            .scalar()
        )

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "recovered_records": recovered_records,
            "corrupted_records": corrupted_records,
            "latest_record_time": latest_record_time,
        }

    # ==========================================================
    # STATISTICS
    # ==========================================================
    def count_replicas(
        self,
        model,
    ):
        return self.db.query(model).count()

    def count_by_user(
        self,
        user_id: UUID,
    ) -> int:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .count()
        )

    def count_by_status(
        self,
        status: str,
    ) -> int:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.record_status == status)
            .count()
        )

    def count_by_event_type(
        self,
        event_type: str,
    ) -> int:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .count()
        )

    # ==========================================================
    # PRIVATE HELPERS
    # ==========================================================
    def _flush_refresh(
        self,
        audit: AuditLog,
    ) -> AuditLog:
        self.db.flush()
        self.db.refresh(audit)

        return audit


# This API is flexible enough to support all the future components you mentioned:

# ✅ AuditService → create_replica()
# ✅ ReplicaVerifier → get_replica(), get_all_replicas(), get_replica_chain()
# ✅ TamperMonitor → get_all_replicas(), replica_exists()
# ✅ RecoveryService → replace_replica(), update_replica()
# ✅ AuditScheduler → reuses the same repository methods without needing any repository changes.