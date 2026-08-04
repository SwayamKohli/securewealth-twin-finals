"""
Zero-Day Intelligence Engine
==============================
Detects previously unseen transaction patterns using a PyTorch autoencoder
trained exclusively on legitimate transactions.

Architecture:
  Trained on  : legitimate transactions ONLY (never fraud during training)
  Detection   : high reconstruction error = pattern was never seen before
  Output      : NORMAL | ANOMALOUS | UNKNOWN_RISK + anomalous_dimensions

Status classification (from training error distribution):
  < P95  → NORMAL        (reconstruction close to training distribution)
  < P99  → ANOMALOUS     (unusual but recognisably similar to known patterns)
  >= P99 → UNKNOWN_RISK  (never seen anything like this)

This engine runs independently from the Fraud Intelligence Engine.
Both outputs are evaluated together.
This engine provides signals but does NOT decide ALLOW / WARN / CHALLENGE / BLOCK.

Sources:
  [18] Sakurada & Yairi (2014) — Anomaly Detection Using Autoencoders, MLSDA.
       P95/P99 threshold strategy: statistically grounded, avoids arbitrary tuning.
  [19] Jesus et al. (2022) — BAF Dataset; one-class learning on legit-only data.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

# CRITICAL: use the SAME adapter as the XGBoost path, not
# ai.utils.feature_engineering.
#
# feature_engineering.FEATURE_COLS is this repo's own 22-feature set
# (day_sin, velocity_1h, device_trust_score, …). The autoencoder was trained in
# the original ai_new layout against a DIFFERENT 22 features (amount,
# amount_z_score, otp_time_sec, burst_flag, …). Only 4 names overlap, and none
# of those share a position.
#
# Feeding the wrong vector means ae_scaler applies `amount`'s mean and std to
# whatever sits in that slot at runtime — velocity_1h — and so on for all 22.
# Reconstruction error came out ~5,000x the p99 threshold, so EVERY
# transaction, including an ordinary ₹4,000 SIP, was classified UNKNOWN_RISK
# and escalated to CHALLENGE. The model was loaded and completely misinformed.
#
# LEGACY_FEATURE_COLS is byte-identical to ae_thresholds.json["feature_cols"],
# in the same order, which is exactly the contract the model was trained on.
from ai.utils.legacy_feature_adapter import (
    LEGACY_FEATURE_COLS as FEATURE_COLS,
    LegacyFeatureAdapter,
)

# ─── Default artifact paths ────────────────────────────────────────────────────
_MODELS_DIR = Path(__file__).parent / "models"


# ─── Autoencoder Architecture ─────────────────────────────────────────────────

def _register_legacy_module_alias() -> None:
    """
    Make `ai_new.zero_day_detector` resolve to this module.

    Only needed while loading artifacts trained in the original `ai_new`
    package layout. Idempotent and harmless if called repeatedly.
    """
    import sys
    import types

    if "ai_new" not in sys.modules:
        pkg = types.ModuleType("ai_new")
        pkg.__path__ = []          # mark as a package so submodules resolve
        sys.modules["ai_new"] = pkg
    sys.modules["ai_new.zero_day_detector"] = sys.modules[__name__]
    setattr(sys.modules["ai_new"], "zero_day_detector", sys.modules[__name__])


class TransactionAutoencoder(nn.Module):
    """
    Symmetric dense autoencoder for transaction anomaly detection.

    Architecture (for input_dim = 22):
      Encoder: 22 → 11 → 5
      Decoder:  5 → 11 → 22

    Bottleneck forces the model to learn a compressed representation of
    NORMAL transaction patterns. High reconstruction error on unseen/fraud
    patterns signals they fall outside the learned distribution.

    Source: [18] Simple dense autoencoder — NOT VAE, NOT CNN, NOT LSTM.
    Plain MSE reconstruction loss is intentional: simpler, faster, interpretable.
    """

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        hidden     = max(input_dim // 2, 4)
        bottleneck = max(input_dim // 4, 2)

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),           # light dropout — prevents memorisation
            nn.Linear(hidden, bottleneck),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, input_dim),
            # No activation on output — input is z-scored, so output is unbounded
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


# ─── Runtime Detector ─────────────────────────────────────────────────────────

class ZeroDayDetector:
    """
    Detects anomalous transaction patterns via autoencoder reconstruction error.

    Usage
    -----
    detector = ZeroDayDetector.from_disk()
    result   = detector.detect(transaction_dict)
    # result["status"] → "NORMAL" | "ANOMALOUS" | "UNKNOWN_RISK"

    The detector is stateless and thread-safe. One instance can serve all requests.
    Expected latency: ~2ms per call (CPU), ~0.5ms (GPU).
    """

    def __init__(
        self,
        autoencoder:  TransactionAutoencoder,
        ae_scaler,
        p95_threshold: float,
        p99_threshold: float,
        user_baselines: dict,
        device: str = "cpu",
    ) -> None:
        self._autoencoder   = autoencoder.to(device)
        self._autoencoder.eval()
        self._ae_scaler     = ae_scaler
        self._p95           = p95_threshold
        self._p99           = p99_threshold
        self._engineer      = LegacyFeatureAdapter(user_baselines)
        self._device        = device
        self._feature_cols  = FEATURE_COLS

    # ── Factory ────────────────────────────────────────────────────────────────

    @classmethod
    def from_disk(
        cls,
        models_dir:     str | Path | None = None,
        baselines_path: str | Path | None = None,
        device:         str               = "cpu",
    ) -> "ZeroDayDetector":
        """
        Load all artifacts from disk. Raises FileNotFoundError with clear
        guidance if any artifact is missing.

        Parameters
        ----------
        models_dir     : directory containing autoencoder artifacts
                         (defaults to ai_new/models/)
        baselines_path : path to user_baselines.pkl
                         (defaults to models_dir/user_baselines.pkl)
        device         : "cpu" or "cuda"
        """
        mdir  = Path(models_dir)  if models_dir     else _MODELS_DIR
        bpath = Path(baselines_path) if baselines_path else mdir / "user_baselines.pkl"

        required = {
            "autoencoder.pth":    mdir / "autoencoder.pth",
            "ae_thresholds.json": mdir / "ae_thresholds.json",
            "ae_scaler.pkl":      mdir / "ae_scaler.pkl",
            "user_baselines.pkl": bpath,
        }
        for name, path in required.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing artifact: {path}\n"
                    "Run the training notebook: ai_new/training/train_zero_day.ipynb"
                )

        # Load autoencoder
        #
        # autoencoder.pth is a PICKLED MODEL OBJECT, not a state_dict, so the
        # pickle records the class's ORIGINAL import path from the training
        # notebook: ai_new.zero_day_detector.TransactionAutoencoder. That
        # package does not exist in this repo — the same class lives here — so
        # unpickling failed with "No module named 'ai_new'" and the pipeline
        # silently fell back to the statistical detector.
        #
        # Register an alias so the pickle resolves to THIS module's class. The
        # architecture is identical (encoder/decoder Sequentials, 22 inputs),
        # and the weights come from the pickle, so nothing is reinterpreted.
        #
        # The alternative — asking for a re-export as a state_dict — is cleaner
        # long term but needs the notebook re-run; this needs nothing.
        _register_legacy_module_alias()

        autoencoder = torch.load(
            required["autoencoder.pth"],
            map_location=device,
            weights_only=False,
        )
        if not isinstance(autoencoder, TransactionAutoencoder):
            raise TypeError(
                f"Expected TransactionAutoencoder, got {type(autoencoder).__name__}. "
                "Re-run the training notebook."
            )

        # Load thresholds
        with open(required["ae_thresholds.json"], encoding="utf-8") as f:
            thresholds = json.load(f)

        # Verify the feature contract instead of assuming it.
        #
        # ae_thresholds.json records the exact column order the model was
        # trained on. If a future retrain uses a different set, silently
        # feeding it the legacy vector would put every value in the wrong
        # semantic slot — which is precisely the failure this detector already
        # had once: reconstruction error ~5,000x the threshold, so every
        # ordinary transaction came back UNKNOWN_RISK and was challenged.
        #
        # Fail loudly. The pipeline catches this and falls back to the
        # statistical detector, which is far better than a confidently wrong
        # autoencoder. FraudEngine does the same check for XGBoost.
        trained_cols = thresholds.get("feature_cols")
        if trained_cols and list(trained_cols) != list(FEATURE_COLS):
            missing = set(trained_cols) - set(FEATURE_COLS)
            extra = set(FEATURE_COLS) - set(trained_cols)
            raise ValueError(
                "Zero-day feature contract mismatch: autoencoder.pth was trained "
                f"on {len(trained_cols)} columns that do not match the adapter's "
                f"{len(FEATURE_COLS)}.\n"
                f"  only in model  : {sorted(missing) or 'none (order differs)'}\n"
                f"  only in adapter: {sorted(extra) or 'none (order differs)'}\n"
                "Update ai/utils/legacy_feature_adapter.py to match the model, or "
                "retrain against the current adapter."
            )

        # Load scaler
        with open(required["ae_scaler.pkl"], "rb") as f:
            ae_scaler = pickle.load(f)

        # Load user baselines
        with open(bpath, "rb") as f:
            user_baselines = pickle.load(f)

        return cls(
            autoencoder    = autoencoder,
            ae_scaler      = ae_scaler,
            p95_threshold  = float(thresholds["p95"]),
            p99_threshold  = float(thresholds["p99"]),
            user_baselines = user_baselines,
            device         = device,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect(self, transaction: dict) -> dict:
        """
        Score a single transaction for novelty / zero-day risk.

        Parameters
        ----------
        transaction : dict
            Same raw transaction dict accepted by FraudIntelligenceEngine.evaluate().

        Returns
        -------
        dict with keys:
            status                str   "NORMAL" | "ANOMALOUS" | "UNKNOWN_RISK"
            confidence            float 0.0–1.0  (how far above P99 the error is)
            reconstruction_error  float mean squared error across all features
            error_percentile      float approximate percentile vs training distribution
            anomalous_dimensions  list  top features with highest per-feature error
        """
        # ── Feature engineering ────────────────────────────────────────────
        feat_row = self._engineer.derive_features_as_row(transaction)
        feat_arr = np.array([feat_row], dtype=np.float32)

        # Apply the same scaler used during training
        feat_scaled = self._ae_scaler.transform(feat_arr)

        X = torch.tensor(feat_scaled, dtype=torch.float32, device=self._device)

        # ── Forward pass (no gradient needed at inference) ─────────────────
        with torch.no_grad():
            reconstructed = self._autoencoder(X)

        # ── Per-feature and total reconstruction error (MSE) ──────────────
        per_feature_mse = ((X - reconstructed) ** 2).squeeze().cpu().numpy()
        total_mse       = float(per_feature_mse.mean())

        # ── Status classification against training distribution ────────────
        # Source: [18] P95/P99 are statistically grounded thresholds.
        # P95 = ANOMALOUS boundary (top 5% of normal error)
        # P99 = UNKNOWN_RISK boundary (top 1% of normal error)
        if total_mse < self._p95:
            status = "NORMAL"
        elif total_mse < self._p99:
            status = "ANOMALOUS"
        else:
            status = "UNKNOWN_RISK"

        # Confidence = how far beyond P99 the error has gone (capped at 1.0)
        # At P99 → confidence = 1.0. Below P95 → confidence = 0.0.
        if total_mse < self._p95:
            confidence = 0.0
        elif total_mse < self._p99:
            # Linear interpolation between P95 and P99
            confidence = (total_mse - self._p95) / max(self._p99 - self._p95, 1e-9)
        else:
            confidence = min(total_mse / max(self._p99, 1e-9), 1.0)
        confidence = round(float(confidence), 3)

        # Approximate percentile (linear mapping from 0 → P95 = 0–95th,
        # P95 → P99 = 95th–99th, above P99 = 99+)
        error_percentile = self._error_to_percentile(total_mse)

        # ── Top anomalous dimensions ───────────────────────────────────────
        anomalous_dims = self._top_anomalous_features(per_feature_mse)

        return {
            "status":               status,
            "confidence":           confidence,
            "reconstruction_error": round(total_mse, 6),
            "error_percentile":     error_percentile,
            "anomalous_dimensions": anomalous_dims,
        }

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _error_to_percentile(self, error: float) -> float:
        """
        Approximate error percentile relative to training distribution.
        Linear interpolation across three known reference points.
        """
        if error <= 0.0:
            return 0.0
        if error < self._p95:
            # 0 to P95 maps to 0th–95th percentile
            pct = (error / max(self._p95, 1e-9)) * 95.0
        elif error < self._p99:
            # P95 to P99 maps to 95th–99th percentile
            pct = 95.0 + ((error - self._p95) / max(self._p99 - self._p95, 1e-9)) * 4.0
        else:
            # Above P99: 99th+ (cap at 99.9)
            pct = min(99.0 + (error / max(self._p99, 1e-9) - 1.0), 99.9)
        return round(pct, 1)

    def _top_anomalous_features(
        self, per_feature_mse: np.ndarray, n: int = 5
    ) -> list[dict]:
        """
        Return top-n features ranked by per-feature reconstruction error.
        Only includes features with error meaningfully above P95.

        Returns
        -------
        list of dicts: [{"feature": str, "reconstruction_error": float}, ...]
        """
        # Threshold: feature must exceed 1.5× the total P95 to be listed
        feature_threshold = self._p95 * 1.5

        candidates = [
            {"feature": self._feature_cols[i], "reconstruction_error": round(float(e), 6)}
            for i, e in enumerate(per_feature_mse)
            if float(e) > feature_threshold
        ]
        candidates.sort(key=lambda x: x["reconstruction_error"], reverse=True)
        return candidates[:n]
