"""
MLResult SQLModel table — stores predictions, SHAP values and RAG explanations.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, SQLModel
from sqlalchemy import DateTime


class MLResult(SQLModel, table=True):
    __tablename__ = "ml_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    transaction_id: uuid.UUID = Field(index=True, foreign_key="transactions.id")

    model_name: str = Field(max_length=64)          # "fraud" | "failure" | "routing"
    prediction: float                                # raw model output (probability)
    confidence: float = Field(default=0.0)

    shap_values: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    raw_features: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    llm_explanation: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )