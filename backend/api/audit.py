from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import get_audit_service
from schemas.audit_schema import (
    AuditResponse,
)
from services.audit_service import AuditService

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


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