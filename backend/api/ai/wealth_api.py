from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.wealth.wealth_schema import WealthRequest, WealthResponse
from services.ai.wealth_service import WealthService

router = APIRouter(
    prefix="/api/v1/ai/wealth",
    tags=["Wealth Intelligence"],
)


@router.post(
    "/recommendations",
    response_model=WealthResponse,
)
def generate_wealth_recommendations(
    request: WealthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate personalized wealth recommendations based on financial profile.
    """
    service = WealthService(db)
    return service.generate_wealth_recommendations(request)


@router.post(
    "/profile-analysis",
    response_model=WealthResponse,
)
def analyze_profile_for_recommendations(
    request: WealthRequest,
    fraud_probability: float = 0.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze financial profile and generate recommendations with fraud probability consideration.
    """
    service = WealthService(db)
    return service.generate_wealth_recommendations(request, fraud_probability=fraud_probability)