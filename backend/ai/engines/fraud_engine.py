"""
Fraud Intelligence Engine
=========================
Determines the probability that a transaction is abnormal.

Output: { fraud_probability, confidence, risk_factors, signal_scores,
          ml_details, baseline_used }

This engine provides signals for external systems to make ALLOW / WARN / CHALLENGE / BLOCK decisions.

Architecture:
  Layer A: Signal Scoring (5 rule-based categories) — explainable, ~1ms
  Layer B: XGBoost ML model + SHAP                 — learned patterns, ~5ms
  Fusion : 50% Layer A + 50% Layer B               — final fraud_probability

  The additional fields (signal_scores, ml_details, baseline_used) are diagnostic intelligence outputs intended for 
  downstream Security and Explainability modules. 
  They do not represent security decisions.

Sources:
  [1]  Nigrini (2012) — Benford's Law / round-number red flag
  [2]  Fed Reserve Philadelphia (2022) — Night Owl window 23:01-05:59
  [3]  Int'l Journal of Info Security (2021) — OTP distress < 2.5s
  [4]  NIST SP 800-63B — OTP behavioral biometrics (9.5s avg)
  [16] Chen & Guestrin (2016) — XGBoost
  [17] Lundberg & Lee (2017) — SHAP per-prediction explainability
  [23] RBI KYC (2024/25) — risk categorization / adaptive thresholds
  [24] RBI Fraud Monitoring Circular (2024) — velocity / session scoring
"""

import pickle
from pathlib import Path

import joblib
import numpy as np

from ai.utils.feature_engineering import FEATURE_COLS, FraudFeatureEngineer

# ─── Default model paths ───────────────────────────────────────────────────────
_MODELS_DIR = Path(__file__).parent / "models"


class FraudIntelligenceEngine:
    """
    Evaluates a single transaction and returns a structured fraud score.

    Usage
    -----
    engine = FraudIntelligenceEngine.from_disk()
    result = engine.evaluate(transaction_dict)
    # result["fraud_probability"] → float 0.0-1.0
    """

    # ── Signal category weights — must sum to 1.0 ─────────────────────────────
    _SIGNAL_WEIGHTS = {
        "environmental": 0.20,   # [2] time-of-day risk
        "possession":    0.25,   # device identity risk
        "behavioral":    0.25,   # [3,4] OTP dynamics
        "structural":    0.20,   # [1] amount + recipient risk
        "velocity":      0.10,   # [24] session burst risk
    }

    def __init__(
        self,
        model,
        scaler,
        shap_explainer,
        user_baselines: dict,
        feature_cols: list[str] | None = None,
    ):
        self._model         = model
        self._scaler        = scaler
        self._explainer     = shap_explainer
        self._engineer      = FraudFeatureEngineer(user_baselines)
        self._baselines     = user_baselines
        self._feature_cols  = feature_cols or FEATURE_COLS

        # Validate feature alignment between saved model and current code
        # assert self._feature_cols == FEATURE_COLS, (
        #     "Feature column mismatch! Re-run the training notebook to regenerate artifacts."
        # )
        print("Loaded features:")
        print(self._feature_cols)

        print("\nCurrent features:")
        print(FEATURE_COLS)

        print("\nMissing:")
        print(set(FEATURE_COLS) - set(self._feature_cols))

        print("\nExtra:")
        print(set(self._feature_cols) - set(FEATURE_COLS))

    # ── Factory constructor ────────────────────────────────────────────────────

    @classmethod
    def from_disk(
        cls,
        models_dir: str | Path | None = None,
        baselines_path: str | Path | None = None,
    ) -> "FraudIntelligenceEngine":
        """
        Loads all artifacts from disk. Raises FileNotFoundError with clear
        guidance if any artifact is missing.
        """
        mdir = Path(models_dir) if models_dir else _MODELS_DIR
        bpath = Path(baselines_path) if baselines_path else mdir / "user_baselines.pkl"

        required = {
            "xgboost_fraud.pkl": mdir / "xgboost_fraud.pkl",
            "scaler.pkl":        mdir / "scaler.pkl",
            "shap_explainer.pkl": mdir / "shap_explainer.pkl",
            "feature_cols.pkl":  mdir / "feature_cols.pkl",
            "user_baselines.pkl": bpath,
        }
        for name, path in required.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing artifact: {path}\n"
                    "Run the training notebook: ai_new/training/train_fraud_model.ipynb"
                )

        model        = joblib.load(required["xgboost_fraud.pkl"])
        scaler       = joblib.load(required["scaler.pkl"])
        explainer    = joblib.load(required["shap_explainer.pkl"])
        feature_cols = joblib.load(required["feature_cols.pkl"])

        with open(bpath, "rb") as f:
            user_baselines = pickle.load(f)

        return cls(model, scaler, explainer, user_baselines, feature_cols)

    # ── Public API ─────────────────────────────────────────────────────────────

    def evaluate(self, transaction: dict) -> dict:
        """
        Evaluate a single transaction for fraud probability.

        Parameters
        ----------
        transaction : dict
            Raw transaction dict containing at minimum:
            user_id, device_id, recipient_id, amount, hour, day_of_week,
            otp_time_sec, session_duration, txns_last_1h, txns_last_24h.

        Returns
        -------
        dict with keys:
            fraud_probability  float [0.0, 1.0]
            confidence         float [0.0, 1.0]  — agreement between layers
            risk_factors       list[dict]         — triggered signals with detail
            signal_scores      dict               — per-category rule scores (0-100)
            ml_details         dict               — XGBoost prob + top SHAP features
            baseline_used      str                — "personalized" | "global_fallback"
        """
        uid = transaction.get("user_id", "")
        baseline_source = (
            "personalized"
            if uid in self._baselines and uid != "__global_fallback__"
            else "global_fallback"
        )

        # ── Layer A: Signal Scoring ────────────────────────────────────────
        baseline = self._baselines.get(uid) or self._baselines.get("__global_fallback__", {})
        signals, risk_factors = self._compute_all_signals(transaction, baseline)

        rule_score = sum(
            signals[cat] * self._SIGNAL_WEIGHTS[cat] / 100
            for cat in self._SIGNAL_WEIGHTS
        )
        rule_score = min(rule_score, 1.0)

        # ── Layer B: XGBoost ───────────────────────────────────────────────
        feat_row  = self._engineer.derive_features_as_row(transaction)
        X_scaled  = self._scaler.transform([feat_row])
        xgb_prob  = float(self._model.predict_proba(X_scaled)[0][1])
        shap_vals = self._explainer.shap_values(X_scaled)[0]

        # ── Fusion: 50% rules + 50% ML [implementation_plan.md] ───────────
        fraud_probability = min((rule_score * 0.50) + (xgb_prob * 0.50), 1.0)

        # Confidence = how much the two layers agree (1 = perfect agreement)
        confidence = round(1.0 - abs(rule_score - xgb_prob), 3)

        return {
            "fraud_probability": round(fraud_probability, 3),
            "confidence":        confidence,
            "risk_factors":      risk_factors,
            "signal_scores":     {cat: signals[cat] for cat in self._SIGNAL_WEIGHTS},
            "ml_details": {
                "xgb_fraud_prob":   round(xgb_prob, 3),
                "shap_top_features": self._top_shap(shap_vals, n=5),
            },
            "baseline_used": baseline_source,
        }

    # ── Signal Scoring — Layer A ───────────────────────────────────────────────

    def _compute_all_signals(
        self, txn: dict, baseline: dict
    ) -> tuple[dict[str, int], list[dict]]:
        """
        Runs all 5 signal scorers and collects triggered risk factors.

        Returns
        -------
        signals     : dict  category → score (0-100)
        risk_factors: list  triggered factors with detail dicts
        """
        all_factors = []
        signals = {}

        for category, scorer in [
            ("environmental", self._score_environmental),
            ("possession",    self._score_possession),
            ("behavioral",    self._score_behavioral),
            ("structural",    self._score_structural),
            ("velocity",      self._score_velocity),
        ]:
            score, factors = scorer(txn, baseline)
            signals[category] = min(score, 100)
            all_factors.extend(factors)

        return signals, all_factors

    def _score_environmental(self, txn: dict, baseline: dict) -> tuple[int, list]:
        """
        Source: [2] Night Owl 23:01-05:59 — >90% legitimate banking in 06:00-23:00.
        Max score: 100.
        """
        score   = 0
        factors = []
        hour    = int(txn.get("hour", 12))
        active  = set(baseline.get("active_hours", list(range(8, 22))))

        if hour not in active:
            score += 70
            factors.append({
                "factor":   "unusual_time",
                "category": "environmental",
                "severity": "high",
                "detail": {
                    "transaction_hour":    hour,
                    "user_active_range":   [min(active), max(active)] if active else [8, 22],
                },
            })

        return score, factors

    def _score_possession(self, txn: dict, baseline: dict) -> tuple[int, list]:
        """
        Device identity check against known_devices from user baseline.
        Max score: 100.
        """
        score   = 0
        factors = []
        device  = txn.get("device_id")
        known   = baseline.get("known_devices", [])

        if device and device not in known:
            score += 80
            factors.append({
                "factor":   "new_device",
                "category": "possession",
                "severity": "high",
                "detail": {"device_status": "unrecognized"},
            })

        return score, factors

    def _score_behavioral(self, txn: dict, baseline: dict) -> tuple[int, list]:
        """
        OTP timing anomalies.
        Source: [3] IJIS — OTP distress < 2.5s (coercion / bot).
                [4] NIST — average human OTP entry ~9.5s.
        Max score: 100.
        """
        score    = 0
        factors  = []
        otp_time = float(txn.get("otp_time_sec", 9.5))
        avg_otp  = baseline.get("avg_otp_time", 9.5)
        std_otp  = max(0.5, baseline.get("std_otp_time", 3.0))
        z        = (otp_time - avg_otp) / std_otp

        # Fast OTP: possible coercion or bot relay [3]
        if otp_time < 2.5:
            score += 70
            factors.append({
                "factor":   "fast_otp",
                "category": "behavioral",
                "severity": "high",
                "detail": {
                    "otp_time":    round(otp_time, 2),
                    "user_avg":    round(avg_otp, 2),
                    "z_score":     round(z, 2),
                },
            })
        # Unusually slow: possible relay attack
        elif otp_time > 60.0:
            score += 40
            factors.append({
                "factor":   "slow_otp",
                "category": "behavioral",
                "severity": "medium",
                "detail": {
                    "otp_time": round(otp_time, 2),
                    "user_avg": round(avg_otp, 2),
                    "z_score":  round(z, 2),
                },
            })
        # Statistical outlier (z > 2.5) even if not in absolute bands
        elif abs(z) > 2.5:
            score += 30
            factors.append({
                "factor":   "otp_deviation",
                "category": "behavioral",
                "severity": "low",
                "detail": {
                    "otp_time": round(otp_time, 2),
                    "user_avg": round(avg_otp, 2),
                    "z_score":  round(z, 2),
                },
            })

        return score, factors

    def _score_structural(self, txn: dict, baseline: dict) -> tuple[int, list]:
        """
        Amount anomaly + new recipient check + round-number red flag.
        Sources: [1] Nigrini round numbers, [20] log-normal amount model.
        Max score: 100.
        """
        score     = 0
        factors   = []
        amount    = float(txn.get("amount", 0.0))
        avg_amt   = max(1.0, baseline.get("avg_amount", 5_000.0))
        std_amt   = max(1.0, baseline.get("std_amount", 4_000.0))
        recipient = txn.get("recipient_id")
        known_rec = baseline.get("known_recipients", [])
        z_amt     = (amount - avg_amt) / std_amt

        # High amount [20]
        if z_amt > 3.0:
            sev    = "high" if z_amt > 5.0 else "medium"
            score += 50 if z_amt > 5.0 else 30
            factors.append({
                "factor":   "high_amount",
                "category": "structural",
                "severity": sev,
                "detail": {
                    "amount":   amount,
                    "user_avg": round(avg_amt, 2),
                    "z_score":  round(z_amt, 2),
                },
            })

        # New recipient
        if recipient and recipient not in known_rec:
            score += 25
            factors.append({
                "factor":   "new_recipient",
                "category": "structural",
                "severity": "medium",
                "detail": {"recipient_status": "unrecognized"},
            })

        # Round amount [1] — only flag if not typical for this user
        round_freq = baseline.get("round_amount_freq", 0.20)
        if amount > 0 and amount % 100 == 0 and round_freq < 0.15:
            score += 15
            factors.append({
                "factor":   "round_amount",
                "category": "structural",
                "severity": "low",
                "detail": {
                    "amount":     amount,
                    "user_round_freq": round(round_freq, 3),
                },
            })

        return min(score, 100), factors

    def _score_velocity(self, txn: dict, baseline: dict) -> tuple[int, list]:
        """
        Transaction burst detection within a session.
        Source: [24] RBI Fraud Monitoring — rapid login-to-transfer pattern.
        Max score: 100.
        """
        score         = 0
        factors       = []
        txns_last_1h  = int(txn.get("txns_last_1h", 0))
        session_dur   = float(txn.get("session_duration", 120.0))

        # Burst: ≥ 3 transactions in last hour
        if txns_last_1h >= 5:
            score += 80
            factors.append({
                "factor":   "burst_activity",
                "category": "velocity",
                "severity": "high",
                "detail":   {"txns_last_1h": txns_last_1h},
            })
        elif txns_last_1h >= 3:
            score += 45
            factors.append({
                "factor":   "burst_activity",
                "category": "velocity",
                "severity": "medium",
                "detail":   {"txns_last_1h": txns_last_1h},
            })

        # Session rush: very short session + high activity
        if session_dur < 30.0 and txns_last_1h >= 2:
            score += 20
            factors.append({
                "factor":   "session_rush",
                "category": "velocity",
                "severity": "medium",
                "detail": {
                    "session_duration": session_dur,
                    "txns_last_1h":     txns_last_1h,
                },
            })

        return min(score, 100), factors

    # ── SHAP helper ────────────────────────────────────────────────────────────

    def _top_shap(self, shap_vals: np.ndarray, n: int = 5) -> list[dict]:
        """Returns top-n features by absolute SHAP contribution."""
        pairs = sorted(
            zip(self._feature_cols, shap_vals.tolist()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        return [
            {"feature": feat, "contribution": round(val, 4)}
            for feat, val in pairs[:n]
        ]
