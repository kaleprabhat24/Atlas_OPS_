"""
Transaction SQLModel table definition.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, SQLModel
from sqlalchemy import DateTime



class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    idempotency_key: Optional[str] = Field(default=None, index=True, max_length=256)

    # ── Fraud Model Features ─────────────────────────────────────────────────
    amount: float = Field(ge=0)
    card1: int
    card2: int
    email_domain: str = Field(max_length=128)
    addr1: int
    addr2: int
    device_type: str = Field(max_length=64)
    device_info: str = Field(max_length=256)
    dist1: float
    dist2: float

    # ── Fraud Scores ─────────────────────────────────────────────────────────
    fraud_score: Optional[float] = Field(default=None)
    fraud_flag: Optional[bool] = Field(default=None)

    # ── Routing & Gateway ─────────────────────────────────────────────────────
    selected_gateway: Optional[str] = Field(default=None, max_length=64)
    gateway_response: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # ── Status & Timestamps ───────────────────────────────────────────────────
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )