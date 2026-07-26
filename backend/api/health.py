from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_db
from services.health_service import HealthService
from schemas.health_schema import (
    HealthResponse,
    ServiceHealthResponse,
)

router = APIRouter(
    prefix="/health",
    tags=["System Health"],
)


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Overall system health",
)
def get_system_health(
    db: Session = Depends(get_db),
):
    """
    Check the overall health of the application.

    Includes:
    - Database connectivity
    - Application metadata
    """

    response = HealthService.get_system_health(db)

    if response.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump(),
        )

    return response


@router.get(
    "/services",
    response_model=ServiceHealthResponse,
    summary="Internal service health",
)
def get_service_health(
    db: Session = Depends(get_db),
):
    """
    Check the health of internal application services.

    Includes:
    - Database
    - Authentication
    - Dashboard
    - Aggregation
    - Notifications
    - Audit
    """

    response = HealthService.get_service_health(db)

    if response.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump(),
        )

    return response