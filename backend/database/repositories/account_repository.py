from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from models.account import Account


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_user(
        self,
        user_id: UUID,
    ) -> list[Account]:
        return (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .order_by(Account.created_at.desc())
            .all()
        )

    def get_by_id(
        self,
        account_id: UUID,
    ) -> Account | None:
        return (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
        )

    def get_by_id_and_user(
        self,
        account_id: UUID,
        user_id: UUID,
    ) -> Account | None:
        return (
            self.db.query(Account)
            .filter(
                Account.account_id == account_id,
                Account.user_id == user_id,
            )
            .first()
        )

    def get_balance(
        self,
        account_id: UUID,
    ):
        return (
            self.db.query(
                Account.balance,
                Account.currency,
                Account.updated_at,
            )
            .filter(Account.account_id == account_id)
            .first()
        )

    def update_balance(
        self,
        account: Account,
        new_balance: Decimal,
    ) -> Account:
        account.balance = new_balance
        self.db.flush()
        self.db.refresh(account)

        return account

    def exists(
        self,
        account_id: UUID,
    ) -> bool:
        return (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
            is not None
        )

    def count_by_user(
        self,
        user_id: UUID,
    ) -> int:
        return (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .count()
        )
    
    def create(
    self,
    account: Account,
    ) -> Account:
        self.db.add(account)
        self.db.flush()
        self.db.refresh(account)
        return account
    
    def update(
    self,
    account: Account,
    ) -> Account:
        self.db.flush()
        self.db.refresh(account)
        return account
    
    def delete(
    self,
    account: Account,
    ) -> None:
        self.db.delete(account)
        self.db.flush()