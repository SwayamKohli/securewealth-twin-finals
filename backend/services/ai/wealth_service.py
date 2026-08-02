import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from models.user import User
from schemas.wealth.wealth_schema import WealthRequest, WealthResponse
from ai.engines.fraud_engine import FraudIntelligenceEngine
from ai.engines.wealth_engine import WealthIntelligenceEngine
from ai.engines.profile_builder import FinancialProfileBuilder


logger = logging.getLogger(__name__)


class WealthService:
    def __init__(self, db: Session):
        self.wealth_engine = WealthIntelligenceEngine()
        self.profile_builder = FinancialProfileBuilder()
        # We'll get fraud engine from elsewhere when needed
    
    def generate_wealth_recommendations(self, request: WealthRequest, fraud_probability: float = 0.0) -> WealthResponse:
        """
        Generate personalized wealth recommendations based on financial profile.
        """
        try:
            # Build the financial profile from raw AA data
            profile = self.profile_builder.build_profile(request.profile_data)

            # Task 3.4: honour the fraud probability carried in the request
            # (previously silently ignored) unless the caller passes a
            # stricter value explicitly.
            effective_fraud_probability = max(
                fraud_probability,
                float(getattr(request, "fraud_probability", 0.0) or 0.0),
            )

            # Generate recommendations using the wealth engine
            result = self.wealth_engine.generate(
                profile=profile,
                fraud_probability=effective_fraud_probability
            )
            
            # Convert to response model
            return WealthResponse(
                suppressed=result['suppressed'],
                suppress_reason=result.get('suppress_reason'),
                user_id=result['user_id'],
                financial_health=result['financial_health'],
                recommendations=[
                    {
                        'recommendation_id': str(rec['recommendation_id']),  # Ensure string
                        'recommendation': str(rec['recommendation']),  # Ensure string
                        'product': str(rec['product']),  # Ensure string
                        'amount': int(rec.get('amount', 0)),  # Ensure integer
                        'tenure': str(rec.get('tenure', '')),  # Ensure string
                        'reason': str(rec['reason']),  # Ensure string
                        'confidence': float(rec['confidence']),  # Ensure float
                        'expected_benefit': str(rec['expected_benefit']),  # Ensure string
                        'priority': str(rec['priority']),  # Ensure string
                        'source': str(rec.get('source', '[8] Virginia Tech AAEC-184'))  # Ensure string
                    }
                    for rec in result['recommendations']
                ],
                goal_summaries=[
                    {
                        'goal_type': str(gs['goal_type']),  # Ensure string
                        'target_amount': float(gs['target_amount']),  # Ensure float
                        'gap': float(gs['gap']),  # Ensure float
                        'completion_pct': float(gs['completion_pct']),  # Ensure float
                        'months_remaining': int(gs['months_remaining']),  # Ensure integer
                        'feasibility': str(gs['feasibility']),  # Ensure string
                        'priority': str(gs['priority'])  # Ensure string
                    }
                    for gs in result['goal_summaries']
                ],
                wealth_position=result.get('wealth_position'),  # Task 3.2: Net Worth
                disclaimer=str(result['disclaimer'])  # Ensure string
            )
            
        except Exception as e:
            logger.exception("Error in wealth recommendation generation")
            raise