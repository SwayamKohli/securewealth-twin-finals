from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import get_audit_service
from schemas.audit_schema import (
    AuditResponse,
)
from services.audit_service import AuditService

from core.dependencies import (
    get_audit_service,
    get_replica_verifier,
    get_tamper_monitor,
)

from audit.replica_verifier import ReplicaVerifier
from audit.tamper_monitor import TamperMonitor

from schemas.audit_schema import (
    AuditResponse,
    IntegrityReport,
    ReplicaVerificationResult,
)

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)





@router.get(
    "/chain",
    response_model=list[AuditResponse],
    summary="Get complete audit chain",
)
def get_audit_chain(
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Retrieve the complete audit chain ordered from oldest to newest.
    """

    return audit_service.get_audit_chain()


#   RECOVERY
@router.get(
    "/integrity",
    response_model=IntegrityReport,
    summary="Run complete audit integrity verification",
)
def verify_integrity(
    monitor: TamperMonitor = Depends(
        get_tamper_monitor,
    ),
):

    return monitor.run()


@router.get(
    "/recovery-history",
    response_model=list[AuditResponse],
    summary="Recovery audit history",
)
def recovery_history(
    audit_service: AuditService = Depends(
        get_audit_service,
    ),
):

    return audit_service.get_recovery_history()

@router.get(
    "/summary",
    summary="Audit summary",
)
def audit_summary(
    audit_service: AuditService = Depends(
        get_audit_service,
    ),
):

    return audit_service.get_audit_summary()

@router.get(
    "/{audit_id}",
    response_model=AuditResponse,
    summary="Get audit record by ID",
)
def get_audit_record(
    audit_id: UUID,
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Retrieve a single audit record.
    """

    audit = audit_service.get_audit_record(audit_id)

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit record not found.",
        )

    return audit


@router.get(
    "/replicas/{audit_id}",
    response_model=ReplicaVerificationResult,
    summary="Verify audit replicas",
)
def verify_replicas(
    audit_id: UUID,
    verifier: ReplicaVerifier = Depends(
        get_replica_verifier,
    ),
):

    return verifier.verify(
        audit_id,
    )

# Fimal audit endpoints

# GET /audit/{audit_id}
# GET /audit/chain
# GET /audit/integrity
# GET /audit/replicas/{audit_id}
# GET /audit/recovery-history
# GET /audit/summary