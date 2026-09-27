"""
Gateway Outage Simulator for ATLAS-OPS.

Sets a Redis key that gateway_service.py reads to inject artificial failure
rates into gateway calls, enabling realistic resilience testing.
"""
import json
from datetime import datetime, timezone

from app.core.circuit_breaker import circuit_breakers
from app.core.logging import get_logger
from app.core.redis_client import get_redis_pool

logger = get_logger(__name__)


class GatewaySimulator:

    @staticmethod
    async def simulate_outage(
        gateway: str,
        failure_rate: float,
        duration_seconds: int,
    ) -> dict:
        """
        Simulate a gateway outage.

        Args:
            gateway: gateway name (stripe | razorpay | paypal | square)
            failure_rate: probability of failure per call (0.0 – 1.0)
            duration_seconds: how long the simulation runs

        Returns:
            confirmation dict
        """
        redis = get_redis_pool()
        sim_key = f"sim:outage:{gateway}"

        payload = json.dumps({
            "gateway": gateway,
            "failure_rate": failure_rate,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_seconds,
        })

        await redis.setex(sim_key, duration_seconds, payload)

        # If failure_rate > 0.5 → also force-open the circuit breaker
        circuit_opened = False
        if failure_rate >= 0.5:
            try:
                circuit_breakers.force_open(gateway)
                circuit_opened = True
            except Exception as exc:
                logger.warning("sim_circuit_open_failed", gateway=gateway, error=str(exc))

        logger.warning(
            "outage_simulation_started",
            gateway=gateway,
            failure_rate=failure_rate,
            duration_seconds=duration_seconds,
            circuit_opened=circuit_opened,
        )

        return {
            "gateway": gateway,
            "failure_rate": failure_rate,
            "duration_seconds": duration_seconds,
            "circuit_opened": circuit_opened,
            "message": (
                f"Outage simulation active for '{gateway}' for {duration_seconds}s "
                f"at {failure_rate*100:.0f}% failure rate."
                + (" Circuit breaker force-opened." if circuit_opened else "")
            ),
        }

    @staticmethod
    async def clear_simulation(gateway: str) -> None:
        """Remove an active outage simulation and reset the circuit."""
        redis = get_redis_pool()
        await redis.delete(f"sim:outage:{gateway}")
        try:
            circuit_breakers.force_close(gateway)
        except Exception:
            pass
        logger.info("outage_simulation_cleared", gateway=gateway)
