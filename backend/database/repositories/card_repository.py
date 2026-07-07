from uuid import UUID

from sqlalchemy.orm import Session

from models.card import Card


class CardRepository:

    @staticmethod
    def create(
        db: Session,
        card: Card,
    ) -> Card:
        db.add(card)
        db.flush()
        db.refresh(card)
        return card

    @staticmethod
    def get_all_by_user(
        db: Session,
        user_id: UUID,
    ) -> list[Card]:
        return (
            db.query(Card)
            .filter(
                Card.user_id == user_id,
            )
            .order_by(
                Card.created_at.desc(),
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        card_id: UUID,
    ) -> Card | None:
        return (
            db.query(Card)
            .filter(
                Card.card_id == card_id,
            )
            .first()
        )

    @staticmethod
    def get_by_id_and_user(
        db: Session,
        card_id: UUID,
        user_id: UUID,
    ) -> Card | None:
        return (
            db.query(Card)
            .filter(
                Card.card_id == card_id,
                Card.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        card: Card,
    ) -> Card:
        db.flush()
        db.refresh(card)
        return card

    @staticmethod
    def delete(
        db: Session,
        card: Card,
    ) -> None:
        db.delete(card)
        db.flush()