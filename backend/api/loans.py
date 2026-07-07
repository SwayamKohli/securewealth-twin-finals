from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user, get_db)
from models.user import User
from schemas.loan_schema import (
    CreateLoanRequest,
    LoanResponse,
    UpdateLoanRequest,
)
from services.loan_service import LoanService

router = APIRouter(
    prefix="/api/v1/loans",
    tags=["Loans"],
)


@router.post(
    "/",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_loan(
    request: CreateLoanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LoanService.create_loan(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )


@router.get(
    "/",
    response_model=list[LoanResponse],
)
def get_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LoanService.get_loans(
        db=db,
        user_id=current_user.user_id,
    )


@router.get(
    "/{loan_id}",
    response_model=LoanResponse,
)
def get_loan(
    loan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LoanService.get_loan(
        db=db,
        loan_id=loan_id,
        user_id=current_user.user_id,
    )


@router.put(
    "/{loan_id}",
    response_model=LoanResponse,
)
def update_loan(
    loan_id: UUID,
    request: UpdateLoanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LoanService.update_loan(
        db=db,
        loan_id=loan_id,
        user_id=current_user.user_id,
        request=request,
    )


@router.delete(
    "/{loan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_loan(
    loan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    LoanService.delete_loan(
        db=db,
        loan_id=loan_id,
        user_id=current_user.user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )