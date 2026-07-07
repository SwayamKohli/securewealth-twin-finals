from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.repositories.account_repository import AccountRepository
from database.repositories.transaction_repository import TransactionRepository
from models.enums import TransactionStatus
from models.transaction import Transaction
from schemas.transaction_schema import (
    InitiateTransactionRequest,
    TransactionResponse,
    TransactionStatusResponse,
)

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.account_repository = AccountRepository(db)

    def initiate_transaction(
        self,
        request: InitiateTransactionRequest,
        user_id: UUID,
    ) -> TransactionResponse:
        try:
            account = self.account_repository.get_by_id_and_user(
                account_id=request.account_id,
                user_id=user_id,
            )

            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

            if account.balance < request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance.",
                )

            new_balance: Decimal = account.balance - request.amount

            self.account_repository.update_balance(
                account=account,
                new_balance=new_balance,
            )

            transaction = Transaction(
                user_id=user_id,
                account_id=request.account_id,
                amount=request.amount,
                merchant_name=request.merchant_name,
                merchant_category=request.merchant_category,
                channel=request.channel,
                transaction_time=datetime.now(timezone.utc),
                status=TransactionStatus.SUCCESS,
            )

            transaction = self.transaction_repository.create(
                transaction,
            )

            self.db.commit()
            self.db.refresh(transaction)

            return TransactionResponse.model_validate(
                transaction,
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception:
            self.db.rollback()
            logger.exception("Error while initiating transaction.")
            traceback.print_exc()
            raise

    def get_transactions(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        status_filter: TransactionStatus | None = None,
        account_id: UUID | None = None,
    ) -> list[TransactionResponse]:
        try:
            if account_id is not None:
                account = self.account_repository.get_by_id_and_user(
                    account_id=account_id,
                    user_id=user_id,
                )

                if account is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Account not found.",
                    )
            
            print(f"from_date: {from_date}, to_date: {to_date}, status_filter: {status_filter}, account_id: {account_id}")

            if to_date:
                to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            transactions = self.transaction_repository.get_filtered(
                user_id=user_id,
                from_date=from_date,
                to_date=to_date,
                status=status_filter,
                account_id=account_id,
            )

            return [
                TransactionResponse.model_validate(transaction)
                for transaction in transactions
            ]

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while fetching transactions.")
            traceback.print_exc()
            raise

    def get_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> TransactionResponse:
        try:
            transaction = self.transaction_repository.get_by_id_and_user(
                transaction_id=transaction_id,
                user_id=user_id,
            )

            if transaction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            return TransactionResponse.model_validate(
                transaction,
            )

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while fetching transaction.")
            traceback.print_exc()
            raise

    def get_transaction_status(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> TransactionStatusResponse:
        try:
            transaction = self.transaction_repository.get_by_id_and_user(
                transaction_id=transaction_id,
                user_id=user_id,
            )

            if transaction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            return TransactionStatusResponse(
                transaction_id=transaction.transaction_id,
                status=transaction.status,
                transaction_time=transaction.transaction_time,
            )

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while fetching transaction status.")
            traceback.print_exc()
            raise