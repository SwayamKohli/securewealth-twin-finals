from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user, get_db)
from models.user import User
from schemas.dashboard_schema import (
    DashboardActivityResponse,
    DashboardSummaryResponse,
    FinancialHealthResponse,
)
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/",
    response_model=DashboardSummaryResponse,
)
def get_dashboard(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):
    try:
        service = DashboardService(db)

        return service.get_dashboard(
            user_id=current_user.user_id,
        )

    except Exception:
        logger.exception(
            "Error while fetching dashboard summary."
        )
        traceback.print_exc()
        raise


@router.get(
    "/activity",
    response_model=DashboardActivityResponse,
)
def get_activity(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):
    try:
        service = DashboardService(db)

        return service.get_activity(
            user_id=current_user.user_id,
        )

    except Exception:
        logger.exception(
            "Error while fetching dashboard activity."
        )
        traceback.print_exc()
        raise


@router.get(
    "/health",
    response_model=FinancialHealthResponse,
)
def get_financial_health(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):
    try:
        service = DashboardService(db)

        return service.get_financial_health(
            user_id=current_user.user_id,
        )

    except Exception:
        logger.exception(
            "Error while fetching financial health."
        )
        traceback.print_exc()
        raise