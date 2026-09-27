"""
Pydantic v2 request / response schemas for ATLAS-OPS.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionStatus


# ───────────────────────────────────────────────────────────────────────────
# Transaction
# ───────────────────────────────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    """Payload for POST /v1/transaction/process"""

    amount: float = Field(gt=0, description="Transaction amount in USD")
    card1: int = Field(description="Card feature 1 (encoded card identifier)")
    card2: int = Field(description="Card feature 2")
    email_domain: str = Field(max_length=128, description="Purchaser email domain")
    addr1: int = Field(description="Billing address area code 1")
    addr2: int = Field(description="Billing address area code 2")
    device_type: str = Field(max_length=64, description="desktop | mobile | tablet")
    device_info: str = Field(max_length=256, description="Browser / OS string")
    dist1: float = Field(ge=0, description="Distance metric 1")
    dist2: float = Field(ge=0, description="Distance metric 2")

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        allowed = {"desktop", "mobile", "tablet"}
        if v.lower() not in allowed:
            raise ValueError(f"device_type must be one of {allowed}")
        return v.lower()


class FraudScoreDetail(BaseModel):
    fraud_probability: float
    fraud_flag: bool
    shap_values: dict[str, float]


class RoutingDetail(BaseModel):
    selected_gateway: str
    gateway_scores: dict[str, float]


class TransactionResponse(BaseModel):
    transaction_id: uuid.UUID
    status: TransactionStatus
    fraud_score: FraudScoreDetail
    routing: Optional[RoutingDetail] = None
    gateway_response: Optional[dict[str, Any]] = None
    failure_diagnosis: Optional[dict[str, Any]] = None
    explanation: Optional[str] = None
    idempotency_cached: bool = False
    processed_at: datetime


# ───────────────────────────────────────────────────────────────────────────
# Explainer
# ───────────────────────────────────────────────────────────────────────────

class ExplainerResponse(BaseModel):
    transaction_id: uuid.UUID
    failure_probability: Optional[float] = None
    shap_values: Optional[dict[str, float]] = None
    llm_explanation: str
    generated_at: datetime


# ───────────────────────────────────────────────────────────────────────────
# Gateway Health
# ───────────────────────────────────────────────────────────────────────────

class GatewayHealthItem(BaseModel):
    gateway_name: str
    total_requests: int
    failed_requests: int
    success_rate: float
    avg_latency_ms: float
    circuit_state: str
    last_updated: datetime


class GatewayHealthResponse(BaseModel):
    gateways: list[GatewayHealthItem]
    snapshot_at: datetime


# ───────────────────────────────────────────────────────────────────────────
# Outage Simulation
# ───────────────────────────────────────────────────────────────────────────

class SimulateOutageRequest(BaseModel):
    gateway: str = Field(description="Gateway to simulate (stripe | razorpay | paypal | square)")
    failure_rate: float = Field(ge=0.0, le=1.0, description="Probability of failure (0–1)")
    duration_seconds: int = Field(ge=1, le=3600, description="How long the simulation runs")

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v: str) -> str:
        allowed = {"stripe", "razorpay", "paypal", "square"}
        if v.lower() not in allowed:
            raise ValueError(f"gateway must be one of {allowed}")
        return v.lower()


class SimulateOutageResponse(BaseModel):
    gateway: str
    failure_rate: float
    duration_seconds: int
    circuit_opened: bool
    message: str


# ───────────────────────────────────────────────────────────────────────────
# Generic
# ───────────────────────────────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    status: str = "ok"
    service: str = "ATLAS-OPS"
    version: str = "1.0.0"
    timestamp: datetime
