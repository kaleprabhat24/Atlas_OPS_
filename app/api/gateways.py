"""
GET /v1/gateways/health

Real-time dashboard of gateway success rates, latency, and circuit states.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit_breaker import circuit_breakers
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.schemas import GatewayHealthItem, GatewayHealthResponse
from app.services.gateway_service import GatewayService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/gateways/health",
    response_model=GatewayHealthResponse,
    summary="Real-time gateway health dashboard",
    description=(
        "Returns success rates, average latency, and circuit breaker state "
        "for all supported payment gateways."
    ),
    tags=["Gateways"],
)
async def get_gateways_health(db: AsyncSession = Depends(get_db)):
    health_records = await GatewayService.get_all_health(db)
    cb_states = circuit_breakers.get_all_states()

    items = []
    for gh in health_records:
        # Merge live circuit state
        live_state = cb_states.get(gh.gateway_name, {}).get("state", gh.circuit_state)
        items.append(
            GatewayHealthItem(
                gateway_name=gh.gateway_name,
                total_requests=gh.total_requests,
                failed_requests=gh.failed_requests,
                success_rate=gh.success_rate,
                avg_latency_ms=gh.avg_latency_ms,
                circuit_state=live_state,
                last_updated=gh.last_updated,
            )
        )

    logger.info("gateway_health_fetched", gateway_count=len(items))
    return GatewayHealthResponse(
        gateways=items,
        snapshot_at=datetime.now(timezone.utc),
    )
