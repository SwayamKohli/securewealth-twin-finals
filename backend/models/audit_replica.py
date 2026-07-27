from uuid import uuid4

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import TimestampMixin
from .base import Base, generate_uuid


class AuditReplica(Base, TimestampMixin):
    __tablename__ = "audit_replicas"

    replica_record_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )

    audit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_logs.audit_id", ondelete="CASCADE"),
        nullable=False,
    )

    replica_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    device_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    account_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    final_decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    channel: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    ai_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    ai_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    unknown_risk_severity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    unknown_risk_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    unknown_risk_decision: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    unknown_risk_reason_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    challenge_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    challenge_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    challenge_trigger_signal: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    security_signals: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    audit_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    compliance_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    previous_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    current_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    digital_signature: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    signature_algorithm: Mapped[str] = mapped_column(
        String(20),
        default="Ed25519",
        nullable=False,
    )

    record_status: Mapped[str] = mapped_column(
        String(20),
        default="VALID",
        nullable=False,
    )
