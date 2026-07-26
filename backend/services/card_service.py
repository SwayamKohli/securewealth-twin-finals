import traceback
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.repositories.card_repository import CardRepository
from models.card import Card
from schemas.card_schema import (
    CreateCardRequest,
    UpdateCardRequest,
)


class CardService:

    @staticmethod
    def create_card(
        db: Session,
        user_id: UUID,
        request: CreateCardRequest,
    ) -> Card:
        try:
            card = Card(
                user_id=user_id,
                card_type=request.card_type,
                issuer=request.issuer,
                reward_type=request.reward_type,
                cashback_rate=request.cashback_rate,
                credit_limit=request.credit_limit,
            )

            card = CardRepository.create(
                db=db,
                card=card,
            )

            db.commit()

            return card

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def get_cards(
        db: Session,
        user_id: UUID,
    ) -> list[Card]:
        return CardRepository.get_all_by_user(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def get_card(
        db: Session,
        card_id: UUID,
        user_id: UUID,
    ) -> Card:
        card = CardRepository.get_by_id_and_user(
            db=db,
            card_id=card_id,
            user_id=user_id,
        )

        if card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found.",
            )

        return card

    @staticmethod
    def update_card(
        db: Session,
        card_id: UUID,
        user_id: UUID,
        request: UpdateCardRequest,
    ) -> Card:
        card = CardRepository.get_by_id_and_user(
            db=db,
            card_id=card_id,
            user_id=user_id,
        )

        if card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found.",
            )

        try:
            update_data = request.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            for field, value in update_data.items():
                setattr(
                    card,
                    field,
                    value,
                )

            card = CardRepository.update(
                db=db,
                card=card,
            )

            db.commit()

            return card

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def delete_card(
        db: Session,
        card_id: UUID,
        user_id: UUID,
    ) -> None:
        card = CardRepository.get_by_id_and_user(
            db=db,
            card_id=card_id,
            user_id=user_id,
        )

        if card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found.",
            )

        try:
            CardRepository.delete(
                db=db,
                card=card,
            )

            db.commit()

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise