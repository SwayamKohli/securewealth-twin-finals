import json
import logging
import re
import requests
from typing import Any, Dict
from dataclasses import asdict
from ai.engines import llm_source

logger = logging.getLogger(__name__)

# Banned engineering or technical system jargon
_BANNED_TERMS = frozenset([
    "dataclass", "handler", "override", "severity", "status", "reason_code",
    "advanced", "security systems", "monitoring", "precautionary", "surveillance",
    "algorithms", "intelligence", "anomaly", "audit", "confidence", "backend"
])

_DEFAULT_COMPLIANCE_TEXT = "This verification is part of our routine digital asset protection measures."


def generate_unknown_risk_explanation(decision_output: Any, ollama_url: str = "http://localhost:11434") -> str:
    """
    Translates an UnknownRiskDecision into an empathetic, layman-friendly statement.
    Safely intercepts low-confidence events to explicitly assure the user of total safety.
    """
    # ── 1. Extract Attributes Safely ──
    if hasattr(decision_output, "to_dict"):
        decision_dict = decision_output.to_dict()
    elif hasattr(decision_output, "__dataclass_fields__"):
        decision_dict = asdict(decision_output)
    else:
        decision_dict = dict(decision_output)

    # A DecisionRecord carries these under `unknown_risk_*` names, while the
    # zero-day engine emits them unprefixed. Accept both, or the severity and
    # decision fall back to LOW/WARN and the customer is told a held payment
    # "processed smoothly".
    def _pick(*keys: str, default: str = "") -> str:
        for key in keys:
            value = decision_dict.get(key)
            if value not in (None, ""):
                return value
        return default

    severity = _pick("severity", "unknown_risk_severity", default="LOW")
    decision = _pick("decision", "unknown_risk_decision", default="WARN")
    reason_code = _pick("reason_code", "unknown_risk_reason_code")

    # Reason codes are shaped like UNKNOWN_RISK_HIGH — the trailing token is the
    # severity, and it is more reliable than an absent severity field.
    if reason_code and severity == "LOW":
        tail = str(reason_code).rsplit("_", 1)[-1].upper()
        if tail in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            severity = tail
    
    # Extract structural flags from the internal audit map layer if present
    audit_entry = decision_dict.get("audit_entry", {})
    ai_status = audit_entry.get("ai_status", reason_code.split("_")[0] if reason_code else "UNKNOWN")
    ai_confidence = audit_entry.get("ai_confidence", 1.0)

    # ── 2. Structural Confidence Gate ──
    # If confidence is below or equal to 15% (0.15), force a confident, clean safety reassurance
    if ai_confidence <= 0.15 or ai_status == "NORMAL":
        return f"This transaction is completely safe, and you may proceed normally. {_DEFAULT_COMPLIANCE_TEXT}"

    # ── 3. Build Post-Scrubbed Prompt for the Local LLM ──
    prompt = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        "You are an encouraging, clear-spoken bank customer service assistant for Punjab & Sind Bank.\n"
        "Your task is to write a warm statement explaining a routine security status update to the account holder.\n\n"
        "CRITICAL TEXT CONSTRAINTS:\n"
        "1. Output EXACTLY 1 to 2 clear sentences total. Get straight to the point without greetings or intros.\n"
        "2. Use simple, everyday plain English. Do NOT explain backend rules or system mechanics.\n"
        "3. ABSOLUTELY FORBIDDEN terms: dataclass, handler, override, severity, status, reason_code, advanced, security systems, monitoring, precautionary, surveillance, algorithms, intelligence, anomaly.\n"
        "4. End your statement exactly with this closing string: '" + _DEFAULT_COMPLIANCE_TEXT + "'\n\n"
        "DYNAMIC EXPLANATION MATRIX:\n"
        "- When Access is WARN: State simply that we noticed a minor variance from your regular habits, but the payment processed smoothly.\n"
        "- When Access is CHALLENGE: State that an extra step is required on screen to confirm identity due to unfamiliar payment details layout.\n"
        "- When Access is BLOCK: State clearly that the transfer was paused because it closely matched an irregular, unrecognized pattern.\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        "Translate this system status event into clear customer narrative sentences:\n"
        f"- Access Path: {decision}\n"
        f"- Pattern Context: {ai_status}\n"
        f"- Priority Assessment: {severity}\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )

    # ── 4. Execute LLM Query Sequence ──
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "keep_alive": llm_source.KEEP_ALIVE,
                "options": {
                    "temperature": 0.0,  # Max stability
                    "top_p": 0.9
                }
            },
            timeout=llm_source.GENERATE_TIMEOUT
        )
        
        if response.status_code == 200:
            raw_text = llm_source.tidy(response.json().get("response", ""))
            
            # Post-generation regex cleanups
            clean_text = re.sub(
                r"^(here is the explanation|explanation|summary|statement)[:\s\n]*", 
                "", raw_text, flags=re.IGNORECASE
            ).strip()
            
            # Reuse the decision-consistency guardrail: an explanation must
            # never claim a held or blocked payment succeeded.
            from ai.engines.decision_explanability import _contradicts_decision

            if (
                clean_text
                and _is_valid_text(clean_text)
                and not _contradicts_decision(clean_text, decision)
            ):
                llm_source.mark(llm_source.LLM)
                if _DEFAULT_COMPLIANCE_TEXT.lower() not in clean_text.lower():
                    clean_text = clean_text.rstrip(".") + f". {_DEFAULT_COMPLIANCE_TEXT}"
                return clean_text

    except requests.exceptions.RequestException:
        logger.warning("Local Ollama framework unreachable. Triggering backup matrix.")

    # ── 5. Offline Fallback Logic ──
    fallback_maps = {
        "WARN": "We noticed a minor variance from your normal spending habits, but your transaction processed safely.",
        "CHALLENGE": "Please complete the brief identity verification step on your screen to proceed.",
        "BLOCK": "For your protection, this transaction was paused because it did not match your normal account signature."
    }
    base_msg = fallback_maps.get(decision, "Transaction safety screening complete.")
    llm_source.mark(llm_source.FALLBACK)
    return f"{base_msg} {_DEFAULT_COMPLIANCE_TEXT}"


def _is_valid_text(text: str) -> bool:
    """Scans generated output to prevent technical jargon leakages."""
    if len(text) < 20 or len(text) > 600:
        return False
    text_lower = text.replace('"', '').replace("'", "").lower()
    for term in _BANNED_TERMS:
        if " " in term:
            if term in text_lower:
                return False
        else:
            if re.search(rf"\b{re.escape(term)}\b", text_lower):
                return False
    return True