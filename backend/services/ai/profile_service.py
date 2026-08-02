import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from models.user import User
from schemas.wealth.profile_schema import ProfileRequest, ProfileResponse
from ai.engines.profile_builder import FinancialProfileBuilder
from ai.engines.account_analyzer   import analyze_accounts
from ai.engines.cashflow_analyzer  import analyze_cashflow
from ai.engines.liability_analyzer import analyze_liabilities
from ai.engines.goal_analyzer      import analyze_goals

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, db: Session):
        self.profile_builder = FinancialProfileBuilder()
    
    def build_financial_profile(self, request: ProfileRequest) -> ProfileResponse:
        """
        Build a unified financial profile from raw account aggregation data.
        """
        try:
            profile = self.profile_builder.build_profile(request.aa_data)
            return ProfileResponse(profile=profile)
            
        except Exception as e:
            logger.exception("Error in profile building")
            raise