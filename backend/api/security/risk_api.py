from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.security.risk_schema import RiskEvaluationInput, RiskEvaluationOutput
from services.security.risk_service import RiskService

router = APIRouter(
    prefix="/api/v1/security/risk",
    tags=["Risk Evaluation"],
)


@router.post(
    "/evaluate",
    response_model=RiskEvaluationOutput,
)
def evaluate_transaction_risk(
    request: RiskEvaluationInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate transaction risk using the risk engine.
    """
    service = RiskService(db)
    return service.evaluate_risk(request)