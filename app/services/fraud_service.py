"""
Fraud Detection Service for ATLAS-OPS.

Scores a transaction for fraud probability and extracts SHAP feature
contributions to explain the decision.
"""
from typing import Any

import numpy as np

from app.core.logging import get_logger
from app.services.ml_loader import (
    FRAUD_FEATURES,
    get_models,
    safe_label_encode,
    scale_features,
)

logger = get_logger(__name__)


class FraudService:
    """Stateless service — relies on the globally loaded model singleton."""

    @staticmethod
    def _build_feature_vector(features: dict[str, Any]) -> np.ndarray:
        """
        Map a normalised features dict to a numpy row using FRAUD_FEATURES order.
        Applies real LabelEncoders for strings and StandardScaler for numericals.
        """
        models = get_models()

        # 1. Apply Label Encoding to known string fields
        # Note: features dict uses 'P_emaildomain', encoders dict uses 'email_domain'
        if "P_emaildomain" in features:
            features["P_emaildomain"] = safe_label_encode(
                models.label_encoders.get("email_domain"), features["P_emaildomain"]
            )
        if "DeviceType" in features:
            features["DeviceType"] = safe_label_encode(
                models.label_encoders.get("device_type"), features["DeviceType"]
            )
        if "DeviceInfo" in features:
            features["DeviceInfo"] = safe_label_encode(
                models.label_encoders.get("device_info"), features["DeviceInfo"]
            )

        # 2. Scale features
        scaled_features = scale_features(models.standard_scaler, features)

        row = []
        for fname in FRAUD_FEATURES:
            val = scaled_features.get(fname, 0)
            row.append(float(val))
        return np.array([row])

    @staticmethod
    async def score(features: dict[str, Any]) -> tuple[float, dict[str, float]]:
        """
        Score a transaction for fraud.

        Args:
            features: dict with keys matching FRAUD_FEATURES

        Returns:
            (fraud_probability: float, shap_values: dict[feature_name -> contribution])
        """
        models = get_models()
        X = FraudService._build_feature_vector(features)

        # ── Prediction ───────────────────────────────────────────────────────
        try:
            proba = models.fraud_model.predict_proba(X)[0]
            # proba shape: (n_classes,)  — index 1 = P(fraud)
            fraud_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as exc:
            logger.error("fraud_model_prediction_failed", error=str(exc))
            # Safe operational fallback if model prediction crashes
            fraud_prob = 0.5

        # ── SHAP ─────────────────────────────────────────────────────────────
        shap_dict: dict[str, float] = {}
        explainer = models.fraud_explainer
        if explainer is not None:
            try:
                shap_vals = explainer.shap_values(X)
                # shap_vals can be (classes, samples, features) for multi-class
                if isinstance(shap_vals, list):
                    vals = shap_vals[1][0]  # class-1 SHAP values for sample 0
                else:
                    vals = shap_vals[0]
                shap_dict = {
                    feat: round(float(v), 6)
                    for feat, v in zip(FRAUD_FEATURES, vals)
                }
            except Exception as exc:
                logger.warning("fraud_shap_failed", error=str(exc))
                shap_dict = {feat: 0.0 for feat in FRAUD_FEATURES}
        else:
            shap_dict = {feat: 0.0 for feat in FRAUD_FEATURES}

        logger.info(
            "fraud_scored",
            fraud_probability=round(fraud_prob, 4),
            top_feature=max(shap_dict, key=lambda k: abs(shap_dict[k]))
            if shap_dict
            else "n/a",
        )
        return fraud_prob, shap_dict
