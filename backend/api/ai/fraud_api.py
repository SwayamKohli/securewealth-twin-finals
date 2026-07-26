from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.wealth.fraud_schema import FraudRequest, FraudResponse
from services.ai.fraud_service import FraudService

router = APIRouter(
    prefix="/api/v1/ai/fraud",
    tags=["Fraud Intelligence"],
)


@router.post(
    "/evaluate",
    response_model=FraudResponse,
)
def evaluate_fraud(
    request: FraudRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate a transaction for fraud probability.
    """
    service = FraudService(db)
    return service.evaluate_fraud(request)


@router.post(
    "/batch-evaluate",
    response_model=list[FraudResponse],
)
def batch_evaluate_fraud(
    requests: list[FraudRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate multiple transactions for fraud probability.
    """
    service = FraudService(db)
    results = []
    for req in requests:
        try:
            result = service.evaluate_fraud(req)
            results.append(result)
        except Exception as e:
            print(f"Error evaluating transaction {req.transaction_id}: {str(e)}")
            # Return a default response for failed evaluations
            results.append(FraudResponse(
                fraud_probability=0.0,
                confidence=0.0,
                risk_factors=[],
                signal_scores={},
                ml_details={},
                baseline_used="error"
            ))
    return results