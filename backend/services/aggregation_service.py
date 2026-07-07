from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from schemas.aggregation_schema import (
    AggregatedAccountResponse,
    AggregationStatusResponse,
    CashflowResponse,
    LinkAccountRequest,
    NetWorthResponse,
    SyncResponse,
)
from schemas.account_schema import CreateAccountRequest
from services.account_service import AccountService
from services.deposit_service import DepositService
from services.loan_service import LoanService
from services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class AggregationService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.account_service = AccountService(db)
        self.transaction_service = TransactionService(db)
        self.deposit_service = DepositService()
        self.loan_service = LoanService()

    def get_accounts(
        self,
        user_id: UUID,
    ) -> list[AggregatedAccountResponse]:
        try:
            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            return [
                AggregatedAccountResponse.model_validate(account)
                for account in accounts
            ]

        except Exception:
            logger.exception("Error while fetching aggregated accounts.")
            traceback.print_exc()
            raise

    def get_account(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> AggregatedAccountResponse:
        try:
            account = self.account_service.get_account(
                account_id=account_id,
                user_id=user_id,
            )

            return AggregatedAccountResponse.model_validate(
                account,
            )

        except Exception:
            logger.exception("Error while fetching aggregated account.")
            traceback.print_exc()
            raise

    def link_account(
        self,
        user_id: UUID,
        request: LinkAccountRequest,
    ):
        try:
            account_request = CreateAccountRequest(
                bank_name=request.bank_name,
                account_type=request.account_type,
                account_number=request.account_number,
                balance=request.balance,
                currency=request.currency,
            )

            return self.account_service.create_account(
                user_id=user_id,
                request=account_request,
            )

        except Exception:
            logger.exception("Error while linking account.")
            traceback.print_exc()
            raise

    def remove_account(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> None:
        try:
            self.account_service.delete_account(
                account_id=account_id,
                user_id=user_id,
            )

        except Exception:
            logger.exception("Error while removing account.")
            traceback.print_exc()
            raise

    def sync(
        self,
        user_id: UUID,
    ) -> SyncResponse:
        try:
            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            return SyncResponse(
                success=True,
                synced_accounts=len(accounts),
                message="Aggregation sync completed successfully.",
                synced_at=datetime.now(timezone.utc),
            )

        except Exception:
            logger.exception("Error while syncing aggregation.")
            traceback.print_exc()
            raise

    def get_status(
        self,
        user_id: UUID,
    ) -> AggregationStatusResponse:
        try:
            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            latest_sync = None

            if accounts:
                latest_sync = max(
                    account.updated_at
                    for account in accounts
                )

            return AggregationStatusResponse(
                accounts_connected=len(accounts),
                last_synced=latest_sync,
                healthy=True,
                status="CONNECTED",
            )

        except Exception:
            logger.exception("Error while fetching aggregation status.")
            traceback.print_exc()
            raise

    def get_net_worth(
        self,
        user_id: UUID,
    ) -> NetWorthResponse:
        try:
            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            deposits = self.deposit_service.get_deposits(
                db=self.db,
                user_id=user_id,
            )

            loans = self.loan_service.get_loans(
                db=self.db,
                user_id=user_id,
            )

            total_account_balance = sum(
                (
                    account.balance
                    for account in accounts
                ),
                Decimal("0.00"),
            )

            total_deposits = sum(
                (
                    deposit.principal
                    for deposit in deposits
                ),
                Decimal("0.00"),
            )

            total_liabilities = sum(
                (
                    loan.outstanding_amount
                    for loan in loans
                ),
                Decimal("0.00"),
            )

            total_assets = (
                total_account_balance
                + total_deposits
            )

            net_worth = (
                total_assets
                - total_liabilities
            )

            return NetWorthResponse(
                total_account_balance=total_account_balance,
                total_deposits=total_deposits,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                net_worth=net_worth,
            )

        except Exception:
            logger.exception("Error while calculating net worth.")
            traceback.print_exc()
            raise

    def get_cashflow(
        self,
        user_id: UUID,
    ) -> CashflowResponse:
        try:
            transactions = self.transaction_service.get_transactions(
                user_id=user_id,
            )

            total_income = Decimal("0.00")
            total_expenses = Decimal("0.00")

            for transaction in transactions:

                if transaction.amount >= 0:
                    total_income += transaction.amount
                else:
                    total_expenses += abs(
                        transaction.amount
                    )

            net_cashflow = (
                total_income
                - total_expenses
            )

            return CashflowResponse(
                total_income=total_income,
                total_expenses=total_expenses,
                net_cashflow=net_cashflow,
                transaction_count=len(transactions),
            )

        except Exception:
            logger.exception("Error while calculating cash flow.")
            traceback.print_exc()
            raise