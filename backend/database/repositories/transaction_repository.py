# backend/database/repositories/transaction_repository.py (modified)
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        transaction: Transaction,
    ) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        self.db.refresh(transaction)

        return transaction

    def get_by_id(
        self,
        transaction_id: UUID,
    ) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(Transaction.transaction_id == transaction_id)
            .first()
        )

    def get_by_id_and_user(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.transaction_id == transaction_id,
                Transaction.user_id == user_id,
            )
            .first()
        )

    def get_all_by_user(
        self,
        user_id: UUID,
    ) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
            )
            .order_by(
                Transaction.transaction_time.desc(),
            )
            .all()
        )

    def get_filtered(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        status: TransactionStatus | None = None,
        account_id: UUID | None = None,
        decision: str | None = None,  # NEW: Filter by decision
    ) -> list[Transaction]:
        query = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
            )
        )

        if from_date is not None:
            query = query.filter(
                Transaction.transaction_time >= from_date,
            )

        if to_date is not None:
            query = query.filter(
                Transaction.transaction_time <= to_date,
            )

        if status is not None:
            query = query.filter(
                Transaction.status == status,
            )

        if account_id is not None:
            query = query.filter(
                Transaction.account_id == account_id,
            )
            
        # NEW: Filter by decision
        if decision is not None:
            query = query.filter(
                Transaction.decision == decision,
            )

        return (
            query.order_by(
                Transaction.transaction_time.desc(),
            )
            .all()
        )

    def get_status(
        self,
        transaction_id: UUID,
    ) -> tuple[TransactionStatus, datetime] | None:
        result = (
            self.db.query(
                Transaction.status,
                Transaction.transaction_time,
                Transaction.decision,  # NEW: Also return decision
                Transaction.decision_timestamp
            )
            .filter(
                Transaction.transaction_id == transaction_id,
            )
            .first()
        )
        
        if result:
            return result[0], result[1], result[2], result[3]  # status, time, decision, decision_time
        return None, None, None, None

    def get_recent_by_account(
        self,
        account_id: UUID,
        limit: int = 5,
    ) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
            )
            .order_by(
                Transaction.transaction_time.desc(),
            )
            .limit(limit)
            .all()
        )