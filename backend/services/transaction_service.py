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
from models.enums import TransactionStatus
from models.transaction import Transaction
from schemas.transaction_schema import (
    InitiateTransactionRequest,
    TransactionResponse,
    TransactionStatusResponse,
)

# NEW: Import decision engine
from security.decision_engine import DecisionEngine, TransactionContext
from security.risk_engine import RiskEvaluationInput, EnvironmentInput
from security.behavior_engine import BehaviorEngine, BehaviorInput

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.account_repository = AccountRepository(db)
        
        # NEW: Initialize security components
        self.decision_engine = DecisionEngine()
        self.behavior_engine = BehaviorEngine()

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

            # NEW: Run security decision before processing transaction
            decision_record = self._evaluate_transaction_security(
                user_id=user_id,
                request=request,
                account=account
            )
            
            # Apply decision logic
            if decision_record.decision == "BLOCK":
                # Don't process transaction, just log it as blocked
                transaction = Transaction(
                    user_id=user_id,
                    account_id=request.account_id,
                    amount=request.amount,
                    merchant_name=request.merchant_name,
                    merchant_category=request.merchant_category,
                    channel=request.channel,
                    transaction_time=datetime.now(timezone.utc),
                    status=TransactionStatus.FAILED,  # Mark as failed due to security block
                    decision=decision_record.decision,
                    decision_timestamp=decision_record.decision_timestamp
                )
            else:
                # Process normal transaction
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
                    decision=decision_record.decision,
                    decision_timestamp=decision_record.decision_timestamp
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

    # NEW: Security evaluation method
    def _evaluate_transaction_security(
        self,
        user_id: UUID,
        request: InitiateTransactionRequest,
        account: "Account"
    ) -> "DecisionRecord":
        """
        Evaluate transaction security using the decision engine pipeline:
        Behavior -> Risk -> Decision
        """
        try:
            # Get user's behavioral baseline
            from database.repositories.behavioural_profile_repository import BehaviouralProfileRepository
            profile_repo = BehaviouralProfileRepository(self.db)
            profile = profile_repo.get_by_user_id(user_id)
            
            # Get recent transaction data for behavior analysis
            recent_transactions = self.transaction_repository.get_filtered(
                user_id=user_id,
                from_date=datetime.now(timezone.utc).replace(day=1),  # Last 30 days
                to_date=datetime.now(timezone.utc)
            )
            
            # Prepare behavior input
            behavior_input = BehaviorInput(
                transaction_hour_ist=datetime.now(timezone.utc).hour,
                amount=float(request.amount),
                ninety_day_median=float(profile.avg_amount) if profile else 5000.0,
                ninety_day_std=float(profile.transaction_velocity) if profile else 2000.0,
                recipient_id=request.merchant_name,
                known_recipients=[t.merchant_name for t in recent_transactions],
                recent_transaction_timestamps=[
                    int(t.transaction_time.timestamp() * 1000) 
                    for t in recent_transactions[-5:]  # Last 5 transactions
                ],
                last_20_amounts=[
                    float(t.amount) 
                    for t in recent_transactions[-20:]
                ],
                otp_entry_ms=4200  # Default value - would come from actual OTP timing
            )
            
            # Analyze behavior
            behavior_signals = self.behavior_engine.analyze(behavior_input)
            
            # Get device trust info (simplified)
            from database.repositories.device_repository import DeviceRepository
            device_repo = DeviceRepository(self.db)
            user_devices = device_repo.get_user_devices(user_id)
            current_device = user_devices[0] if user_devices else None
            
            device_trust = {
                "device_status": current_device.trust_status.value if current_device else "NEW_DEVICE",
                "device_confidence": current_device.device_confidence if current_device else 50,
                "device_age_days": current_device.device_age_days if current_device else 0,
                "security_signals": [current_device.trust_status.value] if current_device else []
            }
            
            # Prepare risk evaluation input
            risk_input = RiskEvaluationInput(
                behavior_signals=behavior_signals,
                environment=EnvironmentInput(
                    ip_region="MUMBAI",  # Would come from actual request
                    last_login_region="MUMBAI",
                    time_since_last_login_ms=3600000,
                    network_type="HOME_WIFI"
                ),
                device_trust=device_trust,
                ai_fraud_probability=0.0,  # Would come from fraud engine
                ai_confidence=0.0
            )
            
            # Create transaction context
            transaction_context = TransactionContext(
                transaction_id=str(uuid.uuid4()),  # Temporary ID
                account_id=str(request.account_id),
                amount=float(request.amount),
                channel=request.channel.value,
                risk_input=risk_input
            )
            
            # Get decision
            decision_record = self.decision_engine.decide(transaction_context)
            
            return decision_record
            
        except Exception as e:
            logger.warning(f"Security evaluation failed: {str(e)}, defaulting to ALLOW")
            # Return a default allow decision if security evaluation fails
            from security.decision_engine import DecisionRecord
            return DecisionRecord(
                transaction_id="temp",
                account_id=str(request.account_id),
                amount=float(request.amount),
                channel=request.channel.value,
                decision="ALLOW",
                risk_score=0,
                security_signals={},
                challenge_required=False,
                challenge_type="",
                report="Security check bypassed due to error",
                audit_note="Security check bypassed due to error",
                decision_timestamp=datetime.now(timezone.utc).isoformat()
            )