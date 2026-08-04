import json
import requests
import re
from typing import Dict, Any
from ai.engines.phishing_engine import ScanResult
from ai.engines.llm_source import tidy as _tidy

# --- Deterministic Fallback Data ---
GROUP_REASONING: Dict[str, str] = {
    "psychological": "uses manipulative language to create urgency or panic",
    "authority": "impersonates a trusted organization or bank",
    "credential": "requests highly sensitive login or financial details",
    "greed": "offers an unlikely reward, lottery, or cashback",
    "transaction": "claims an issue with a payment, transfer, or EMI",
    "technical": "contains suspicious links, fake apps, or masked numbers",
    "upi_digital": "exploits digital payment interfaces",
    "social_engineering": "uses tricks to gain blind compliance",
    "refund_overpayment": "uses fake refunds to trick you into sending money",
    "threat_escalation": "threatens legal action or account blocking",
    "seasonal": "exploits current events like tax season"
}

# Immutable, unified backup copy for structural validation failures
_DEFAULT_SCAM_INSTRUCTION = "Do not click any links or share private banking passwords. Delete this message immediately."


# --- 1. Local LLM Generator (Ollama) ---
def generate_llm_explanation(result: ScanResult, model_name: str = "llama3:latest", timeout: float = 45.0) -> str:
    """
    Queries local Ollama framework instance using native JSON structure constraints.
    """
    prompt_context = f"""
    Risk Level: {result.risk_level}
    Top Signal: {result.top_signal}
    Methods Used: {', '.join(result.signal_groups_fired)}
    Keywords Found: {json.dumps(result.detected_keywords)}
    """

    system_prompt = """
    You are an objective, expert banking security analysis assistant.
    Explain communication payload vulnerabilities to non-technical everyday banking users.

    CRITICAL STRUCTURE RULES:
    1. Output a description in plain, simple English. Do NOT use technical jargon.
    2. If the transaction or alert is clean/safe, output exactly: "This is a legitimate bank alert. No action is needed."
    3. If a scam, explicitly detail what the attacker wants (e.g., 'They want your money' or 'They want your PIN').
    4. Highlight the sender's tone style choice (e.g., 'The sender is acting like a bully to scare you').
    5. You MUST end the string exactly with a defensive directive step (e.g., 'Do not click the link' or 'Delete this immediately').
    6. Keep the total explanation copy under 50 words total.
    7. Return ONLY valid JSON matching this exact schema block structure: {"explanation": "your text here"}
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model_name,
            "prompt": prompt_context,
            "system": system_prompt,
            "stream": False,
        "keep_alive": "30m",
            "format": "json"  # Enforces structural JSON constraints at the engine layer
        },
        timeout=timeout 
    )
    
    response.raise_for_status()
    data = response.json()
    
    raw_response = data.get("response", "{}").strip()
    
    # Non-destructive strip out of stray markdown ticks if leaked by the compiler
    clean_json = raw_response.replace("```json", "").replace("```", "").strip()
    
    try:
        parsed_response = json.loads(clean_json)
        
        # DEFENSIVE PAYLOAD RECOVERY: If JSON is valid but key name shifted
        if "explanation" in parsed_response:
            explanation_text = _tidy(parsed_response["explanation"])
        else:
            # Dynamically pull the first string element available in the dictionary keys
            string_values = [str(v) for v in parsed_response.values() if isinstance(v, str)]
            explanation_text = _tidy(string_values[0]) if string_values else ""
            
        # If the extracted string is invalid or completely empty, throw to activate fallback pathing
        if not explanation_text or len(explanation_text) < 15:
            raise ValueError("Extracted narrative block fails standard length minimum checks.")
            
        return explanation_text

    except (json.JSONDecodeError, KeyError, IndexError, ValueError):
        # Gracefully raise to let the orchestrator divert cleanly into fallback engines
        raise RuntimeError("LLM output data model configuration format verification failed.")


# --- 2. Deterministic Fallback Engine ---
def generate_fallback_explanation(result: ScanResult) -> str:
    if str(result.risk_level).upper() == "SAFE":
        return "This is a legitimate bank alert. No action is needed."
    
    parts = [f"This message has been flagged as a {result.risk_level} risk communication profile."]
    
    explanations = [GROUP_REASONING[g] for g in result.signal_groups_fired if g in GROUP_REASONING]
    if explanations:
        parts.append("It matches patterns that " + " and ".join(explanations) + ".")
    
    parts.append(_DEFAULT_SCAM_INSTRUCTION)
    return " ".join(parts)


# --- 3. Main Orchestrator ---
def get_phishing_explanation(result: ScanResult) -> dict:
    try:
        explanation = generate_llm_explanation(result)
        source = "LLM"
    except Exception as e:
        # Programmatic protection fallback loop triggered safely without breaking response dictionary layouts
        explanation = generate_fallback_explanation(result)
        source = "RULES_FALLBACK"
    
    return {
        "explanation": explanation, 
        "source": source,
        "risk_level": result.risk_level,
        "score": result.phishing_score
    }