from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────────

_TEMPLATES_PATH = Path(__file__).parent / "templates" / "device_templates.json"
_OLLAMA_URL     = "http://localhost:11434/api/generate"
_DEFAULT_MODEL  = "llama3:latest"
_TIMEOUT_SECS   = 10
_MAX_LLM_OUTPUT = 600

# Strict security blacklist — engineering jargon or legally complex terms
_BANNED_TERMS = frozenset([
    "fingerprint", "hash", "sha256", "repository", "dataclass", "uuid", 
    "payload", "emulator", "rooted", "automation", "spoofed", "fraud",
    "zero-day", "banned", "blacklist", "hardware-constant", "co-variance"
])

_MANDATORY_DISCLAIMER = "This update is part of our standard digital security verification."


# ─── Explainer ────────────────────────────────────────────────────────────────

class DeviceTrustExplainer:
    """
    Converts DeviceTrustService dictionary payloads into personalized,
    plain-language security notifications for Punjab & Sind Bank interfaces.
    """

    def __init__(
        self,
        model:    str = _DEFAULT_MODEL,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model     = _DEFAULT_MODEL if model in ("llama3", "llama3:latest") else model
        self._api_url   = base_url.rstrip("/") + "/api/generate"
        self._templates = self._load_fallback_templates()
        self._llm_ok: bool = self._llm_available()

    # ── Public API ──────────────────────────────────────────────────────────────

    def explain(self, trust_result: dict[str, Any], user_profile: dict[str, Any]) -> dict[str, Any]:
        """
        Generate plain-language text explanations for current login device states.
        """
        status      = trust_result.get("device_status", "NEW_DEVICE")
        age_days    = trust_result.get("device_age_days", 0)
        confidence  = trust_result.get("device_confidence", 0)
        signals     = trust_result.get("security_signals", [])
        
        name = user_profile.get("name", "Customer")

        output_payload = {
            "device_status":     status,
            "device_confidence": confidence,
            "security_signals":  list(signals),
            "customer_message":  "",
            "generated_by":      "template"
        }

        if self._llm_ok:
            prompt = self._build_device_prompt(status, age_days, confidence, signals, name)
            raw_response = self._call_llm(prompt)
            
            if raw_response and self._is_valid(raw_response):
                clean_text = raw_response[:_MAX_LLM_OUTPUT].strip()
                
                # CRITICAL POST-PROCESSING: Strip out standard introductory phrases
                clean_text = re.sub(r"^(here is the security update statement|security update statement|here is the statement|translation)[:\s]*", "", clean_text, flags=re.IGNORECASE)
                clean_text = clean_text.strip()
                
                # Post-generation disclaimer verification
                if _MANDATORY_DISCLAIMER.lower() not in clean_text.lower():
                    clean_text = clean_text.rstrip(".") + f". {_MANDATORY_DISCLAIMER}"
                
                output_payload["customer_message"] = clean_text
                output_payload["generated_by"]     = "llm"
                return output_payload

        output_payload["customer_message"] = self._get_fallback_message(status, name)
        return output_payload

    # ── Internal Core Helpers ────────────────────────────────────────────────────

    def _llm_available(self) -> bool:
        try:
            req = urllib.request.Request(
                self._api_url.replace("/api/generate", "/api/tags"),
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _call_llm(self, prompt: str) -> str | None:
        payload = json.dumps({
            "model":  self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  
                "top_p": 0.9
            }
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                self._api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception:
            return None

    def _build_device_prompt(self, status: str, age: int, conf: int, signals: list[str], name: str) -> str:
        """Construct the system instruction payload without technical metadata variable names."""
        
        # Soften descriptions based on status before feeding to the LLM context
        if status == "NEW_DEVICE":
            context_description = "The customer is logging into their account using a freshly registered device for the first time."
        elif status == "INACTIVE_DEVICE":
            context_description = f"The customer is returning to their mobile banking app after being away for {age} days."
        elif status == "SUSPICIOUS_DEVICE":
            context_description = "The login attempt exhibits unrecognized profile patterns requiring simple identity verification."
        else:
            context_description = f"The customer is connecting from their verified, recognized everyday profile with a record of {age} days."

        return (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are a reassuring, professional digital security advisor for Punjab & Sind Bank.\n"
            f"Your task is to write a helpful notification message informing the customer about their current login attempt.\n\n"
            f"CRITICAL PROSE INSTRUCTIONS:\n"
            f"1. Output EXACTLY 2 clear, comforting sentences. Do not greet, introduce your response, or include sign-offs.\n"
            f"2. Talk naturally using everyday language. Do NOT use technical terms or refer to trust metrics.\n"
            f"3. ABSOLUTELY FORBIDDEN terms: fingerprint, hash, sha256, payload, automated, emulator, rooted, malicious, zero-day, mismatch, risk score, database, uncertainty, configuration.\n"
            f"4. Never accuse the user of fraudulent behavior. Frame any variance as a standard verification point.\n"
            f"5. Start directly with the sentence content. Never output introductory filler like 'Here is the statement:'.\n"
            f"6. End the statement exactly with this compliance message: '{_MANDATORY_DISCLAIMER}'\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Generate a security update statement for this profile:\n"
            f"- Customer Name: {name}\n"
            f"- Situation: {context_description}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )

    def _is_valid(self, text: str) -> bool:
        if not text or len(text.strip()) < 25 or len(text) > _MAX_LLM_OUTPUT:
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

    def _get_fallback_message(self, status: str, name: str) -> str:
        fallbacks = {
            "TRUSTED_DEVICE": f"Welcome back, {name}. Your access profile is fully recognized and confirmed.",
            "KNOWN_DEVICE": f"Hello {name}. Your current device is verified for account access activity.",
            "NEW_DEVICE": f"We noticed you are logging in from a newly registered device profile, {name}.",
            "INACTIVE_DEVICE": f"Welcome back, {name}. We are re-confirming this connection profile since it has been some time since your last visit.",
            "SUSPICIOUS_DEVICE": "We detected an unverified device profile pattern variation during this access attempt.",
            "ZERO_DAY_DEVICE": "This login attempt is operating via an unconfirmed or unexpected system profile configuration."
        }
        base_message = fallbacks.get(status, f"Account login activity update processing for {name}.")
        return f"{base_message} {_MANDATORY_DISCLAIMER}"

    @staticmethod
    def _load_fallback_templates() -> dict:
        try:
            with open(_TEMPLATES_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}