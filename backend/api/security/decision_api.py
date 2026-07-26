from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.security.decision_schema import TransactionContext, DecisionRecord
from services.security.decision_service import DecisionService

router = APIRouter(
    prefix="/api/v1/security/decision",
    tags=["Decision Engine"],
)


@router.post(
    "/make",
    response_model=DecisionRecord,
)
def make_transaction_decision(
    request: TransactionContext,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Make final transaction decision using the decision engine.
    """
    service = DecisionService(db)
    return service.make_decision(request)