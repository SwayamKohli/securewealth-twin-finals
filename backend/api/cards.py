from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user, get_db)
from models.user import User
from schemas.card_schema import (
    CardResponse,
    CreateCardRequest,
    UpdateCardRequest,
)
from services.card_service import CardService

router = APIRouter(
    prefix="/api/v1/cards",
    tags=["Cards"],
)


@router.post(
    "/",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_card(
    request: CreateCardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CardService.create_card(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )


@router.get(
    "/",
    response_model=list[CardResponse],
)
def get_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CardService.get_cards(
        db=db,
        user_id=current_user.user_id,
    )


@router.get(
    "/{card_id}",
    response_model=CardResponse,
)
def get_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CardService.get_card(
        db=db,
        card_id=card_id,
        user_id=current_user.user_id,
    )


@router.put(
    "/{card_id}",
    response_model=CardResponse,
)
def update_card(
    card_id: UUID,
    request: UpdateCardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CardService.update_card(
        db=db,
        card_id=card_id,
        user_id=current_user.user_id,
        request=request,
    )


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CardService.delete_card(
        db=db,
        card_id=card_id,
        user_id=current_user.user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )