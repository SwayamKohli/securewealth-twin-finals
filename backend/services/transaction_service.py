# backend/services/transaction_service.py (modified)
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
from models.enums import AccountType, TransactionStatus
from models.transaction import Transaction
from schemas.transaction_schema import (
    InitiateTransactionRequest,
    TransactionResponse,
    TransactionStatusResponse,
)

# Unified backend security pipeline (Behavior -> Fraud ML -> Zero-Day -> Risk -> Decision)
from security.decision_engine import DecisionRecord
from services.security.security_pipeline import SecurityPipeline

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.account_repository = AccountRepository(db)
        self.security_pipeline = SecurityPipeline(db)

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

            # Task 2.3: investments are funded from Savings accounts only.
            if account.account_type != AccountType.SAVINGS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Investments can only be made from a Savings account.",
                )

            if account.balance < request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance.",
                )

            # NEW: Run security decision before processing transaction
            decision_record = self._evaluate_transaction_security(
                user_id=user_id,
                request=request,
                account=account
            )
            
            decision_time = self._parse_decision_timestamp(
                decision_record.decision_timestamp
            )

            # Adaptive security (task 4.2):
            #   ALLOW / WARN  -> complete immediately (silent for low risk)
            #   CHALLENGE     -> hold as PENDING until the customer verifies
            #   BLOCK         -> reject, nothing is debited
            if decision_record.decision == "BLOCK":
                txn_status = TransactionStatus.FAILED
            elif decision_record.decision == "CHALLENGE":
                txn_status = TransactionStatus.PENDING
            else:
                txn_status = TransactionStatus.SUCCESS
                new_balance: Decimal = account.balance - request.amount
                self.account_repository.update_balance(
                    account=account,
                    new_balance=new_balance,
                )

            transaction = Transaction(
                user_id=user_id,
                account_id=request.account_id,
                amount=request.amount,
                merchant_name=request.fund_name,
                merchant_category=request.fund_category,
                channel=request.channel,
                transaction_time=datetime.now(timezone.utc),
                status=txn_status,
                decision=decision_record.decision,
                decision_timestamp=decision_time,
            )

            transaction = self.transaction_repository.create(
                transaction,
            )

            self.db.commit()
            self.db.refresh(transaction)

            # CHALLENGE -> open a verification session (task 4.3)
            if txn_status == TransactionStatus.PENDING:
                from services.security.challenge_service import register_challenge

                trigger = ""
                if isinstance(decision_record.challenge_details, dict):
                    trigger = decision_record.challenge_details.get(
                        "trigger_signal", ""
                    )
                register_challenge(
                    transaction.transaction_id,
                    decision_record.challenge_type,
                    trigger,
                )

            # Task 2.8: exactly ONE immutable audit record per investment
            # request, written AFTER the final fraud decision. Audit failure
            # must never fail the customer's transaction.
            self._write_audit_record(
                transaction=transaction,
                user_id=user_id,
                decision_record=decision_record,
            )

            # Response carries the security verdict so the frontend never has
            # to orchestrate AI modules itself (task 2.4).
            response = TransactionResponse.model_validate(transaction)
            response.risk_score = decision_record.risk_score
            response.decision_report = (
                decision_record.report or decision_record.audit_note or None
            )
            response.challenge_required = decision_record.challenge_required
            response.challenge_type = decision_record.challenge_type or None

            # Real triggered signals, so the app can show what was actually
            # checked instead of guessing from the amount.
            signals = decision_record.security_signals or {}
            active = signals.get("active_behavior") or []
            response.triggered_signals = [str(x) for x in active if x]

            return response

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
                decision=transaction.decision,
                decision_timestamp=transaction.decision_timestamp,
                transaction_time=transaction.transaction_time,
            )

        except HTTPException:
            raise

        except Exception:
            logger.exception("Error while fetching transaction status.")
            traceback.print_exc()
            raise

    def complete_challenged_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> TransactionResponse:
        """
        Called by the ChallengeService once every verification step passes.
        Debits the account and marks the held (PENDING) investment SUCCESS.
        """
        try:
            transaction = self.transaction_repository.get_by_id_and_user(
                transaction_id=transaction_id,
                user_id=user_id,
            )
            if transaction is None:
                raise HTTPException(status_code=404, detail="Transaction not found.")
            if transaction.status != TransactionStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction is not awaiting verification.",
                )

            account = self.account_repository.get_by_id_and_user(
                account_id=transaction.account_id,
                user_id=user_id,
            )
            if account is None or account.balance < transaction.amount:
                transaction.status = TransactionStatus.FAILED
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance to complete the investment.",
                )

            self.account_repository.update_balance(
                account=account,
                new_balance=account.balance - transaction.amount,
            )
            transaction.status = TransactionStatus.SUCCESS
            self.db.commit()
            self.db.refresh(transaction)
            return TransactionResponse.model_validate(transaction)

        except HTTPException:
            raise
        except Exception:
            self.db.rollback()
            logger.exception("Error completing challenged transaction.")
            raise

    def _write_audit_record(
        self,
        *,
        transaction: Transaction,
        user_id: UUID,
        decision_record: DecisionRecord,
    ) -> None:
        """
        Audit flow (task 2.8):
            Investment Request -> Fraud Engine -> Decision -> Audit Entry.
        One immutable, hash-chained, signed record per investment.
        """
        try:
            # Imported lazily to keep the transaction path importable even if
            # audit key material is missing in a dev environment.
            from core.dependencies import (
                get_hash_chain_service,
                get_signature_service,
            )
            from database.repositories.audit_repository import AuditRepository
            from services.audit_service import AuditLogData, AuditService

            signals = decision_record.security_signals or {}
            context = signals.get("context") or {}
            ai_fraud = signals.get("ai_fraud") or {}

            # Severity is encoded in the reason code, e.g. "UNKNOWN_RISK_HIGH"
            severity = None
            if decision_record.unknown_risk_reason_code:
                severity = decision_record.unknown_risk_reason_code.rsplit("_", 1)[-1]

            trigger_signal = None
            if isinstance(decision_record.challenge_details, dict):
                trigger_signal = decision_record.challenge_details.get(
                    "trigger_signal"
                ) or decision_record.challenge_details.get("reason")

            audit_service = AuditService(
                audit_repo=AuditRepository(self.db),
                hash_service=get_hash_chain_service(),
                signature_service=get_signature_service(),
            )

            audit_service.log_security_decision(
                AuditLogData(
                    transaction_id=transaction.transaction_id,
                    user_id=user_id,
                    device_id=context.get("device_id"),
                    account_id=transaction.account_id,
                    event_type="TRANSACTION_SECURITY",
                    final_decision=decision_record.decision,
                    risk_score=decision_record.risk_score,
                    amount=transaction.amount,
                    channel=transaction.channel.value,
                    ai_status=(
                        decision_record.unknown_risk_decision or None
                        if decision_record.unknown_risk_applied
                        else "NORMAL"
                    ),
                    ai_confidence=ai_fraud.get("confidence"),
                    unknown_risk_severity=severity,
                    unknown_risk_applied=decision_record.unknown_risk_applied,
                    unknown_risk_decision=decision_record.unknown_risk_decision or None,
                    unknown_risk_reason_code=decision_record.unknown_risk_reason_code or None,
                    challenge_required=decision_record.challenge_required,
                    challenge_type=decision_record.challenge_type or None,
                    challenge_trigger_signal=trigger_signal,
                    security_signals=signals,
                    audit_note=decision_record.audit_note or decision_record.report,
                    compliance_reference=decision_record.compliance_ref or None,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "Audit record creation failed for transaction %s "
                "(transaction itself was NOT affected).",
                transaction.transaction_id,
            )

    @staticmethod
    def _parse_decision_timestamp(value: str | None) -> datetime:
        """DecisionRecord carries an ISO string; the DB column is DateTime."""
        if value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now(timezone.utc)

    def _evaluate_transaction_security(
        self,
        user_id: UUID,
        request: InitiateTransactionRequest,
        account: "Account",
    ) -> DecisionRecord:
        """
        Real-time fraud check (task 2.6). Delegates to the unified
        SecurityPipeline: Behavior -> Fraud ML -> Zero-Day -> Risk -> Decision.
        The pipeline is fail-safe: internal errors yield CHALLENGE, never ALLOW.
        """
        return self.security_pipeline.evaluate(
            user_id=user_id,
            account_id=request.account_id,
            amount=float(request.amount),
            channel=request.channel.value,
            recipient_id=request.fund_name,
        )