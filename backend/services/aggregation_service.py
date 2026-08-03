from __future__ import annotations

import logging
import traceback
from datetime import datetime, timedelta, timezone
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

# NEW: Import AI services
from services.ai.profile_service import ProfileService
from services.ai.wealth_service import WealthService
from schemas.wealth.profile_schema import ProfileRequest
from schemas.wealth.wealth_schema import WealthRequest

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
        
        # NEW: AI services
        self.profile_service = ProfileService(db)
        self.wealth_service = WealthService(db)

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
                    Decimal(str(d.principal))  # FIXED: Convert to string then Decimal
                    for d in deposits
                ),
                Decimal("0.00"),
            )

            total_liabilities = sum(
                (
                    Decimal(str(l.outstanding_amount))  # FIXED: Convert to string then Decimal
                    for l in loans
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

    # One month. Every figure this method returns is a MONTHLY figure, because
    # everything downstream treats it as one: profile_builder maps
    # total_expenses straight onto monthly_expenses, and the emergency-fund
    # target is 4 x that number.
    #
    # This previously summed the customer's ENTIRE history with no window at
    # all. The seeder writes 90 days, so every "monthly" figure was 3x real:
    # runway came out a third of the truth and the emergency-fund target became
    # twelve months of spending. Swayam has 5.2 months of runway and was still
    # told to build an emergency fund, because 400,000 / (54,000 x 3) = 2.5.
    # It also drifted upward for the whole demo, since each new investment was
    # added to the lifetime total.
    CASHFLOW_WINDOW_DAYS = 30

    def get_cashflow(
        self,
        user_id: UUID,
    ) -> CashflowResponse:
        try:
            from schemas.transaction_schema import APPROVED_FUND_CATEGORIES

            transactions = self.transaction_service.get_transactions(
                user_id=user_id,
            )

            cutoff = datetime.now(timezone.utc) - timedelta(
                days=self.CASHFLOW_WINDOW_DAYS
            )

            total_income = Decimal("0.00")
            total_expenses = Decimal("0.00")
            total_invested = Decimal("0.00")
            counted = 0

            for transaction in transactions:
                when = getattr(transaction, "transaction_time", None) or getattr(
                    transaction, "created_at", None
                )
                if when is not None:
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=timezone.utc)
                    if when < cutoff:
                        continue

                # Only settled money moves. A blocked or pending investment has
                # not left the account, so counting it would misstate the month.
                status = str(getattr(transaction, "status", "") or "").upper()
                if status and "SUCCESS" not in status:
                    continue

                counted += 1
                # get_transactions returns TransactionResponse, where the DB's
                # merchant_category is exposed as fund_category. Reading only
                # the DB name gave "" for every row, so nothing was ever
                # recognised as an investment and every SIP was counted as
                # income — Ayush showed ₹8,26,500 of income on a ₹1,50,000
                # salary. Accept either name so this works whether it is handed
                # ORM rows or response models.
                category = str(
                    getattr(transaction, "fund_category", None)
                    or getattr(transaction, "merchant_category", "")
                    or ""
                ).strip().upper()

                # An investment is not income and not an expense — it is the
                # customer moving their own money from cash into an asset.
                # Counting SIPs as income (the old behaviour) inflated income
                # every time anyone demoed an investment.
                if category in APPROVED_FUND_CATEGORIES:
                    total_invested += abs(transaction.amount)
                    continue

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
                transaction_count=counted,
                # Named explicitly so nothing downstream has to assume the
                # window. profile_builder prefers these over the totals.
                monthly_income=total_income,
                monthly_expenses=total_expenses,
                monthly_invested=total_invested,
                period_days=self.CASHFLOW_WINDOW_DAYS,
            )

        except Exception:
            logger.exception("Error while calculating cash flow.")
            traceback.print_exc()
            raise

    # NEW: Methods that integrate with AI engines
    def generate_financial_profile(
        self,
        user_id: UUID,
    ) -> dict:
        """
        Generate a unified financial profile using the AI profile builder.
        """
        try:
            # Gather all financial data
            accounts = self.account_service.get_accounts(user_id=user_id)
            deposits = self.deposit_service.get_deposits(db=self.db, user_id=user_id)
            loans = self.loan_service.get_loans(db=self.db, user_id=user_id)
            
            # Get recent transactions for cashflow analysis
            transactions = self.transaction_service.get_transactions(user_id=user_id)
            
            # Construct AA data format expected by profile builder
            aa_data = {
                "user_id": str(user_id),
                "accounts": [
                    {
                        "account_id": str(acc.account_id),
                        "account_type": str(acc.account_type.value),
                        "balance": float(acc.balance),  # Convert Decimal to float for JSON serialization
                        "currency": str(acc.currency)
                    }
                    for acc in accounts
                ],
                "deposits": [
                    {
                        "deposit_id": str(dep.deposit_id),
                        "deposit_type": str(dep.deposit_type.value),
                        "principal": float(dep.principal),  # Convert Decimal to float
                        "interest_rate": float(dep.interest_rate),
                        "maturity_date": str(dep.maturity_date),
                        "institution": str(dep.institution)
                    }
                    for dep in deposits
                ],
                "loans": [
                    {
                        "loan_id": str(ln.loan_id),
                        "loan_type": str(ln.loan_type.value),
                        "outstanding_amount": float(ln.outstanding_amount),  # Convert Decimal to float
                        "emi": float(ln.emi),
                        "interest_rate": float(ln.interest_rate),
                        "remaining_tenure": ln.remaining_tenure
                    }
                    for ln in loans
                ],
                "transactions": [
                    {
                        "transaction_id": str(tx.transaction_id),
                        "amount": float(tx.amount),  # Convert Decimal to float
                        # get_transactions hands back TransactionResponse, which
                        # exposes these as fund_*. Reading only merchant_* would
                        # raise AttributeError. Nothing routes here today, but
                        # the rename has already caused one silent bug.
                        "merchant_name": str(
                            getattr(tx, "fund_name", None)
                            or getattr(tx, "merchant_name", "")
                        ),
                        "merchant_category": str(
                            getattr(tx, "fund_category", None)
                            or getattr(tx, "merchant_category", "")
                        ),
                        "channel": str(tx.channel.value),
                        "transaction_time": str(tx.transaction_time),
                        "status": str(tx.status.value)
                    }
                    for tx in transactions
                ]
            }
            
            # Build financial profile using AI
            profile_request = ProfileRequest(aa_data=aa_data)
            profile_response = self.profile_service.build_financial_profile(profile_request)
            
            return profile_response.profile
            
        except Exception as e:
            logger.exception("Error while generating financial profile.")
            traceback.print_exc()
            raise

    def generate_wealth_recommendations(
        self,
        user_id: UUID,
        fraud_probability: float = 0.0,
    ) -> dict:
        """
        Generate wealth recommendations using the AI wealth engine.
        """
        try:
            # First, get the financial profile
            profile = self.generate_financial_profile(user_id)
            
            # Create wealth request
            wealth_request = WealthRequest(
                profile_data=profile,
                fraud_probability=fraud_probability
            )
            
            # Generate recommendations
            wealth_response = self.wealth_service.generate_wealth_recommendations(
                wealth_request,
                fraud_probability=fraud_probability
            )
            
            return {
                "suppressed": wealth_response.suppressed,
                "recommendations": wealth_response.recommendations,
                "financial_health": wealth_response.financial_health,
                "goal_summaries": wealth_response.goal_summaries,
                "disclaimer": wealth_response.disclaimer
            }
            
        except Exception as e:
            logger.exception("Error while generating wealth recommendations.")
            traceback.print_exc()
            raise