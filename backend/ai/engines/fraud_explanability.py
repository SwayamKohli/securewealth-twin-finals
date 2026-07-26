import json
import requests
from dataclasses import asdict
from security.risk_engine import RiskEvaluationOutput

def generate_risk_breakdown(output: RiskEvaluationOutput, ollama_url: str = "http://localhost:11434") -> str:
    """
    Takes a RiskEvaluationOutput and passes its sub-scores and weights to Ollama
    to generate an easy-to-understand breakdown of what factors influenced the risk score.
    """
    out_dict = asdict(output)
    signals = out_dict.get("security_signals", {})
    sub_scores = signals.get("sub_scores", {})
    env = signals.get("environment", {})
    dev = signals.get("device", {})

    # Extract clean human context from the sub-scores
    active_behaviors = ", ".join(signals.get("active_behavior", [])) or "None (Normal transaction timing/patterns)"
    network_profile = env.get("network_type", "Unknown Network")
    location_changed = "Yes (Sudden shift from last known area)" if env.get("region_changed") else "No"
    device_profile = f"{dev.get('device_status', 'Unknown')} (Confidence: {dev.get('device_confidence', 0)}%)"

    # Formulate a structured, simple prompt optimized for Llama 3
    # Formulate the updated prompt ensuring data labels explicitly state 'Risk'
    prompt = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        "You are a helpful, reassuring bank customer support advisor. "
        "Your job is to explain a security risk assessment breakdown to a customer in plain English.\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT mention developer jargon like 'sub_scores', 'dataclass', 'dictionary', 'float', 'weights', 'AI', or 'API'.\n"
        "1.1. Crucial: The values provided represent a RISK score, NOT a safety score. Lower values indicate lower risks and higher values indicate higher risks. Never refer to these scores as safety scores.\n"
        "2. Do not show raw formulas or mention mathematical multiplication. Explain it contextually.\n"
        "3. Focus on the main contributors. If the total risk score is under 30, reassure them everything looks perfect.\n"
        "3.1. If it is high, gently highlight what triggered our systems (e.g., location changes or unrecognized networks).\n"
        "3.2. The reason should be clear cut; do not blackbox the reason.\n"
        "4. Limit the output to 3 sentences maximum. Keep it clear, friendly, and non-technical.\n"
        "5. Do not greet, be courteous, or provide meta-text. Start directly with the explanation.\n"
        "6. If the overall risk score is under 5, ignore long summaries and just return a positive, ultra-short reassurance phrase.\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        "Please provide a quick summary for the customer based on these security metrics:\n"
        f"- Overall Account Risk Score: {out_dict.get('risk_score')} out of 100\n" # Fixed label
        f"- Device Risk Context: {device_profile} (Internal rating: {sub_scores.get('device', 0)})\n"
        f"- Connection Environment Risk: Network is {network_profile}, Unexpected Location Switch: {location_changed} (Internal rating: {sub_scores.get('environmental', 0)})\n"
        f"- Behavioral Timing/Activity Risk: {active_behaviors} (Internal rating: {sub_scores.get('behavioral', 0)})\n"
        f"- Automated Pattern Matching Anomaly Risk: (Internal rating: {sub_scores.get('ai_fraud', 0)})\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9
                }
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        return "Your transaction profile has been evaluated smoothly by our security network."
    except requests.exceptions.RequestException:
        # Simple non-technical fallback text
        score = out_dict.get("risk_score", 0)
        if score > 50:
            return "Our system noticed some unusual changes in your current login location and network connection, so we are reviewing this activity to keep your funds safe."
        return "Everything looks great! Your transaction details perfectly match your normal daily spending patterns."