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


@router.get(
    "/ai",
    summary="Which AI models are actually loaded",
)
def get_ai_health():
    """
    Report the live state of every optional ML component.

    Both the zero-day detector and the explanation engines degrade silently to
    a fallback when their artifacts or services are missing — which means a
    working model and a broken one look identical from the outside. This makes
    the answer checkable:

        GET /api/v1/health/ai

    Used on stage to prove the autoencoder is running rather than asserting it.
    """
    from services.security.security_pipeline import zero_day_status
    from ai.engines import llm_source

    zd = zero_day_status()
    ollama_up = llm_source.ollama_available()

    return {
        "zero_day": zd,
        "explanations": {
            "source": "llm" if ollama_up else "template",
            "engine": "llama3 via Ollama" if ollama_up else "deterministic templates",
            "detail": (
                "local model reachable"
                if ollama_up
                else "Ollama unreachable — explanations use the offline templates"
            ),
        },
        # Plain-language summary for the admin dashboard / a quick glance.
        "summary": (
            f"Zero-day: {zd['detector']} · "
            f"Explanations: {'local LLM' if ollama_up else 'templates'}"
        ),
    }
