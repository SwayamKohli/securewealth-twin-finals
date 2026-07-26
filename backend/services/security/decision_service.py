from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.user import User
from schemas.security.decision_schema import TransactionContext, DecisionRecord
from security.decision_engine import DecisionEngine, TransactionContext as EngineTxnCtx
from security.risk_engine import RiskEvaluationInput as EngineRiskInput, EnvironmentInput as EngineEnvInput
from security.behavior_engine import BehaviorEngine, BehaviorInput as BehInput, BehaviorSignals


class DecisionService:
    def __init__(self, db: Session):
        self.decision_engine = DecisionEngine()
        self.behavior_engine = BehaviorEngine()
    
    def make_decision(self, request: TransactionContext) -> DecisionRecord:
        """
        Make final transaction decision using the decision engine.
        """
        try:
            # Convert the request data to engine-compatible format
            # First, convert behavior signals if they exist in the risk_input
            risk_input_data = request.risk_input
            
            # Prepare behavior signals
            if 'behavior_signals' in risk_input_data:
                behavior_data = risk_input_data['behavior_signals']
                behavior_input = BehInput(
                    transaction_hour_ist=behavior_data.get('transaction_hour_ist', 12),
                    amount=behavior_data.get('amount', 0.0),
                    ninety_day_median=behavior_data.get('ninety_day_median', 1000.0),
                    ninety_day_std=behavior_data.get('ninety_day_std', 500.0),
                    recipient_id=behavior_data.get('recipient_id', ''),
                    known_recipients=behavior_data.get('known_recipients', []),
                    recent_transaction_timestamps=behavior_data.get('recent_transaction_timestamps', []),
                    last_20_amounts=behavior_data.get('last_20_amounts', []),
                    otp_entry_ms=behavior_data.get('otp_entry_ms', 9500)
                )
                
                behavior_signals = self.behavior_engine.analyze(behavior_input)
            else:
                # Create a basic behavior signal if not provided
                behavior_signals = BehaviorSignals()
            
            # Prepare environment input
            env_input = EngineEnvInput(
                ip_region=risk_input_data['environment']['ip_region'],
                last_login_region=risk_input_data['environment']['last_login_region'],
                time_since_last_login_ms=risk_input_data['environment']['time_since_last_login_ms'],
                network_type=risk_input_data['environment']['network_type']
            )
            
            # Prepare risk input for the engine
            engine_risk_input = EngineRiskInput(
                behavior_signals=behavior_signals,
                environment=env_input,
                device_trust=risk_input_data['device_trust'],
                ai_fraud_probability=risk_input_data.get('ai_fraud_probability', 0.0),
                ai_confidence=risk_input_data.get('ai_confidence', 0.0)
            )
            
            # Create engine transaction context
            engine_ctx = EngineTxnCtx(
                transaction_id=request.transaction_id,
                account_id=request.account_id,
                amount=request.amount,
                channel=request.channel,
                risk_input=engine_risk_input,
                unknown_risk_event=request.unknown_risk_event
            )
            
            # Call the decision engine
            decision_result = self.decision_engine.decide(engine_ctx)
            
            # Convert to response model
            return DecisionRecord(
                transaction_id=decision_result.transaction_id,
                account_id=decision_result.account_id,
                amount=decision_result.amount,
                channel=decision_result.channel,
                decision=decision_result.decision,
                risk_score=decision_result.risk_score,
                security_signals=decision_result.security_signals,
                challenge_required=decision_result.challenge_required,
                challenge_type=decision_result.challenge_type,
                challenge_details=decision_result.challenge_details,
                unknown_risk_applied=decision_result.unknown_risk_applied,
                unknown_risk_decision=decision_result.unknown_risk_decision,
                unknown_risk_reason_code=decision_result.unknown_risk_reason_code,
                report=decision_result.report,
                audit_note=decision_result.audit_note,
                decision_timestamp=decision_result.decision_timestamp,
                compliance_ref=decision_result.compliance_ref
            )
            
        except Exception as e:
            print(f"Error in decision making: {str(e)}")
            raise