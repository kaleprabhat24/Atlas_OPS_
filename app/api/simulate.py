"""
POST /v1/simulate/outage

Admin endpoint to simulate network instability for a given gateway.
Protected by X-Admin-Key header matching SECRET_KEY in settings.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.schemas import SimulateOutageRequest, SimulateOutageResponse
from app.services.gateway_simulator import GatewaySimulator

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


def _verify_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not x_admin_key or x_admin_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Admin-Key header.",
        )


@router.post(
    "/simulate/outage",
    response_model=SimulateOutageResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate a gateway outage",
    description=(
        "Admin-only. Injects failures into a gateway for a configurable "
        "duration. Failure rate >= 0.5 will also force-open the circuit breaker."
    ),
    tags=["Admin / Simulation"],
    dependencies=[Depends(_verify_admin)],
)
async def simulate_outage(
    payload: SimulateOutageRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.warning(
        "outage_simulation_requested",
        gateway=payload.gateway,
        failure_rate=payload.failure_rate,
        duration_seconds=payload.duration_seconds,
    )

    result = await GatewaySimulator.simulate_outage(
        gateway=payload.gateway,
        failure_rate=payload.failure_rate,
        duration_seconds=payload.duration_seconds,
    )

    return SimulateOutageResponse(**result)


@router.delete(
    "/simulate/outage/{gateway}",
    status_code=status.HTTP_200_OK,
    summary="Clear an active outage simulation",
    description="Admin-only. Removes the simulation flag and resets the circuit breaker.",
    tags=["Admin / Simulation"],
    dependencies=[Depends(_verify_admin)],
)
async def clear_outage(gateway: str):
    from app.core.circuit_breaker import SUPPORTED_GATEWAYS
    if gateway.lower() not in SUPPORTED_GATEWAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown gateway: {gateway}",
        )
    await GatewaySimulator.clear_simulation(gateway.lower())
    return {"message": f"Simulation cleared for gateway '{gateway}'."}
