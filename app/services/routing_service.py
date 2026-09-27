"""
Routing Service for ATLAS-OPS.

Selects the optimal payment gateway by running the routing model against
current gateway health metrics, excluding any gateway with an open circuit.
"""
from typing import Any

import numpy as np

from app.core.circuit_breaker import SUPPORTED_GATEWAYS, circuit_breakers
from app.core.logging import get_logger
from app.services.ml_loader import ROUTING_FEATURES, get_models, scale_features

logger = get_logger(__name__)


class RoutingService:

    @staticmethod
    def _build_feature_vector(
        gateway_name: str, health: dict[str, Any]
    ) -> np.ndarray:
        models = get_models()
        circuit_state_numeric = 0 if health.get("circuit_state") == "closed" else 1
        mapping = {
            "gateway_health_score": health.get("success_rate", 1.0),
            "recent_success_rate": health.get("success_rate", 1.0),
            "avg_latency_ms": health.get("avg_latency_ms", 0.0),
            "circuit_state_numeric": circuit_state_numeric,
            "total_requests": health.get("total_requests", 0),
        }

        # Apply standard scaling dynamically
        scaled_mapping = scale_features(models.standard_scaler, mapping)

        row = [float(scaled_mapping.get(f, 0.0)) for f in ROUTING_FEATURES]
        return np.array([row])

    @staticmethod
    async def select_gateway(gateway_health: dict[str, dict[str, Any]]) -> tuple[str, dict[str, float]]:
        """
        Select the best gateway.

        Args:
            gateway_health: {gateway_name: health_metrics_dict}

        Returns:
            (selected_gateway_name, {gateway: score})
        """
        models = get_models()
        cb_states = circuit_breakers.get_all_states()

        scores: dict[str, float] = {}

        for gw in SUPPORTED_GATEWAYS:
            # Skip gateways with an open circuit
            if cb_states.get(gw, {}).get("state") == "open":
                scores[gw] = -1.0
                logger.info("routing_skip_open_circuit", gateway=gw)
                continue

            health = gateway_health.get(gw, {})
            X = RoutingService._build_feature_vector(gw, health)

            try:
                proba = models.routing_model.predict_proba(X)[0]
                # Class 1 = "good route" probability
                score = float(proba[1]) if len(proba) > 1 else float(proba[0])
            except Exception as exc:
                logger.warning("routing_model_error", gateway=gw, error=str(exc))
                score = health.get("success_rate", 0.5)

            # Penalise high-latency gateways
            latency = health.get("avg_latency_ms", 0.0)
            if latency > 1000:
                score *= 0.8

            scores[gw] = round(score, 4)

        # Pick gateway with highest score
        eligible = {gw: s for gw, s in scores.items() if s >= 0}
        if not eligible:
            fallback = SUPPORTED_GATEWAYS[0]
            logger.warning("routing_all_circuits_open", fallback=fallback)
            return fallback, scores

        selected = max(eligible, key=lambda k: eligible[k])
        logger.info("routing_decision", selected_gateway=selected, scores=scores)
        return selected, scores
