from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ============================================================
# Base Audit Model
# ============================================================

class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: UUID

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

    security_signals: dict | None

    audit_note: str | None
    compliance_reference: str | None

    previous_hash: str
    current_hash: str

    digital_signature: bytes
    signature_algorithm: str

    record_status: str

    created_at: datetime
    updated_at: datetime


# ============================================================
# Audit Summary
# ============================================================

class AuditSummaryResponse(BaseModel):
    total_records: int
    valid_records: int
    recovered_records: int
    corrupted_records: int
    latest_record_time: datetime | None


# ============================================================
# Integrity Status
# ============================================================

class IntegrityStatusResponse(BaseModel):
    hash_chain_valid: bool
    signatures_valid: bool
    replicas_consistent: bool
    overall_status: str
    last_verified_at: datetime


# ============================================================
# Replica Status
# ============================================================

class ReplicaStatusResponse(BaseModel):
    replica_name: str
    audit_id: UUID
    verification_status: str
    verified_at: datetime | None


# ============================================================
# Recovery Response
# ============================================================

class RecoveryResponse(BaseModel):
    audit_id: UUID
    recovered: bool
    recovery_event_id: UUID | None
    message: str

class ReplicaVerificationResult(BaseModel):
    audit_id: UUID

    comparison: dict[str, dict]

    healthy_copies: int

    corrupted_copies: list[str]

    replicas_behind: list[str]

    recovery_required: bool

    recovery_possible: bool
class RecoveryResult(BaseModel):
    audit_id: UUID

    recovered: bool

    repaired_copies: list[str]

    source_copy: str | None

    message: str

class IntegrityReport(BaseModel):
    started_at: datetime
    completed_at: datetime

    overall_status: str

    hash_chain_valid: bool
    checked_records: int

    signatures_valid: int
    signatures_invalid: int

    replicas_valid: int
    replicas_invalid: int

    recoveries_attempted: int
    recoveries_succeeded: int

    findings: list[dict]

# ============================================================
# Tamper Finding
# ============================================================

class TamperFindingResponse(BaseModel):
    audit_id: UUID
    severity: str
    corruption_type: str
    affected_fields: list[str]
    detail: str
    recovered: bool


# ============================================================
# Monitoring Report
# ============================================================

class MonitoringReportResponse(BaseModel):
    cycle_id: str

    started_at: datetime
    completed_at: datetime

    status: str
    severity: str

    total_records_scanned: int

    hash_chain_valid: bool

    signatures_valid: int
    signatures_invalid: int

    replicas_valid: int
    replicas_invalid: int

    recoveries_attempted: int
    recoveries_succeeded: int

    findings: list[TamperFindingResponse]

    summary: str