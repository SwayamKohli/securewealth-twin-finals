from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user,get_db)
from models.user import User
from schemas.aggregation_schema import (
    AggregatedAccountResponse,
    AggregationStatusResponse,
    CashflowResponse,
    LinkAccountRequest,
    NetWorthResponse,
    SyncRequest,
    SyncResponse,
)
from services.aggregation_service import AggregationService

router = APIRouter(
    prefix="/api/v1/aggregation",
    tags=["Aggregation"],
)


@router.get(
    "/accounts",
    response_model=list[AggregatedAccountResponse],
    status_code=status.HTTP_200_OK,
)
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_accounts(
        user_id=current_user.user_id,
    )


@router.get(
    "/accounts/{account_id}",
    response_model=AggregatedAccountResponse,
    status_code=status.HTTP_200_OK,
)
def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/accounts/link",
    status_code=status.HTTP_201_CREATED,
)
def link_account(
    request: LinkAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.link_account(
        user_id=current_user.user_id,
        request=request,
    )


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    service.remove_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/sync",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
def sync_aggregation(
    request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.sync(
        user_id=current_user.user_id,
    )


@router.get(
    "/status",
    response_model=AggregationStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_status(
        user_id=current_user.user_id,
    )


@router.get(
    "/net-worth",
    response_model=NetWorthResponse,
    status_code=status.HTTP_200_OK,
)
def get_net_worth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_net_worth(
        user_id=current_user.user_id,
    )


@router.get(
    "/cashflow",
    response_model=CashflowResponse,
    status_code=status.HTTP_200_OK,
)
def get_cashflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_cashflow(
        user_id=current_user.user_id,
    )