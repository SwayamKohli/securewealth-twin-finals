from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.audit import AuditLog
from models.audit_replica import AuditReplica


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
            .order_by(AuditLog.created_at.desc())
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
        replica: AuditReplica,
    ) -> AuditReplica:
        self.db.add(replica)
        self.db.flush()
        self.db.refresh(replica)

        return replica

    def get_replica(
        self,
        audit_id: UUID,
        replica_name: str,
    ) -> AuditReplica | None:
        return (
            self.db.query(AuditReplica)
            .filter(
                AuditReplica.audit_id == audit_id,
                AuditReplica.replica_name == replica_name,
            )
            .first()
        )

    def get_all_replicas(
        self,
        audit_id: UUID,
    ) -> list[AuditReplica]:
        return (
            self.db.query(AuditReplica)
            .filter(AuditReplica.audit_id == audit_id)
            .order_by(AuditReplica.replica_name.asc())
            .all()
        )

    def update_replica(
        self,
        replica: AuditReplica,
    ) -> AuditReplica:
        self.db.flush()
        self.db.refresh(replica)

        return replica

    def delete_replica(
        self,
        replica: AuditReplica,
    ) -> None:
        self.db.delete(replica)
        self.db.flush()

    # ==========================================================
    # RECOVERY
    # ==========================================================

    def replace_master_record(
        self,
        audit_id: UUID,
        replacement: AuditLog,
    ) -> AuditLog:
        audit = self.get_by_id(audit_id)

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

    # ==========================================================
    # STATISTICS
    # ==========================================================

    def count(
        self,
    ) -> int:
        return (
            self.db.query(AuditLog)
            .count()
        )

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