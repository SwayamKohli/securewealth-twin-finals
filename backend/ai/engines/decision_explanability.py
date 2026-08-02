import json
import logging
import re
import requests
from typing import Dict, Any
from ai.engines import llm_source

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
    #
    # This engine was written against a DecisionRecord OBJECT, but the API hands
    # it a plain dict parsed from JSON — and getattr() does not read dict keys.
    # Every field therefore fell through to its default, so a CHALLENGE was
    # explained to the customer as an ALLOW ("your access has been successfully
    # granted"). Normalise first, then read.
    def _read(key: str, default: str) -> str:
        if isinstance(record, dict):
            value = record.get(key, default)
        else:
            value = getattr(record, key, default)
        return default if value in (None, "") else value

    decision = str(_read("decision", "ALLOW")).upper()
    reason_code = _humanize_string(_read("reason_code", "NORMAL_ACCESS"))
    challenge_type = _humanize_string(_read("challenge_type", "None"))
    
    # Clean up security signals arrays into natural text variations before the LLM sees them
    raw_signals = []
    _signals = (
        record.get("security_signals")
        if isinstance(record, dict)
        else getattr(record, "security_signals", None)
    )
    if isinstance(_signals, dict):
        raw_signals = _signals.get("active_behavior", [])
    
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
                "keep_alive": llm_source.KEEP_ALIVE,
                "options": {
                    "temperature": 0.0,  
                    "top_p": 0.9
                }
            },
            timeout=llm_source.GENERATE_TIMEOUT
        )
        
        if response.status_code == 200:
            raw_text = llm_source.tidy(response.json().get("response", ""))
            
            # HARDENED REGEX INTERCEPT: Strip conversational introductions completely
            clean_text = re.sub(
                r"^(here is the translation|here is the explanation|translation|explanation|summary)[:\s\n]*", 
                "", raw_text, flags=re.IGNORECASE
            ).strip()
            
            # Perform Guardrail checks on the string content
            if (
                clean_text
                and _is_valid_narrative(clean_text)
                and not _contradicts_decision(clean_text, decision)
            ):
                llm_source.mark(llm_source.LLM)
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
    llm_source.mark(llm_source.FALLBACK)
    return f"{base_fallback} {_DEFAULT_COMPLIANCE_TEXT}"


# ── Decision-consistency guardrail ───────────────────────────────────────────
# The jargon filter above catches HOW the model writes. This catches WHAT it
# says — specifically, an explanation that contradicts the decision it is
# supposed to be explaining.
#
# Observed in testing: for a CHALLENGE the model produced "Your account access
# has been successfully granted... as usual", and for an unknown-risk CHALLENGE
# it produced "the payment processed smoothly without any issues". Both are the
# opposite of the truth — the money is on hold pending verification. Shipping
# that to a customer is worse than shipping a plain template, because it tells
# them to stop paying attention at the exact moment they should not.
#
# Rule: when the decision withholds or pauses money, the narrative must not
# claim completion or success.
_COMPLETION_CLAIMS = (
    "successfully granted",
    "successfully completed",
    "successfully processed",
    "processed smoothly",
    "processed successfully",
    "went through",
    "has been completed",
    "was completed",
    "no issues",
    "without any issues",
    "as usual",
    "nothing to worry",
    "no action is needed",
    "no action needed",
)

# Decisions where money has NOT moved / is not final.
_WITHHOLDING_DECISIONS = frozenset({"CHALLENGE", "BLOCK"})


def _contradicts_decision(text: str, decision: str) -> bool:
    """True when the narrative claims success for a paused or blocked action."""
    if str(decision).upper() not in _WITHHOLDING_DECISIONS:
        return False
    low = text.lower()
    return any(claim in low for claim in _COMPLETION_CLAIMS)


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