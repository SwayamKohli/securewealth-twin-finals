from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.phishing.phishing_schema import PhishingScanRequest, PhishingScanResponse
from services.phishing.phishing_service import PhishingService

router = APIRouter(
    prefix="/api/v1/phishing",
    tags=["Phishing Detection"],
)


@router.post(
    "/scan",
    response_model=PhishingScanResponse,
)
def scan_message_for_phishing(
    request: PhishingScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Scan a message for phishing content.
    """
    service = PhishingService(db)
    return service.scan_message_content(request)


@router.post(
    "/bulk-scan",
    response_model=list[PhishingScanResponse],
)
def bulk_scan_messages(
    requests: list[PhishingScanRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Scan multiple messages for phishing content.
    """
    service = PhishingService(db)
    results = []
    for req in requests:
        try:
            result = service.scan_message_content(req)
            results.append(result)
        except Exception as e:
            print(f"Error scanning message: {str(e)}")
            # Return a default response for failed scans
            results.append(PhishingScanResponse(
                phishing_score=0.0,
                risk_level="SAFE",
                fired_signals=[],
                detected_keywords={},
                signal_groups_fired=[],
                negative_signals_found=[],
                signal_count=0,
                top_signal=None,
                message=req.message,
                scanned_at=""
            ))
    return results