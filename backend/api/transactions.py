from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user, 
    get_db
)
from models.enums import TransactionStatus
from models.user import User
from schemas.transaction_schema import (
    InitiateTransactionRequest,
    TransactionResponse,
    TransactionStatusResponse,
)
from services.transaction_service import TransactionService

router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["Transactions"],
)


@router.post(
    "/initiate",
    response_model=TransactionResponse,
    status_code=201,
)
def initiate_transaction(
    request: InitiateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)

    return service.initiate_transaction(
        request=request,
        user_id=current_user.user_id,
    )


@router.get(
    "/",
    response_model=list[TransactionResponse],
)
def get_transactions(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    status: TransactionStatus | None = Query(default=None),
    account_id: UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)

    return service.get_transactions(
        user_id=current_user.user_id,
        from_date=from_date,
        to_date=to_date,
        status_filter=status,
        account_id=account_id,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)

    return service.get_transaction(
        transaction_id=transaction_id,
        user_id=current_user.user_id,
    )


@router.get(
    "/{transaction_id}/status",
    response_model=TransactionStatusResponse,
)
def get_transaction_status(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)

    return service.get_transaction_status(
        transaction_id=transaction_id,
        user_id=current_user.user_id,
    )