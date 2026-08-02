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
from ai.engines.i18n_catalog import narrative
from ai.engines.device_trust_explainability import DeviceTrustExplainer
from ai.engines.fraud_explanability import generate_risk_breakdown
from ai.engines.unknown_risk_explanability import generate_unknown_risk_explanation
from ai.engines.wealth_explainability import RecommendationExplainer
from ai.engines import llm_source

router = APIRouter(prefix="/api/v1/ai/explainability", tags=["Explainability"])

@router.post("/phishing", response_model=PhishingExplanationResponse)
def explain_phishing_detection(
    request: PhishingExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate explanation for phishing detection results."""
    try:
        # get_phishing_explanation() reads ATTRIBUTES off a ScanResult object,
        # but the API receives a plain dict. Wrap it so both work.
        from types import SimpleNamespace

        raw = request.scan_result
        scan_obj = SimpleNamespace(
            phishing_score=float(raw.get("phishing_score", 0.0) or 0.0),
            risk_level=str(raw.get("risk_level", "SAFE")),
            fired_signals=raw.get("fired_signals", []),
            detected_keywords=raw.get("detected_keywords", {}),
            signal_groups_fired=raw.get("signal_groups_fired", []),
            negative_signals_found=raw.get("negative_signals_found", []),
            signal_count=int(raw.get("signal_count", 0) or 0),
            top_signal=raw.get("top_signal"),
            message=raw.get("message", ""),
            scanned_at=raw.get("scanned_at", ""),
        )
        explanation = get_phishing_explanation(scan_obj)
        # Multilingual output (task 5.5): template catalog for hi/pa
        if request.language in ("hi", "pa"):
            top = str(
                request.scan_result.get("top_signal")
                or (request.scan_result.get("signal_groups_fired") or [""])[0]
                or ""
            ).upper()
            key_map = {
                "LINK": "SUSPICIOUS_LINK", "URL": "SUSPICIOUS_LINK",
                "SENDER": "UNKNOWN_SENDER", "DOMAIN": "FAKE_DOMAIN",
                "URGEN": "URGENT_LANGUAGE", "OTP": "OTP_SCAM",
            }
            key = "SAFE"
            risk = str(request.scan_result.get("risk_level", "")).upper()
            if risk not in ("", "SAFE", "LOW"):
                key = next((v for frag, v in key_map.items() if frag in top), "URGENT_LANGUAGE")
            localized = narrative("phishing", key, request.language)
            if localized:
                explanation = {**explanation, "explanation": localized, "source": "TEMPLATE_" + request.language.upper()}
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
        # Multilingual output (task 5.5)
        if request.language in ("hi", "pa"):
            ctype = str(request.requirement.get("challenge_type", "")).upper()
            localized = narrative("challenge", ctype, request.language)
            if localized:
                return ChallengeExplanationResponse(
                    explanation=localized,
                    source="template_" + request.language,
                )
        explanation = generate_challenge_instruction(
            request.requirement, 
            request.ollama_url or "http://localhost:11434"
        )
        # Report what ACTUALLY produced the text. The previous version keyed
        # off request.ollama_url, so a default-URL request that the local model
        # answered was still reported as "template".
        return ChallengeExplanationResponse(
            explanation=explanation, source=llm_source.take()
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
        # Multilingual output (task 5.5)
        if request.language in ("hi", "pa"):
            decision = str(request.record.get("decision", "")).upper()
            localized = narrative("decision", decision, request.language)
            if localized:
                # Curated translation, not model output — label it honestly.
                return DecisionExplanationResponse(explanation=localized, source="catalog")
        explanation = generate_customer_explanation(
            request.record,
            request.ollama_url or "http://localhost:11434"
        )
        return DecisionExplanationResponse(
            explanation=explanation, source=llm_source.take()
        )
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
        return RiskExplanationResponse(
            explanation=explanation, source=llm_source.take()
        )
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
        return UnknownRiskExplanationResponse(
            explanation=explanation, source=llm_source.take()
        )
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