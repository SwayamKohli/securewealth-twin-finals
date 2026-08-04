from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────────

_TEMPLATES_PATH = Path(__file__).parent / "templates" / "fallback_templates.json"

# Ollama HTTP endpoint — standard default port
_OLLAMA_URL     = "http://localhost:11434/api/generate"

# ENFORCED PROMPT CONSTRAINT: Tag name strictly targeting the latest distribution tag
_DEFAULT_MODEL  = "llama3:latest"

# HTTP timeout — keep short so a slow/absent LLM doesn't block the API response
_TIMEOUT_SECS   = 45   # cold model load can take 15-40s; see llm_source

# Maximum characters accepted from LLM before we reject as hallucination
_MAX_LLM_OUTPUT = 600

# Technical terms / phrases that must never appear in customer-facing output.
_BANNED_TERMS = frozenset([
    "z-score", "shap", "autoencoder", "xgboost", "reconstruction error",
    "sigmoid", "probability distribution", "feature importance",
    "guaranteed return", "will definitely", "risk-free",
    "you should buy", "100% safe", "buy shares", "stock pick",
    "mutual fund name", "nav value", "fund aum",
    "advanced", "security systems", "monitoring", "precautionary",
    "surveillance", "algorithms", "intelligence", "anomaly", "override", 
    "dataclass", "handler", "backend"
])


# ─── Explainer ────────────────────────────────────────────────────────────────

class RecommendationExplainer:
    """
    Converts WealthIntelligenceEngine output into personalized natural-language.

    Usage
    -----
    explainer = RecommendationExplainer(model="llama3:latest")
    result = explainer.explain(wealth_result, profile)
    """

    def __init__(
        self,
        model:    str = _DEFAULT_MODEL,
        base_url: str = "http://localhost:11434",
    ) -> None:
        # Enforce llama3:latest strictly if defaults or baseline tags are requested
        self._model     = _DEFAULT_MODEL if model in ("llama3", "llama3:latest") else model
        self._api_url   = base_url.rstrip("/") + "/api/generate"
        self._templates = self._load_templates()
        self._llm_ok: bool = self._llm_available()

    # ── Public API ──────────────────────────────────────────────────────────────

    def explain(self, wealth_result: dict, profile: dict) -> dict:
        """
        Generate natural-language explanations for wealth recommendations.
        """
        suppressed    = wealth_result.get("suppressed", False)
        health        = wealth_result.get("financial_health", {})
        recs          = wealth_result.get("recommendations", [])
        goal_summaries = wealth_result.get("goal_summaries", [])
        disclaimer    = wealth_result.get("disclaimer", self._templates.get("disclaimer", ""))

        # ── Suppressed path ──────────────────────────────────────────────────
        if suppressed:
            reason      = wealth_result.get("suppress_reason", "")
            overview    = self._suppressed_overview(reason, profile)
            health_summ = self._health_summary(health)
            
            # EXTRACT FALLBACK RECOMMENDATIONS: Retain structural metrics like expense optimization
            explained = []
            for rec in recs:
                explained.append({
                    "recommendation_id": rec.get("recommendation_id", ""),
                    "recommendation":    rec.get("recommendation", ""),
                    "product":           rec.get("product", ""),
                    "amount":            rec.get("amount", 0),
                    "tenure":            rec.get("tenure", ""),
                    "explanation":       rec.get("reason", ""),
                    "expected_benefit":  rec.get("expected_benefit", ""),
                    "priority":          rec.get("priority", ""),
                })
                
            return {
                "suppressed":                 True,
                "suppress_reason":            reason,
                "overview":                   overview,
                "health_summary":             health_summ,
                "recommendation_explanations": explained,
                "goal_summaries":             goal_summaries,
                "disclaimer":                 disclaimer,
                "generated_by":              "template",
                "financial_health":           health,
            }

        # ── Normal path ──────────────────────────────────────────────────────
        llm_ok   = self._llm_ok
        used_llm = False

        # Overview paragraph — try LLM first, fallback on failure
        overview = self._generate_overview(wealth_result, profile, llm_ok)
        if overview.get("source") == "llm":
            used_llm = True
        overview_text = overview["text"]

        # Per-recommendation explanations
        explained = []
        for rec in recs:
            entry = self._explain_recommendation(rec, profile, llm_ok)
            if entry.get("source") == "llm":
                used_llm = True
            
            # SAFE NON-DESTRUCTIVE APPEND: Avoids mutating source memory matrices
            explained.append({
                "recommendation_id": rec.get("recommendation_id", ""),
                "recommendation":    rec.get("recommendation", ""),
                "product":           rec.get("product", ""),
                "amount":            rec.get("amount", 0),
                "tenure":            rec.get("tenure", ""),
                "explanation":       entry["text"],
                "expected_benefit":  rec.get("expected_benefit", ""),
                "priority":          rec.get("priority", ""),
            })

        health_summ  = self._health_summary(health)
        generated_by = "llm" if used_llm else "template"

        return {
            "suppressed":                 False,
            "overview":                   overview_text,
            "health_summary":             health_summ,
            "recommendation_explanations": explained,
            "goal_summaries":             goal_summaries,
            "disclaimer":                 disclaimer,
            "generated_by":              generated_by,
            "financial_health":           health,
        }

    # ── LLM interaction ─────────────────────────────────────────────────────────

    def _llm_available(self) -> bool:
        """Probe Ollama health endpoint."""
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
        """Call Ollama /api/generate with stream=false."""
        payload = json.dumps({
            "model":  self._model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.1,
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
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
            logger.warning("Ollama call failed: %s", exc)
            return None

    # ── Generation helpers ──────────────────────────────────────────────────────

    def _generate_overview(
        self, wealth_result: dict, profile: dict, llm_ok: bool
    ) -> dict:
        """Build the opening paragraph."""
        if llm_ok:
            prompt = self._build_overview_prompt(wealth_result, profile)
            raw    = self._call_llm(prompt)
            if raw and self._is_valid(raw):
                return {"text": raw[:_MAX_LLM_OUTPUT], "source": "llm"}

        return {"text": self._template_overview(wealth_result, profile), "source": "template"}

    def _explain_recommendation(
        self, rec: dict, profile: dict, llm_ok: bool
    ) -> dict:
        """Explain a single recommendation."""
        if llm_ok:
            prompt = self._build_rec_prompt(rec, profile)
            raw    = self._call_llm(prompt)
            if raw and self._is_valid(raw):
                return {"text": raw[:_MAX_LLM_OUTPUT], "source": "llm"}

        return {"text": self._template_rec(rec, profile), "source": "template"}

    # ── Prompt builders ─────────────────────────────────────────────────────────

    def _build_overview_prompt(self, wealth_result: dict, profile: dict) -> str:
        """Build the prompt for the opening overview paragraph."""
        name   = profile.get("name", "the customer")
        age    = profile.get("age", "")
        health = wealth_result.get("financial_health", {})
        score  = health.get("score", 0)
        grade  = health.get("grade", "")
        recs   = wealth_result.get("recommendations", [])
        n_recs = len(recs)
        goals  = wealth_result.get("goal_summaries", [])
        n_goals = len(goals)

        components = health.get("components", {})
        comp_text = ", ".join(
            f"{k.replace('_', ' ')} {v:.0f}/25"
            for k, v in components.items()
        )

        return (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are an encouraging, supportive financial wellness assistant for Punjab & Sind Bank.\n"
            f"Your job is to provide an objective, positive, and motivating overview of the customer's score layout. "
            f"Never be critical, judgmental, or use negative phrases like 'struggling' or 'failing'. Focus on growth steps.\n\n"
            f"CRITICAL PROSE RULES:\n"
            f"1. Output EXACTLY 2 to 3 sentences total. Get straight to the point.\n"
            f"2. Use simple, everyday plain English. The customer is not a financial expert.\n"
            f"3. Do NOT mention specific investment product labels or brand names.\n"
            f"4. ABSOLUTELY FORBIDDEN terms: advanced, systems, algorithms, monitoring, anomaly, risk-free, guaranteed, struggling, failing, vulnerable.\n"
            f"5. DO NOT include greetings, introductions, markdown quotation marks, or conversational preamble text.\n"
            f"6. End the statement exactly with: 'This is a simulation. Consult a SEBI-registered advisor before investing.'\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Write a brief overview paragraph using this metadata context:\n"
            f"- Account Holder Name: {name}, Age: {age}\n"
            f"- Account Score Rating: {score:.0f}/100 (Grade {grade})\n"
            f"- Allocation Components: {comp_text}\n"
            f"- Monitored Financial Goals: {n_goals}\n"
            f"- Total Direct Action Items: {n_recs}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )

    def _build_rec_prompt(self, rec: dict, profile: dict) -> str:
        """Build the prompt for a single recommendation explanation."""
        name    = profile.get("name", "the customer")
        age     = profile.get("age", "")
        product = rec.get("product", "")
        amount  = rec.get("amount", 0)
        tenure  = rec.get("tenure", "")
        reason  = rec.get("reason", "")
        benefit = rec.get("expected_benefit", "")
        source  = rec.get("source", "")

        return (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are a friendly financial wellness advisor for Punjab & Sind Bank.\n\n"
            f"CRITICAL TEXT RULES:\n"
            f"1. Output EXACTLY 2 clear sentences. Get straight to the facts.\n"
            f"2. ABSOLUTELY FORBIDDEN: Do not include introductory text like 'Here is a translation:', 'Friendly translation:', conversational meta-text, or markdown blockquotes.\n"
            f"3. Translate technical reasoning statements into warm, accessible customer actions.\n"
            f"4. Rely only on the given facts. Do not name specific mutual fund schemes, stocks, or indices.\n"
            f"5. FORBIDDEN WORDS: advanced, security systems, monitoring, algorithms, intelligence, risk-free, guaranteed, definitely.\n"
            f"6. End the explanation exactly with: 'This is a simulation. Consult a SEBI-registered advisor.'\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Provide customer translation text for this individual action profile:\n"
            f"- Target User: {name}, Age: {age}\n"
            f"- Recommended Category: {product}\n"
            f"- Value Target: Rs.{amount:,}\n"
            f"- Duration/Tenure: {tenure}\n"
            f"- Core Operational Reason: {reason}\n"
            f"- Expected Outcome/Benefit: {benefit}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )

    # ── Template fallbacks ──────────────────────────────────────────────────────

    def _template_overview(self, wealth_result: dict, profile: dict) -> str:
        """Deterministic overview from templates."""
        health   = wealth_result.get("financial_health", {})
        score    = health.get("score", 0)
        name     = profile.get("name", "")
        greeting = f"Hi {name}, " if name else ""

        grade_templates = self._templates.get("wealth_overview", {})
        cash_health     = "healthy" if score >= 60 else ("moderate" if score >= 40 else "stressed")
        base            = grade_templates.get(cash_health, "Here is your customized wealth status report.")

        return f"{greeting}{base} This is a simulation. Consult a SEBI-registered advisor before investing."

    def _suppressed_overview(self, reason: str, profile: dict) -> str:
        """Overview text when advice is suppressed."""
        name     = profile.get("name", "")
        greeting = f"Hi {name}, " if name else ""
        templates = self._templates.get("wealth_overview", {})

        if reason == "high_fraud_risk":
            msg = templates.get("suppressed_fraud", "Your wealth building dashboard insights are temporarily paused while our team completes a routine account update verification.")
        elif reason == "no_investable_surplus":
            msg = templates.get("no_surplus", "We analyzed your monthly outlays. Let's work together on optimizing routine expenses to establish a monthly saving surplus.")
        else:
            msg = "Your wealth dashboard information is temporarily processing."

        return f"{greeting}{msg}"

    def _template_rec(self, rec: dict, profile: dict) -> str:
        """Deterministic recommendation explanation from templates."""
        rec_id   = rec.get("recommendation_id", "")
        product  = rec.get("product", "")
        amount   = rec.get("amount", 0)
        reason   = rec.get("reason", "")
        name     = profile.get("name", "")

        rec_templates = self._templates.get("recommendation_explanations", {})

        template_text = rec_templates.get(rec_id)
        if not template_text:
            for key in rec_templates:
                if rec_id.startswith(key) or key.startswith(rec_id.split("_")[0]):
                    template_text = rec_templates[key]
                    break

        if template_text:
            base = f"For {name}: {template_text}" if name else template_text
        else:
            base = f"Suggested asset deployment to {product} of Rs.{amount:,}. {reason}"

        return f"{base} This is a simulation. Consult a SEBI-registered advisor."

    def _health_summary(self, health: dict) -> str:
        """Plain-language health score interpretation from templates."""
        score  = health.get("score", 0)
        grade  = health.get("grade", "D")
        grade_templates = self._templates.get("health_grades", {})
        template = grade_templates.get(grade, "")
        if template:
            return template.replace("{score}", f"{score:.0f}")
        return f"Your baseline account health balance index evaluates to {score:.0f} out of 100."

    # ── Validation ──────────────────────────────────────────────────────────────

    def _is_valid(self, text: str) -> bool:
        """Reject LLM output that contains banned jargon or breaches bounds."""
        import re
        if not text or len(text.strip()) < 30:
            return False
        if len(text) > _MAX_LLM_OUTPUT:
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

    # ── Loaders ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _load_templates() -> dict:
        """Load fallback templates from JSON."""
        try:
            with open(_TEMPLATES_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Could not load fallback templates: %s", exc)
            return {}