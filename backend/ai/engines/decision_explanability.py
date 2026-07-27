import json
import logging
import re
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Banned technical or legally complex engineering jargon
_BANNED_TERMS = frozenset([
    "array", "dataclass", "stricter outcome", "handler", "signals", "vpn", 
    "zero-day", "unknown risk", "override", "reason code", "system action",
    "channel", "flagged", "discrepancies", "backend", "anomaly", "metric", "signature"
])

_DEFAULT_COMPLIANCE_TEXT = "This check is part of our routine digital asset protection measures."


def _humanize_string(token: str) -> str:
    """Converts raw SNAKE_CASE variables into soft lowercase natural language phrases."""
    if not token or token.lower() == "none":
        return ""
    # Replace underscores with spaces, drop to lower, and clean trailing spaces
    phrase = token.replace("_", " ").lower().strip()
    # Apply soft contextual swaps for raw technical terms
    phrase = phrase.replace("signature", "pattern")
    phrase = phrase.replace("metric", "indicator")
    return phrase


def generate_customer_explanation(record: Any, ollama_url: str = "http://localhost:11434") -> str:
    """
    Translates technical DecisionRecords into warm, plain-language customer summaries
    using strict programmatic inputs from decision, reason_code, security_signals, and challenge_type.
    """
    # ── 1. Secure Attribute Extraction & Conversion ──
    decision = getattr(record, "decision", "ALLOW")
    reason_code = _humanize_string(getattr(record, "reason_code", "NORMAL_ACCESS"))
    challenge_type = _humanize_string(getattr(record, "challenge_type", "None"))
    
    # Clean up security signals arrays into natural text variations before the LLM sees them
    raw_signals = []
    if hasattr(record, "security_signals") and isinstance(record.security_signals, dict):
        raw_signals = record.security_signals.get("active_behavior", [])
    
    cleaned_signals = [_humanize_string(s) for s in raw_signals if s]
    signals_str = ", ".join(cleaned_signals) if cleaned_signals else "none"

    # ── 2. Structural Prompt Preparation ──
    prompt = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        "You are an encouraging, clear-spoken customer wellness service assistant for Punjab & Sind Bank.\n"
        "Your task is to write a warm, motivating update message regarding a user's transaction status access.\n\n"
        "CRITICAL TEXT INSTRUCTIONS:\n"
        "1. Output EXACTLY 2 sentences total. Do not include greetings, introductions, filler, or sign-offs.\n"
        "2. Use simple, conversational plain English. The user is an everyday banking customer.\n"
        "3. Do NOT use technical terminology or repeat system code flags, tokens, or system metrics.\n"
        "4. ABSOLUTELY FORBIDDEN terms: array, dataclass, stricter outcome, handler, signals, vpn, zero-day, unknown risk, override, anomaly, discrepancies, channel, signature, metric, translation.\n"
        "5. Frame any checkpoint or security block calmly as a protective measure to keep their account balance safe.\n"
        "6. Start directly with the sentence content. Never output introductory phrases like 'Here is the translation:'.\n"
        "7. End the statement exactly with this closing string: '" + _DEFAULT_COMPLIANCE_TEXT + "'\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        "Translate this situation update into clear customer narrative sentences:\n"
        f"- Account Access Status: {decision}\n"
        f"- Activity Category: {reason_code}\n"
        f"- Context Details: {signals_str}\n"
        f"- Next Steps Required: {challenge_type or 'none'}\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )

    # ── 3. Local LLM Generation Request Execution ──
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  
                    "top_p": 0.9
                }
            },
            timeout=8
        )
        
        if response.status_code == 200:
            raw_text = response.json().get("response", "").strip()
            
            # HARDENED REGEX INTERCEPT: Strip conversational introductions completely
            clean_text = re.sub(
                r"^(here is the translation|here is the explanation|translation|explanation|summary)[:\s\n]*", 
                "", raw_text, flags=re.IGNORECASE
            ).strip()
            
            # Perform Guardrail checks on the string content
            if clean_text and _is_valid_narrative(clean_text):
                if _DEFAULT_COMPLIANCE_TEXT.lower() not in clean_text.lower():
                    clean_text = clean_text.rstrip(".") + f". {_DEFAULT_COMPLIANCE_TEXT}"
                return clean_text

    except requests.exceptions.RequestException:
        logger.warning("Local Ollama endpoint unreachable. Diverting to offline layout maps.")

    # ── 4. Deterministic Offline Fallback Strategy Maps ──
    fallback_maps = {
        "ALLOW": "Everything processed cleanly as our system successfully recognized your normal account transaction patterns.",
        "WARN": "We successfully processed your transaction, but noted a small variance from your standard profile traits.",
        "CHALLENGE": f"To ensure absolute account protection, please complete the quick security confirmation step using your required {challenge_type or 'verification'} prompt.",
        "BLOCK": "We have safely paused this transaction activity to defend your funds against highly unusual or unrecognized access patterns."
    }
    
    base_fallback = fallback_maps.get(decision, "We are verifying this transaction sequence for account protection safety.")
    return f"{base_fallback} {_DEFAULT_COMPLIANCE_TEXT}"


def _is_valid_narrative(text: str) -> bool:
    """Enforces strict checks against engineering term leakages post-generation."""
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