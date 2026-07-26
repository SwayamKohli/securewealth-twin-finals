from uuid import UUID

from sqlalchemy.orm import Session

from models.loan import Loan


class LoanRepository:

    @staticmethod
    def create(
        db: Session,
        loan: Loan,
    ) -> Loan:
        db.add(loan)
        db.flush()
        db.refresh(loan)
        return loan

    @staticmethod
    def get_all_by_user(
        db: Session,
        user_id: UUID,
    ) -> list[Loan]:
        return (
            db.query(Loan)
            .filter(
                Loan.user_id == user_id,
            )
            .order_by(
                Loan.created_at.desc(),
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        loan_id: UUID,
    ) -> Loan | None:
        return (
            db.query(Loan)
            .filter(
                Loan.loan_id == loan_id,
            )
            .first()
        )

    @staticmethod
    def get_by_id_and_user(
        db: Session,
        loan_id: UUID,
        user_id: UUID,
    ) -> Loan | None:
        return (
            db.query(Loan)
            .filter(
                Loan.loan_id == loan_id,
                Loan.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        loan: Loan,
    ) -> Loan:
        db.flush()
        db.refresh(loan)
        return loan

    @staticmethod
    def delete(
        db: Session,
        loan: Loan,
    ) -> None:
        db.delete(loan)
        db.flush()