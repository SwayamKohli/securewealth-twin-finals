from __future__ import annotations

import logging
import traceback
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.repositories.account_repository import AccountRepository
from schemas.account_schema import (
    AccountResponse,
    AccountSummaryResponse,
    BalanceResponse,
)
from database.repositories.transaction_repository import TransactionRepository
from schemas.transaction_schema import TransactionResponse

from models.account import Account

from schemas.account_schema import (
    CreateAccountRequest,
)

from models.enums import AccountType

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, db: Session):
        self.repository = AccountRepository(db)
        self.transaction_repository = TransactionRepository(db)

    def get_accounts(
        self,
        user_id: UUID,
    ) -> list[AccountResponse]:
        try:
            accounts = self.repository.get_all_by_user(user_id)

            return [
                AccountResponse.model_validate(account)
                for account in accounts
            ]

        except HTTPException:
            raise

        except Exception as e:
            logger.exception("Error while fetching accounts.")
            traceback.print_exc()
            raise

    def get_account(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> AccountResponse:
        try:
            account = self.repository.get_by_id_and_user(
                account_id=account_id,
                user_id=user_id,
            )

            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

            return AccountResponse.model_validate(account)

        except HTTPException:
            raise

        except Exception as e:
            logger.exception("Error while fetching account.")
            traceback.print_exc()
            raise

    def get_balance(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> BalanceResponse:
        try:
            account = self.repository.get_by_id_and_user(
                account_id=account_id,
                user_id=user_id,
            )

            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

            return BalanceResponse(
                account_id=account.account_id,
                balance=account.balance,
                currency=account.currency,
                last_updated=account.updated_at,
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.exception("Error while fetching account balance.")
            traceback.print_exc()
            raise

    def get_summary(
    self,
    account_id: UUID,
    user_id: UUID,
    ) -> AccountSummaryResponse:
        try:
            account = self.repository.get_by_id_and_user(
                account_id=account_id,
                user_id=user_id,
            )

            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

            recent_transactions = (
                self.transaction_repository.get_recent_by_account(
                    account_id=account.account_id,
                    limit=5,
                )
            )

            return AccountSummaryResponse(
                account=AccountResponse.model_validate(account),
                current_balance=account.balance,
                recent_transactions=[
                    TransactionResponse.model_validate(transaction)
                    for transaction in recent_transactions
                ],
            )

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while fetching account summary.")
            traceback.print_exc()
            raise
    
    def create_account(
    self,
    user_id: UUID,
    request: CreateAccountRequest,
    ) -> AccountResponse:
        try:
            masked_account_number = (
                "X" * (len(request.account_number) - 4)
                + request.account_number[-4:]
            )

            account = Account(
                user_id=user_id,
                bank_name=request.bank_name,
                account_type=AccountType(request.account_type),
                account_number_masked=masked_account_number,
                balance=request.balance,
                currency=request.currency,
            )

            account = self.repository.create(
                account=account,
            )

            self.repository.db.commit()

            return AccountResponse.model_validate(
                account,
            )

        except HTTPException:
            self.repository.db.rollback()
            raise

        except Exception:
            self.repository.db.rollback()
            logger.exception("Error while creating account.")
            traceback.print_exc()
            raise

    def delete_account(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> None:
        try:
            account = self.repository.get_by_id_and_user(
                account_id=account_id,
                user_id=user_id,
            )

            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

            self.repository.delete(
                account=account,
            )

            self.repository.db.commit()

        except HTTPException:
            self.repository.db.rollback()
            raise

        except Exception:
            self.repository.db.rollback()
            logger.exception("Error while deleting account.")
            traceback.print_exc()
            raise