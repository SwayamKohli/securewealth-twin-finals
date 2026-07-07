from uuid import UUID

from sqlalchemy.orm import Session

from models.deposit import Deposit


class DepositRepository:

    @staticmethod
    def create(
        db: Session,
        deposit: Deposit,
    ) -> Deposit:
        db.add(deposit)
        db.flush()
        db.refresh(deposit)
        return deposit

    @staticmethod
    def get_all_by_user(
        db: Session,
        user_id: UUID,
    ) -> list[Deposit]:
        return (
            db.query(Deposit)
            .filter(
                Deposit.user_id == user_id,
            )
            .order_by(
                Deposit.created_at.desc(),
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        deposit_id: UUID,
    ) -> Deposit | None:
        return (
            db.query(Deposit)
            .filter(
                Deposit.deposit_id == deposit_id,
            )
            .first()
        )

    @staticmethod
    def get_by_id_and_user(
        db: Session,
        deposit_id: UUID,
        user_id: UUID,
    ) -> Deposit | None:
        return (
            db.query(Deposit)
            .filter(
                Deposit.deposit_id == deposit_id,
                Deposit.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        deposit: Deposit,
    ) -> Deposit:
        db.flush()
        db.refresh(deposit)
        return deposit

    @staticmethod
    def delete(
        db: Session,
        deposit: Deposit,
    ) -> None:
        db.delete(deposit)
        db.flush()