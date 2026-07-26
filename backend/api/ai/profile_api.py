from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.wealth.profile_schema import ProfileRequest, ProfileResponse
from services.ai.profile_service import ProfileService

router = APIRouter(
    prefix="/api/v1/ai/profile",
    tags=["Financial Profile"],
)


@router.post(
    "/build",
    response_model=ProfileResponse,
)
def build_financial_profile(
    request: ProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build a unified financial profile from raw account aggregation data.
    """
    service = ProfileService(db)
    return service.build_financial_profile(request)