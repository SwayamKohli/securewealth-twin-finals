from typing import Dict, Any
from sqlalchemy.orm import Session

from models.user import User
from schemas.security.risk_schema import RiskEvaluationInput, RiskEvaluationOutput
from security.risk_engine import evaluate_risk, RiskEvaluationInput as EngineRiskInput, EnvironmentInput as EngineEnvInput
from security.behavior_engine import BehaviorEngine, BehaviorInput as BehInput, BehaviorSignals


class RiskService:
    def __init__(self, db: Session):
        self.behavior_engine = BehaviorEngine()
    
    def evaluate_risk(self, request: RiskEvaluationInput) -> RiskEvaluationOutput:
        """
        Evaluate transaction risk using the risk engine.
        """
        try:
            # Prepare behavior signals
            behavior_input = BehInput(
                transaction_hour_ist=request.behavior_signals.get('transaction_hour_ist', 12),
                amount=request.behavior_signals.get('amount', 0.0),
                ninety_day_median=request.behavior_signals.get('ninety_day_median', 1000.0),
                ninety_day_std=request.behavior_signals.get('ninety_day_std', 500.0),
                recipient_id=request.behavior_signals.get('recipient_id', ''),
                known_recipients=request.behavior_signals.get('known_recipients', []),
                recent_transaction_timestamps=request.behavior_signals.get('recent_transaction_timestamps', []),
                last_20_amounts=request.behavior_signals.get('last_20_amounts', []),
                otp_entry_ms=request.behavior_signals.get('otp_entry_ms', 9500)
            )
            
            behavior_signals = self.behavior_engine.analyze(behavior_input)
            
            # Prepare environment input
            env_input = EngineEnvInput(
                ip_region=request.environment['ip_region'],
                last_login_region=request.environment['last_login_region'],
                time_since_last_login_ms=request.environment['time_since_last_login_ms'],
                network_type=request.environment['network_type']
            )
            
            # Prepare risk evaluation input for the engine
            engine_input = EngineRiskInput(
                behavior_signals=behavior_signals,
                environment=env_input,
                device_trust=request.device_trust,
                ai_fraud_probability=request.ai_fraud_probability,
                ai_confidence=request.ai_confidence
            )
            
            # Call the risk engine
            result = evaluate_risk(engine_input)
            
            return RiskEvaluationOutput(
                risk_score=result.risk_score,
                security_signals=result.security_signals,
                timestamp=result.timestamp,
                compliance_note=result.compliance_note
            )
            
        except Exception as e:
            print(f"Error in risk evaluation: {str(e)}")
            raise