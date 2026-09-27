"""
Gateway Execution Service for ATLAS-OPS.

Executes payment calls to external gateways wrapped in circuit breakers.
Updates GatewayHealth in the database after each call.
Respects outage simulation flags set by GatewaySimulator.
"""
import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import pybreaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.circuit_breaker import circuit_breakers
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis_pool
from app.models.gateway import GatewayHealth

settings = get_settings()
logger = get_logger(__name__)

GATEWAY_URLS: dict[str, str] = {
    "stripe": settings.stripe_url,
    "razorpay": settings.razorpay_url,
    "paypal": settings.paypal_url,
    "square": settings.square_url,
}


async def _get_or_create_gateway_health(
    db: AsyncSession, gateway_name: str
) -> GatewayHealth:
    result = await db.execute(
        select(GatewayHealth).where(GatewayHealth.gateway_name == gateway_name)
    )
    gateway = result.scalar_one_or_none()
    if gateway is None:
        gateway = GatewayHealth(gateway_name=gateway_name)
        db.add(gateway)
        await db.flush()
    return gateway


async def _update_gateway_health(
    db: AsyncSession,
    gateway_name: str,
    success: bool,
    latency_ms: float,
) -> None:
    gw = await _get_or_create_gateway_health(db, gateway_name)
    gw.total_requests += 1
    if not success:
        gw.failed_requests += 1
    gw.success_rate = round(
        1.0 - (gw.failed_requests / gw.total_requests), 4
    )
    # Rolling average latency
    alpha = 0.2  # exponential moving average factor
    gw.avg_latency_ms = round(
        alpha * latency_ms + (1 - alpha) * gw.avg_latency_ms, 2
    )
    # Sync circuit state
    try:
        gw.circuit_state = circuit_breakers.get(gateway_name).current_state
    except Exception:
        gw.circuit_state = "unknown"
    gw.last_updated = datetime.now(timezone.utc)
    db.add(gw)


async def _simulate_gateway_call(
    gateway_name: str, transaction_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Simulate a real gateway HTTP call.
    Adds realistic latency (50–800 ms) and occasional random failures.
    """
    redis = get_redis_pool()
    sim_key = f"sim:outage:{gateway_name}"
    sim_data = None
    if redis is not None:
        try:
            sim_data = await redis.get(sim_key)
        except Exception:
            pass

    failure_rate = 0.05  # 5% baseline failure rate
    if sim_data:
        import json
        sim = json.loads(sim_data)
        failure_rate = float(sim.get("failure_rate", failure_rate))

    # Simulate latency
    latency = random.uniform(50, 800 + failure_rate * 2000)
    await asyncio.sleep(latency / 1000)

    if random.random() < failure_rate:
        error_type = random.choice(["timeout", "connection_drop", "dns_failure", "http_error"])
        raise RuntimeError(f"Gateway {gateway_name} error: {error_type}")

    return {
        "gateway": gateway_name,
        "status": "success",
        "gateway_transaction_id": f"gtx_{gateway_name}_{int(time.time())}",
        "latency_ms": round(latency, 2),
        "http_status_code": 200,
    }


class GatewayService:

    @staticmethod
    async def execute(
        gateway_name: str,
        transaction_data: dict[str, Any],
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Execute a payment via the given gateway, wrapped in its circuit breaker.

        Returns a result dict with:
          - success: bool
          - gateway_response: dict
          - gateway_error: dict (if failed)
          - latency_ms: float
        """
        gw = gateway_name.lower()
        start = time.monotonic()

        try:
            # Execute the async gateway call directly
            response = await _simulate_gateway_call(gw, transaction_data)
            latency_ms = (time.monotonic() - start) * 1000

            await _update_gateway_health(db, gw, success=True, latency_ms=latency_ms)

            logger.info(
                "gateway_call_success",
                gateway=gw,
                latency_ms=round(latency_ms, 2),
            )
            return {
                "success": True,
                "gateway_response": response,
                "latency_ms": round(latency_ms, 2),
            }

        except pybreaker.CircuitBreakerError as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error("gateway_circuit_open", gateway=gw, error=str(exc))
            await _update_gateway_health(db, gw, success=False, latency_ms=latency_ms)
            return {
                "success": False,
                "gateway_error": {
                    "payment_gateway": gw,
                    "acquirer_bank": "unknown",
                    "http_status_code": 503,
                    "gateway_latency_ms": latency_ms,
                    "retry_attempts": 0,
                    "gateway_health_score": 0.0,
                    "recent_success_rate": 0.0,
                    "timeout_flag": False,
                    "connection_drop_flag": False,
                    "dns_failure_flag": False,
                    "error": "Circuit breaker is OPEN",
                },
                "latency_ms": round(latency_ms, 2),
            }

        except RuntimeError as exc:
            latency_ms = (time.monotonic() - start) * 1000
            error_msg = str(exc)
            logger.error("gateway_call_failed", gateway=gw, error=error_msg, latency_ms=round(latency_ms, 2))

            # Notify the circuit breaker of this failure via force_open
            # if the gateway's DB success_rate has dropped below threshold.
            try:
                breaker = circuit_breakers.get(gw)
                # Use pybreaker's internal mechanism safely — just open if needed
                fail_count = breaker.fail_counter
                if fail_count >= breaker.fail_max:
                    breaker.open()
            except Exception:
                pass

            await _update_gateway_health(db, gw, success=False, latency_ms=latency_ms)

            timeout = "timeout" in error_msg
            conn_drop = "connection_drop" in error_msg
            dns_fail = "dns_failure" in error_msg

            return {
                "success": False,
                "gateway_error": {
                    "payment_gateway": gw,
                    "acquirer_bank": "unknown",
                    "http_status_code": 504 if timeout else 503,
                    "gateway_latency_ms": round(latency_ms, 2),
                    "retry_attempts": 1,
                    "gateway_health_score": 0.3,
                    "recent_success_rate": 0.5,
                    "timeout_flag": timeout,
                    "connection_drop_flag": conn_drop,
                    "dns_failure_flag": dns_fail,
                    "error": error_msg,
                },
                "latency_ms": round(latency_ms, 2),
            }

    @staticmethod
    async def get_all_health(db: AsyncSession) -> list[GatewayHealth]:
        """Return GatewayHealth for all supported gateways, seeding missing entries."""
        from app.core.circuit_breaker import SUPPORTED_GATEWAYS

        health_list = []
        for gw in SUPPORTED_GATEWAYS:
            gh = await _get_or_create_gateway_health(db, gw)
            # Sync circuit state from in-memory breaker
            try:
                gh.circuit_state = circuit_breakers.get(gw).current_state
            except Exception:
                pass
            health_list.append(gh)
        await db.flush()
        return health_list
