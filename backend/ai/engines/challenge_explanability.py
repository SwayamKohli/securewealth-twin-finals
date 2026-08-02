import json
import logging
import re
import requests
from typing import Any, Dict
from dataclasses import asdict
from ai.engines import llm_source

logger = logging.getLogger(__name__)

# Jargon and UI mechanics blacklist — forces frontend independence
_BANNED_TERMS = frozenset([
    "challenge_type", "dataclass", "trigger_signal", "boolean", "flag", "code",
    "anomaly", "distress", "spike", "override", "click", "button", "tap", "sms",
    "text", "popup", "screen", "window", "link", "submit", "press", "ui", "frontend"
])

_DEFAULT_COMPLIANCE_TEXT = "This temporary verification helps ensure your funds remain completely protected."


def _humanize_context(token: str) -> str:
    """Converts technical system enums into soft, natural language concepts."""
    if not token or token.lower() == "none":
        return ""
    # Strip layout indicators, drop casing, remove underscores
    phrase = token.replace("_", " ").lower().strip()
    # Mask UI-specific mechanics into general security actions
    phrase = phrase.replace("otp reconfirmation", "identity validation update")
    phrase = phrase.replace("device confirmation", "connection verification check")
    phrase = phrase.replace("risk warning acceptance", "safety advisory review")
    return phrase


def generate_challenge_instruction(requirement: Any, ollama_url: str = "http://localhost:11434") -> str:
    """
    Takes a ChallengeRequirement and instructs the customer on the security intent
    of the verification check completely decoupled from any frontend UI components.
    """
    # ── 1. Safe Parameter Structuring ──
    if hasattr(requirement, "to_dict"):
        req_dict = requirement.to_dict()
    elif hasattr(requirement, "__dataclass_fields__"):
        req_dict = asdict(requirement)
    else:
        req_dict = dict(requirement)

    # Clean exit gate if no security validation action is triggered
    if not req_dict.get("challenge_required", True):
        return f"No further actions are required. Your request has processed successfully. {_DEFAULT_COMPLIANCE_TEXT}"

    # Extract strings and pre-clean them to prevent technical variable leakages
    challenge_type = _humanize_context(req_dict.get("challenge_type", "verification checkpoint"))
    trigger_signal = _humanize_context(req_dict.get("trigger_signal", "profile variance"))

    # ── 2. Structural Frontend-Agnostic Prompt ──
    prompt = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        "You are an encouraging, professional digital safety assistant for Punjab & Sind Bank.\n"
        "Your task is to write a brief security notice informing the user about an ongoing safety check.\n\n"
        "CRITICAL FRONTEND-AGNOSTIC RULES:\n"
        "1. Output EXACTLY 2 clear sentences total. Do not include greetings, introductions, or closing remarks.\n"
        "2. Talk naturally using everyday plain English. Focus on the safety intent of verifying identity.\n"
        "3. ABSOLUTELY FORBIDDEN to mention UI actions or frontend mechanics (e.g., click, tap, press, button, link, popup, screen, text, SMS, OTP).\n"
        "4. ABSOLUTELY FORBIDDEN terms: challenge_type, trigger_signal, anomaly, override, spike, flag, code, dataclass.\n"
        "5. Frame the prompt cleanly as a routine validation check to shield their balance from unrecognized access changes.\n"
        "6. Start directly with the sentence content. Never output phrases like 'Here is the instructions:'.\n"
        "7. End the statement exactly with this compliance string: '" + _DEFAULT_COMPLIANCE_TEXT + "'\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        "Translate this security validation context into natural customer sentences:\n"
        f"- Reason for verification check: A minor {trigger_signal} was processed.\n"
        f"- Operational safety goal: Complete the active {challenge_type}.\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )

    # ── 3. Execute Deterministic Query Sequence ──
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "keep_alive": llm_source.KEEP_ALIVE,
                "options": {
                    "temperature": 0.0,  # Forces maximum repeatability
                    "top_p": 0.9
                }
            },
            timeout=llm_source.GENERATE_TIMEOUT
        )
        
        if response.status_code == 200:
            raw_text = llm_source.tidy(response.json().get("response", ""))
            
            # Scrub out potential conversational meta-introductions
            clean_text = re.sub(
                r"^(here is the text|here is the instruction|instruction|summary|translation)[:\s\n]*", 
                "", raw_text, flags=re.IGNORECASE
            ).strip()
            
            if clean_text and _is_valid_instruction(clean_text):
                llm_source.mark(llm_source.LLM)
                if _DEFAULT_COMPLIANCE_TEXT.lower() not in clean_text.lower():
                    clean_text = clean_text.rstrip(".") + f". {_DEFAULT_COMPLIANCE_TEXT}"
                return clean_text

    except requests.exceptions.RequestException:
        logger.warning("Local Ollama daemon unreachable. Reverting to decoupled offline fallbacks.")

    # ── 4. UI-Independent Backup Fallback Matrix ──
    fallback_maps = {
        "connection verification check": "We noticed an access update involving an unrecognized device signature connection profile. Please finalize the active security verification step to confirm your identity.",
        "identity validation update": "To ensure your transaction session remains fully protected, a brief confirmation check has been initialized. Please complete the security validation step assigned to your profile.",
        "transaction confirmation": "This transaction amount reflects a minor change from your everyday account volume parameters. Please re-confirm the transfer details to safely validate this request.",
        "safety advisory review": "This transaction sequence is occurring during atypical operational hours. Please review and acknowledge our digital account security advisory to proceed safely."
    }
    
    base_msg = fallback_maps.get(challenge_type, "To preserve account protection integrity, an access validation checkpoint is processing. Please finalize the identity verification step to proceed.")
    llm_source.mark(llm_source.FALLBACK)
    return f"{base_msg} {_DEFAULT_COMPLIANCE_TEXT}"


def _is_valid_instruction(text: str) -> bool:
    """Ensures generated strings are free from technical terms and UI interface jargon."""
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