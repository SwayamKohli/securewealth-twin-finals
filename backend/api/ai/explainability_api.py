from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.explainability_schema import (
    PhishingExplanationRequest,
    PhishingExplanationResponse,
    ChallengeExplanationRequest,
    ChallengeExplanationResponse,
    DecisionExplanationRequest,
    DecisionExplanationResponse,
    DeviceTrustExplanationRequest,
    DeviceTrustExplanationResponse,
    RiskExplanationRequest,
    RiskExplanationResponse,
    UnknownRiskExplanationRequest,
    UnknownRiskExplanationResponse,
    WealthExplanationRequest,
    WealthExplanationResponse
)

from ai.engines.phishing_explanability import get_phishing_explanation
from ai.engines.decision_explanability import generate_customer_explanation
from ai.engines.challenge_explanability import generate_challenge_instruction
from ai.engines.device_trust_explainability import DeviceTrustExplainer
from ai.engines.fraud_explanability import generate_risk_breakdown
from ai.engines.unknown_risk_explanability import generate_unknown_risk_explanation
from ai.engines.wealth_explainability import RecommendationExplainer

router = APIRouter(prefix="/api/v1/ai/explainability", tags=["Explainability"])

@router.post("/phishing", response_model=PhishingExplanationResponse)
def explain_phishing_detection(
    request: PhishingExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for phishing detection results."""
    try:
        explanation = get_phishing_explanation(request.scan_result)
        return PhishingExplanationResponse(**explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/challenge", response_model=ChallengeExplanationResponse)
def explain_challenge_requirement(
    request: ChallengeExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for challenge requirements."""
    try:
        explanation = generate_challenge_instruction(
            request.requirement, 
            request.ollama_url or "http://localhost:11434"
        )
        return ChallengeExplanationResponse(
            explanation=explanation,
            source="llm" if request.ollama_url else "template"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision", response_model=DecisionExplanationResponse)
def explain_decision(
    request: DecisionExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for transaction decisions."""
    try:
        explanation = generate_customer_explanation(
            request.record,
            request.ollama_url or "http://localhost:11434"
        )
        return DecisionExplanationResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/device-trust", response_model=DeviceTrustExplanationResponse)
def explain_device_trust(
    request: DeviceTrustExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for device trust status."""
    try:
        explainer = DeviceTrustExplainer()
        result = explainer.explain(request.trust_result, request.user_profile)
        return DeviceTrustExplanationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk", response_model=RiskExplanationResponse)
def explain_risk_breakdown(
    request: RiskExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for risk evaluation."""
    try:
        explanation = generate_risk_breakdown(
            request.output,
            request.ollama_url or "http://localhost:11434"
        )
        return RiskExplanationResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unknown-risk", response_model=UnknownRiskExplanationResponse)
def explain_unknown_risk(
    request: UnknownRiskExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for unknown risk events."""
    try:
        explanation = generate_unknown_risk_explanation(
            request.decision_output,
            request.ollama_url or "http://localhost:11434"
        )
        return UnknownRiskExplanationResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wealth", response_model=WealthExplanationResponse)
def explain_wealth_recommendations(
    request: WealthExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanations for wealth recommendations."""
    try:
        explainer = RecommendationExplainer()
        result = explainer.explain(request.wealth_result, request.profile)
        return WealthExplanationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))