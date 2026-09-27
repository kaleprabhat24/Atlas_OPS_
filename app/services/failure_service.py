"""
Payment Failure Diagnosis Service for ATLAS-OPS.

Runs the failure model against gateway telemetry and extracts SHAP values
to identify which features contributed most to the failure.
"""
from typing import Any

import numpy as np

from app.core.logging import get_logger
from app.services.ml_loader import (
    FAILURE_FEATURES,
    get_models,
    safe_label_encode,
    scale_features,
)

logger = get_logger(__name__)


class FailureService:

    @staticmethod
    def _build_feature_vector(gateway_error: dict[str, Any]) -> np.ndarray:
        """
        Build the failure model feature vector from raw gateway error metadata.
        """
        models = get_models()

        gw_name = gateway_error.get("payment_gateway", "unknown")
        acq_bank = gateway_error.get("acquirer_bank", "unknown")

        # Use actual label encoders
        gw_encoded = safe_label_encode(models.label_encoders.get("gateway_id"), gw_name)
        bank_encoded = safe_label_encode(models.label_encoders.get("bank_id"), acq_bank)

        mapping = {
            "gateway_latency_ms": gateway_error.get("gateway_latency_ms", 0.0),
            "retry_attempts": gateway_error.get("retry_attempts", 0),
            "gateway_health_score": gateway_error.get("gateway_health_score", 1.0),
            "recent_success_rate": gateway_error.get("recent_success_rate", 1.0),
            "timeout_flag": int(gateway_error.get("timeout_flag", False)),
            "connection_drop_flag": int(gateway_error.get("connection_drop_flag", False)),
            "dns_failure_flag": int(gateway_error.get("dns_failure_flag", False)),
            "http_status_code": gateway_error.get("http_status_code", 200),
            "payment_gateway": gw_encoded,
            "acquirer_bank": bank_encoded,
        }

        # Apply standard scaling dynamically
        scaled_mapping = scale_features(models.standard_scaler, mapping)

        row = [float(scaled_mapping.get(f, 0.0)) for f in FAILURE_FEATURES]
        return np.array([row])

    @staticmethod
    async def diagnose(
        gateway_error: dict[str, Any],
        transaction_shap: dict[str, float],
    ) -> tuple[float, dict[str, Any]]:
        """
        Diagnose a payment failure.

        Args:
            gateway_error: raw gateway error telemetry
            transaction_shap: SHAP values from the fraud model for context

        Returns:
            (failure_probability, diagnosis_dict)
        """
        models = get_models()
        X = FailureService._build_feature_vector(gateway_error)

        # ── Prediction ───────────────────────────────────────────────────────
        try:
            proba = models.failure_model.predict_proba(X)[0]
            failure_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as exc:
            logger.error("failure_model_prediction_failed", error=str(exc))
            # Safe operational fallback if model prediction crashes
            failure_prob = 0.5

        # ── SHAP ─────────────────────────────────────────────────────────────
        shap_dict: dict[str, float] = {}
        explainer = models.failure_explainer
        if explainer is not None:
            try:
                shap_vals = explainer.shap_values(X)
                if isinstance(shap_vals, list):
                    vals = shap_vals[1][0]
                else:
                    vals = shap_vals[0]
                shap_dict = {
                    feat: round(float(v), 6)
                    for feat, v in zip(FAILURE_FEATURES, vals)
                }
            except Exception as exc:
                logger.warning("failure_shap_failed", error=str(exc))

        # Top contributing features
        top_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

        diagnosis = {
            "failure_probability": round(failure_prob, 4),
            "top_contributing_features": [
                {"feature": f, "shap_value": s} for f, s in top_features
            ],
            "shap_values": shap_dict,
            "raw_error": gateway_error,
        }

        logger.info(
            "failure_diagnosed",
            failure_probability=failure_prob,
            top_feature=top_features[0][0] if top_features else "n/a",
        )
        return failure_prob, diagnosis
