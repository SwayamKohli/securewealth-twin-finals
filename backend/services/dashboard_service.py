from __future__ import annotations

import logging
import traceback
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from schemas.dashboard_schema import (
    DashboardActivityResponse,
    DashboardSummaryResponse,
    FinancialHealthResponse,
    NetWorthResponse,
)
from schemas.user_schema import UserResponse
from services.account_service import AccountService
from services.deposit_service import DepositService
from services.loan_service import LoanService
from services.transaction_service import TransactionService
from services.user_service import UserService

logger = logging.getLogger(__name__)


class DashboardService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.account_service = AccountService(db)
        self.transaction_service = TransactionService(db)

    def get_dashboard(
        self,
        user_id: UUID,
    ) -> DashboardSummaryResponse:
        try:
            user = UserService.get_me(
                db=self.db,
                user_id=user_id,
            )

            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            transactions = self.transaction_service.get_transactions(
                user_id=user_id,
            )

            deposits = DepositService.get_deposits(
                db=self.db,
                user_id=user_id,
            )

            loans = LoanService.get_loans(
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

            total_deposit_principal = sum(
                (
                    deposit.principal
                    for deposit in deposits
                ),
                Decimal("0.00"),
            )

            total_outstanding_loans = sum(
                (
                    loan.outstanding_amount
                    for loan in loans
                ),
                Decimal("0.00"),
            )

            total_assets = (
                total_account_balance
                + total_deposit_principal
            )

            total_liabilities = (
                total_outstanding_loans
            )

            net_worth = (
                total_assets
                - total_liabilities
            )

            recent_transactions = sorted(
                transactions,
                key=lambda transaction: transaction.transaction_time,
                reverse=True,
            )[:5]

            return DashboardSummaryResponse(
                user=UserResponse.model_validate(
                    user,
                ),
                accounts=accounts,
                net_worth=NetWorthResponse(
                    total_assets=total_assets,
                    total_liabilities=total_liabilities,
                    net_worth=net_worth,
                ),
                recent_transactions=recent_transactions,
                notifications=[],
            )

        except Exception:
            logger.exception(
                "Error while fetching dashboard summary."
            )
            traceback.print_exc()
            raise

    def get_activity(
        self,
        user_id: UUID,
    ) -> DashboardActivityResponse:
        try:
            transactions = self.transaction_service.get_transactions(
                user_id=user_id,
            )

            transactions = sorted(
                transactions,
                key=lambda transaction: transaction.transaction_time,
                reverse=True,
            )

            return DashboardActivityResponse(
                transactions=transactions,
            )

        except Exception:
            logger.exception(
                "Error while fetching dashboard activity."
            )
            traceback.print_exc()
            raise

    def get_financial_health(
        self,
        user_id: UUID,
    ) -> FinancialHealthResponse:
        try:
            accounts = self.account_service.get_accounts(
                user_id=user_id,
            )

            deposits = DepositService.get_deposits(
                db=self.db,
                user_id=user_id,
            )

            loans = LoanService.get_loans(
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

            total_deposit_principal = sum(
                (
                    deposit.principal
                    for deposit in deposits
                ),
                Decimal("0.00"),
            )

            total_outstanding_loans = sum(
                (
                    loan.outstanding_amount
                    for loan in loans
                ),
                Decimal("0.00"),
            )

            total_assets = (
                total_account_balance
                + total_deposit_principal
            )

            total_liabilities = (
                total_outstanding_loans
            )

            net_worth = (
                total_assets
                - total_liabilities
            )

            return FinancialHealthResponse(
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                net_worth=net_worth,
                total_accounts=len(accounts),
                total_deposits=len(deposits),
                total_loans=len(loans),
            )

        except Exception:
            logger.exception(
                "Error while fetching financial health."
            )
            traceback.print_exc()
            raise