from typing import Dict, Any
from sqlalchemy.orm import Session

from models.user import User
from schemas.wealth.fraud_schema import FraudRequest, FraudResponse
from ai.engines.fraud_engine import FraudIntelligenceEngine


class FraudService:
    def __init__(self, db: Session):
        # Initialize the fraud engine from disk once at service startup
        self.fraud_engine = FraudIntelligenceEngine.from_disk()
    
    def evaluate_fraud(self, request: FraudRequest) -> FraudResponse:
        """
        Evaluate a transaction for fraud probability using the fraud intelligence engine.
        """
        try:
            # Convert the request to a dict that the fraud engine expects
            transaction_dict = {
                'user_id': request.user_id,
                'device_id': request.device_id,
                'recipient_id': request.recipient_id,
                'amount': request.amount,
                'hour': request.hour,
                'day_of_week': request.day_of_week,
                'otp_time_sec': request.otp_time_sec,
                'session_duration': request.session_duration,
                'txns_last_1h': request.txns_last_1h,
                'txns_last_24h': request.txns_last_24h,
                'in_active_window': request.in_active_window
            }
            
            # Call the fraud engine
            result = self.fraud_engine.evaluate(transaction_dict)
            
            # Convert result to response model
            return FraudResponse(
                fraud_probability=result['fraud_probability'],
                confidence=result['confidence'],
                risk_factors=result['risk_factors'],
                signal_scores=result['signal_scores'],
                ml_details=result['ml_details'],
                baseline_used=result['baseline_used']
            )
            
        except Exception as e:
            # Log the error appropriately
            print(f"Error in fraud evaluation: {str(e)}")
            raise