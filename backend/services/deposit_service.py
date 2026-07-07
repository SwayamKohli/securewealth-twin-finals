import traceback
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.repositories.deposit_repository import DepositRepository
from models.deposit import Deposit
from schemas.deposit_schema import (
    CreateDepositRequest,
    UpdateDepositRequest,
)


class DepositService:

    @staticmethod
    def create_deposit(
        db: Session,
        user_id: UUID,
        request: CreateDepositRequest,
    ) -> Deposit:
        try:
            deposit = Deposit(
                user_id=user_id,
                deposit_type=request.deposit_type,
                principal=request.principal,
                interest_rate=request.interest_rate,
                start_date=request.start_date,
                maturity_date=request.maturity_date,
                institution=request.institution,
            )

            deposit = DepositRepository.create(
                db=db,
                deposit=deposit,
            )

            db.commit()

            return deposit

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def get_deposits(
        db: Session,
        user_id: UUID,
    ) -> list[Deposit]:
        return DepositRepository.get_all_by_user(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def get_deposit(
        db: Session,
        deposit_id: UUID,
        user_id: UUID,
    ) -> Deposit:
        deposit = DepositRepository.get_by_id_and_user(
            db=db,
            deposit_id=deposit_id,
            user_id=user_id,
        )

        if deposit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deposit not found.",
            )

        return deposit

    @staticmethod
    def update_deposit(
        db: Session,
        deposit_id: UUID,
        user_id: UUID,
        request: UpdateDepositRequest,
    ) -> Deposit:
        deposit = DepositRepository.get_by_id_and_user(
            db=db,
            deposit_id=deposit_id,
            user_id=user_id,
        )

        if deposit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deposit not found.",
            )

        try:
            update_data = request.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            for field, value in update_data.items():
                setattr(
                    deposit,
                    field,
                    value,
                )

            deposit = DepositRepository.update(
                db=db,
                deposit=deposit,
            )

            db.commit()

            return deposit

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def delete_deposit(
        db: Session,
        deposit_id: UUID,
        user_id: UUID,
    ) -> None:
        deposit = DepositRepository.get_by_id_and_user(
            db=db,
            deposit_id=deposit_id,
            user_id=user_id,
        )

        if deposit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deposit not found.",
            )

        try:
            DepositRepository.delete(
                db=db,
                deposit=deposit,
            )

            db.commit()

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise