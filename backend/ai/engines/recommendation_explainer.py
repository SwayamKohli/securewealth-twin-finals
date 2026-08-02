"""
Wealth Recommendation Explainer
=================================
Converts WealthIntelligenceEngine output into personalized, human-readable
natural-language messages using a locally running Ollama LLM.

Integration contract (Ollama):
  - Model served by Ollama at http://localhost:11434
  - API: POST /api/generate  {model, prompt, stream: false}
  - Response: {"response": "...", "done": true}
  - If Ollama is unreachable or returns an error → graceful fallback to templates

Design principles:
  - This component is stateless. One instance can serve all requests.
  - LLM is always optional. If unavailable, the output is 100% template-based.
  - Every output contains the legal disclaimer verbatim.
  - No financial jargon (z-score, SHAP, autoencoder) leaks into output.
  - No guaranteed returns, no specific fund names, no stock picks.
  - Prompt is deterministic — same input always builds the same prompt.

This module never modifies, filters, reprioritizes, or generates wealth recommendations. 
It only converts the already generated Wealth Intelligence Engine output into customer-friendly explanations. 
Recommendation generation remains the exclusive responsibility of wealth_engine.py.

Sources referenced for prompting guidelines:
  [11] RBI Digital Lending Directions (2025) — no misleading claims
  [22] RBI Product Awareness norms — plain language for customers
  PSB FINALS.md §8 — SEBI compliance: no advisory activity
"""

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

# Default model name — can be overridden at construction time.
# Ollama model names: "llama3", "mistral", "phi3", "gemma2", etc.
# The calling system picks the model; we call whatever is registered.
_DEFAULT_MODEL  = "llama3"

# HTTP timeout — keep short so a slow/absent LLM doesn't block the API response
_TIMEOUT_SECS   = 45   # cold model load can take 15-40s; see llm_source

# Maximum characters accepted from LLM before we reject as hallucination
_MAX_LLM_OUTPUT = 600

# Technical terms / phrases that must never appear in customer-facing output.
# Matched as whole words / exact phrases (not substrings) — see _is_valid().
_BANNED_TERMS = frozenset([
    "z-score", "shap", "autoencoder", "xgboost", "reconstruction error",
    "sigmoid", "probability distribution", "feature importance",
    "guaranteed return", "will definitely", "risk-free",
    "you should buy", "100% safe", "buy shares", "stock pick",
    "mutual fund name", "nav value", "fund aum",
])


# ─── Explainer ────────────────────────────────────────────────────────────────

class RecommendationExplainer:
    """
    Converts WealthIntelligenceEngine output into personalized natural-language.

    Usage
    -----
    explainer = RecommendationExplainer(model="llama3")
    result = explainer.explain(wealth_result, profile)

    Parameters (constructor)
    ----------
    model   : str   Ollama model name. Default "llama3".
    base_url: str   Ollama base URL. Default "http://localhost:11434".

    Output of explain()
    -------------------
    {
        "overview"                   : str   — personalized opening paragraph
        "health_summary"             : str   — plain-language health score interpretation
        "recommendation_explanations": list  — one entry per recommendation
            {
                "recommendation_id" : str
                "recommendation"    : str   — short title from wealth engine
                "product"           : str
                "amount"            : int
                "tenure"            : str
                "explanation"       : str   — personalized explanation
                "expected_benefit"  : str   — carried through from wealth engine
                "priority"          : str
            }
        "goal_summaries"             : list  — goal progress, passed through unchanged
        "disclaimer"                 : str   — legal disclaimer, always present
        "generated_by"               : str   — "llm" | "template"
        "suppressed"                 : bool  — mirrored from wealth_result
        "suppress_reason"            : str   — only if suppressed
    }
    """

    def __init__(
        self,
        model:    str = _DEFAULT_MODEL,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model     = model
        self._api_url   = base_url.rstrip("/") + "/api/generate"
        self._templates = self._load_templates()
        # Cache Ollama availability at construction time.
        # If Ollama is not running when the explainer is instantiated, we skip
        # all LLM calls for the lifetime of this instance. The caller can
        # reconstruct a new instance if Ollama comes online later.
        self._llm_ok: bool = self._llm_available()

    # ── Public API ──────────────────────────────────────────────────────────────

    def explain(self, wealth_result: dict, profile: dict) -> dict:
        """
        Generate natural-language explanations for wealth recommendations.

        Parameters
        ----------
        wealth_result : dict   Output of WealthIntelligenceEngine.generate()
        profile       : dict   Output of FinancialProfileBuilder.build_profile()
                               (used for personalisation: name, age, income)
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
            return {
                "suppressed":                 True,
                "suppress_reason":            reason,
                "overview":                   overview,
                "health_summary":             health_summ,
                "recommendation_explanations": [],
                "goal_summaries":             goal_summaries,
                "disclaimer":                 disclaimer,
                "generated_by":              "template",
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
        }

    # ── LLM interaction ─────────────────────────────────────────────────────────

    def _llm_available(self) -> bool:
        """
        Probe Ollama health endpoint. Returns True only if Ollama is running
        and reachable. Does not check if the specific model is loaded.
        """
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
        """
        Call Ollama /api/generate with stream=false.
        Returns the response string, or None if the call fails.
        """
        payload = json.dumps({
            "model":  self._model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
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
        """
        Build the opening paragraph. Returns {"text": str, "source": "llm"|"template"}.
        """
        if llm_ok:
            prompt = self._build_overview_prompt(wealth_result, profile)
            raw    = self._call_llm(prompt)
            if raw and self._is_valid(raw):
                return {"text": raw[:_MAX_LLM_OUTPUT], "source": "llm"}

        return {"text": self._template_overview(wealth_result, profile), "source": "template"}

    def _explain_recommendation(
        self, rec: dict, profile: dict, llm_ok: bool
    ) -> dict:
        """
        Explain a single recommendation. Returns {"text": str, "source": "llm"|"template"}.
        """
        if llm_ok:
            prompt = self._build_rec_prompt(rec, profile)
            raw    = self._call_llm(prompt)
            if raw and self._is_valid(raw):
                return {"text": raw[:_MAX_LLM_OUTPUT], "source": "llm"}

        return {"text": self._template_rec(rec, profile), "source": "template"}

    # ── Prompt builders ─────────────────────────────────────────────────────────

    def _build_overview_prompt(self, wealth_result: dict, profile: dict) -> str:
        """
        Build the prompt for the opening overview paragraph.
        Structured prompt — the LLM only fills in the natural-language gap.
        """
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
            f"You are a financial wellness assistant for Punjab & Sind Bank.\n"
            f"Customer: {name}, age {age}\n"
            f"Financial health score: {score:.0f}/100 (Grade {grade})\n"
            f"Score components: {comp_text}\n"
            f"Goals on file: {n_goals}\n"
            f"Number of recommendations generated: {n_recs}\n\n"
            f"Write a friendly, personalised 2-3 sentence opening paragraph for this customer's "
            f"wealth report. Mention their health score and set the tone for the recommendations "
            f"below. Do NOT mention specific investment products. Do NOT use technical terms like "
            f"z-score, SHAP, or autoencoder. Do NOT guarantee returns or claim anything is risk-free. "
            f"End with: 'This is a simulation. Consult a SEBI-registered advisor before investing.'"
        )

    def _build_rec_prompt(self, rec: dict, profile: dict) -> str:
        """
        Build the prompt for a single recommendation explanation.
        The 'reason' field from the wealth engine is included as structured context
        — the LLM's job is to make it friendly and personal, not to invent facts.
        """
        name    = profile.get("name", "the customer")
        age     = profile.get("age", "")
        product = rec.get("product", "")
        amount  = rec.get("amount", 0)
        tenure  = rec.get("tenure", "")
        reason  = rec.get("reason", "")
        benefit = rec.get("expected_benefit", "")
        source  = rec.get("source", "")

        return (
            f"You are a financial wellness assistant for Punjab & Sind Bank.\n"
            f"Customer: {name}, age {age}\n"
            f"Recommendation: {rec.get('recommendation', '')}\n"
            f"Product category: {product}\n"
            f"Suggested amount: Rs.{amount:,}\n"
            f"Tenure: {tenure}\n"
            f"Why this recommendation: {reason}\n"
            f"Expected benefit: {benefit}\n"
            f"Source: {source}\n\n"
            f"Write a friendly, clear 2-3 sentence explanation of this recommendation for the customer. "
            f"Use simple language — the customer is not a finance expert. "
            f"Stick only to the facts given above. "
            f"Do NOT name specific mutual fund schemes or stocks. "
            f"Do NOT guarantee returns. Do NOT use words like 'risk-free' or 'definitely'. "
            f"Do NOT use technical terms like z-score, SHAP, autoencoder, or NAV. "
            f"End with: 'This is a simulation. Consult a SEBI-registered advisor.'"
        )

    # ── Template fallbacks ──────────────────────────────────────────────────────

    def _template_overview(self, wealth_result: dict, profile: dict) -> str:
        """Deterministic overview from templates — no LLM needed."""
        health   = wealth_result.get("financial_health", {})
        score    = health.get("score", 0)
        grade    = health.get("grade", "D")
        name     = profile.get("name", "")
        greeting = f"Hi {name}, " if name else ""

        grade_templates = self._templates.get("wealth_overview", {})
        cash_health     = "healthy" if score >= 60 else ("moderate" if score >= 40 else "stressed")
        base            = grade_templates.get(cash_health, "Here is your wealth report.")
        disclaimer      = self._templates.get("disclaimer", "")

        return f"{greeting}{base} This is a simulation. Consult a SEBI-registered advisor before investing."

    def _suppressed_overview(self, reason: str, profile: dict) -> str:
        """Overview text when advice is suppressed."""
        name     = profile.get("name", "")
        greeting = f"Hi {name}, " if name else ""
        templates = self._templates.get("wealth_overview", {})

        if reason == "high_fraud_risk":
            msg = templates.get("suppressed_fraud", "Your investment advice is currently paused.")
        elif reason == "no_investable_surplus":
            msg = templates.get("no_surplus", "No investable surplus at this time.")
        else:
            msg = "Your wealth advice is temporarily unavailable."

        return f"{greeting}{msg}"

    def _template_rec(self, rec: dict, profile: dict) -> str:
        """
        Deterministic recommendation explanation from templates.
        Looks up by recommendation_id first, then generates a generic version.
        """
        rec_id   = rec.get("recommendation_id", "")
        product  = rec.get("product", "")
        amount   = rec.get("amount", 0)
        reason   = rec.get("reason", "")
        name     = profile.get("name", "")

        # Look up pre-written template
        rec_templates = self._templates.get("recommendation_explanations", {})

        # Try exact match first, then try prefix match on rec_id
        template_text = rec_templates.get(rec_id)
        if not template_text:
            # Try to match by prefix (e.g., "education_fd" matches "education")
            for key in rec_templates:
                if rec_id.startswith(key) or key.startswith(rec_id.split("_")[0]):
                    template_text = rec_templates[key]
                    break

        if template_text:
            base = f"For {name}: {template_text}" if name else template_text
        else:
            # Generic fallback — use the reason field from the wealth engine directly
            base = f"Suggested {product} of Rs.{amount:,}. {reason}"

        disclaimer = self._templates.get("disclaimer", "")
        return f"{base} {disclaimer}"

    def _health_summary(self, health: dict) -> str:
        """Plain-language health score interpretation from templates."""
        score  = health.get("score", 0)
        grade  = health.get("grade", "D")
        grade_templates = self._templates.get("health_grades", {})
        template = grade_templates.get(grade, "")
        if template:
            return template.replace("{score}", f"{score:.0f}")
        return f"Financial health score: {score:.0f}/100 (Grade {grade})."

    # ── Validation ──────────────────────────────────────────────────────────────

    def _is_valid(self, text: str) -> bool:
        """
        Reject LLM output that:
          - contains banned technical jargon
          - is empty or too short to be useful
          - exceeds the character cap (likely hallucination)

        Multi-word banned phrases are matched as exact substrings.
        Single-word terms are matched as whole words (word-boundary) to avoid
        false positives (e.g. 'shap' inside 'shape', 'nav' inside 'navigation').
        """
        import re
        if not text or len(text.strip()) < 30:
            return False
        if len(text) > _MAX_LLM_OUTPUT:
            return False
        text_lower = text.lower()
        for term in _BANNED_TERMS:
            if " " in term:
                # Multi-word phrase — exact substring match is fine
                if term in text_lower:
                    return False
            else:
                # Single word — whole-word match to avoid false positives
                if re.search(rf"\b{re.escape(term)}\b", text_lower):
                    return False
        return True

    # ── Loaders ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _load_templates() -> dict:
        """Load fallback templates from JSON. Returns empty dict on failure."""
        try:
            with open(_TEMPLATES_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Could not load fallback templates: %s", exc)
            return {}
