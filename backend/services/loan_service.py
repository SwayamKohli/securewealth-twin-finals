import traceback
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.repositories.loan_repository import LoanRepository
from models.loan import Loan
from schemas.loan_schema import (
    CreateLoanRequest,
    UpdateLoanRequest,
)


class LoanService:

    @staticmethod
    def create_loan(
        db: Session,
        user_id: UUID,
        request: CreateLoanRequest,
    ) -> Loan:
        try:
            loan = Loan(
                user_id=user_id,
                loan_type=request.loan_type,
                outstanding_amount=request.outstanding_amount,
                emi=request.emi,
                interest_rate=request.interest_rate,
                remaining_tenure=request.remaining_tenure,
            )

            loan = LoanRepository.create(
                db=db,
                loan=loan,
            )

            db.commit()

            return loan

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def get_loans(
        db: Session,
        user_id: UUID,
    ) -> list[Loan]:
        return LoanRepository.get_all_by_user(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def get_loan(
        db: Session,
        loan_id: UUID,
        user_id: UUID,
    ) -> Loan:
        loan = LoanRepository.get_by_id_and_user(
            db=db,
            loan_id=loan_id,
            user_id=user_id,
        )

        if loan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found.",
            )

        return loan

    @staticmethod
    def update_loan(
        db: Session,
        loan_id: UUID,
        user_id: UUID,
        request: UpdateLoanRequest,
    ) -> Loan:
        loan = LoanRepository.get_by_id_and_user(
            db=db,
            loan_id=loan_id,
            user_id=user_id,
        )

        if loan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found.",
            )

        try:
            update_data = request.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            for field, value in update_data.items():
                setattr(
                    loan,
                    field,
                    value,
                )

            loan = LoanRepository.update(
                db=db,
                loan=loan,
            )

            db.commit()

            return loan

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def delete_loan(
        db: Session,
        loan_id: UUID,
        user_id: UUID,
    ) -> None:
        loan = LoanRepository.get_by_id_and_user(
            db=db,
            loan_id=loan_id,
            user_id=user_id,
        )

        if loan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found.",
            )

        try:
            LoanRepository.delete(
                db=db,
                loan=loan,
            )

            db.commit()

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise