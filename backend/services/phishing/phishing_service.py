from typing import Dict, Any
from sqlalchemy.orm import Session

from models.user import User
from schemas.phishing.phishing_schema import PhishingScanRequest, PhishingScanResponse
from ai.engines.phishing_engine import scan_message


class PhishingService:
    def __init__(self, db: Session):
        # No initialization needed for phishing engine - it's all functions
        pass
    
    def scan_message_content(self, request: PhishingScanRequest) -> PhishingScanResponse:
        """
        Scan a message for phishing content using the phishing detection engine.
        """
        try:
            # Call the phishing engine
            result = scan_message(request.message, request.context)
            
            return PhishingScanResponse(
                phishing_score=result.phishing_score,
                risk_level=result.risk_level,
                fired_signals=result.fired_signals,
                detected_keywords=result.detected_keywords,
                signal_groups_fired=result.signal_groups_fired,
                negative_signals_found=result.negative_signals_found,
                signal_count=result.signal_count,
                top_signal=result.top_signal,
                message=request.message,
                scanned_at=result.scanned_at if hasattr(result, 'scanned_at') else ""
            )
            
        except Exception as e:
            print(f"Error in phishing scanning: {str(e)}")
            raise