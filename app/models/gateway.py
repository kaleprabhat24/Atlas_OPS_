"""
GatewayHealth SQLModel table — real-time health metrics per payment gateway.
"""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from sqlalchemy import Column, DateTime


class GatewayHealth(SQLModel, table=True):
    __tablename__ = "gateway_health"

    gateway_name: str = Field(primary_key=True, max_length=64)

    total_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)
    success_rate: float = Field(default=1.0)   # 0.0 – 1.0
    avg_latency_ms: float = Field(default=0.0)
    circuit_state: str = Field(default="closed", max_length=32)

    last_updated: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
