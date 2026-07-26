from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user, get_db)
from models.user import User
from schemas.deposit_schema import (
    CreateDepositRequest,
    DepositResponse,
    UpdateDepositRequest,
)
from services.deposit_service import DepositService

router = APIRouter(
    prefix="/api/v1/deposits",
    tags=["Deposits"],
)


@router.post(
    "/",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deposit(
    request: CreateDepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DepositService.create_deposit(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )


@router.get(
    "/",
    response_model=list[DepositResponse],
)
def get_deposits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DepositService.get_deposits(
        db=db,
        user_id=current_user.user_id,
    )


@router.get(
    "/{deposit_id}",
    response_model=DepositResponse,
)
def get_deposit(
    deposit_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DepositService.get_deposit(
        db=db,
        deposit_id=deposit_id,
        user_id=current_user.user_id,
    )


@router.put(
    "/{deposit_id}",
    response_model=DepositResponse,
)
def update_deposit(
    deposit_id: UUID,
    request: UpdateDepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DepositService.update_deposit(
        db=db,
        deposit_id=deposit_id,
        user_id=current_user.user_id,
        request=request,
    )


@router.delete(
    "/{deposit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_deposit(
    deposit_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    DepositService.delete_deposit(
        db=db,
        deposit_id=deposit_id,
        user_id=current_user.user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )