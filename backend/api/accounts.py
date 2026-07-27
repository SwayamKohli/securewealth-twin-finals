from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    get_db,
)
from models.user import User
from schemas.account_schema import (
    AccountResponse,
    AccountSummaryResponse,
    BalanceResponse,
    CreateAccountRequest,
    UpdateAccountRequest,
)
from services.account_service import AccountService

router = APIRouter(
    prefix="/api/v1/accounts",
    tags=["Accounts"],
)


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    request: CreateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.create_account(
        user_id=current_user.user_id,
        request=request,
    )


@router.get(
    "/",
    response_model=list[AccountResponse],
)
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.get_accounts(
        user_id=current_user.user_id,
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
)
def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.get_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
)
def update_account(
    account_id: UUID,
    request: UpdateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.update_account(
        account_id=account_id,
        user_id=current_user.user_id,
        request=request,
    )


@router.get(
    "/{account_id}/balance",
    response_model=BalanceResponse,
)
def get_balance(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.get_balance(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.get(
    "/{account_id}/summary",
    response_model=AccountSummaryResponse,
)
def get_summary(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    return service.get_summary(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    service.delete_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )
    
    return None