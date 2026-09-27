"""
GET /v1/transaction/{transaction_id}/explain

Returns the AI-generated failure explanation and SHAP values for a transaction.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.ml_result import MLResult
from app.models.schemas import ExplainerResponse
from app.models.transaction import Transaction

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/transaction/{transaction_id}/explain",
    response_model=ExplainerResponse,
    summary="Get AI-generated failure explanation",
    description=(
        "Returns the SHAP feature contributions and the LLM-generated "
        "human-readable explanation for why a transaction failed."
    ),
    tags=["Explainability"],
)
async def explain_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # Verify the transaction exists
    txn_result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = txn_result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )

    # Fetch the failure MLResult (most recent failure model record)
    ml_result_query = await db.execute(
        select(MLResult)
        .where(MLResult.transaction_id == transaction_id)
        .where(MLResult.model_name == "failure")
        .order_by(MLResult.created_at.desc())
    )
    ml_result = ml_result_query.scalar_one_or_none()

    if not ml_result:
        # Try fraud model as fallback
        ml_result_query = await db.execute(
            select(MLResult)
            .where(MLResult.transaction_id == transaction_id)
            .order_by(MLResult.created_at.desc())
        )
        ml_result = ml_result_query.scalar_one_or_none()

    if not ml_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ML result found for transaction {transaction_id}. "
                   "Ensure the transaction has been processed.",
        )

    explanation = ml_result.llm_explanation or (
        "No failure explanation available — this transaction was approved or rejected "
        "before a gateway call was attempted."
    )

    logger.info(
        "explanation_retrieved",
        transaction_id=str(transaction_id),
        model=ml_result.model_name,
    )

    return ExplainerResponse(
        transaction_id=transaction_id,
        failure_probability=ml_result.prediction,
        shap_values=ml_result.shap_values or {},
        llm_explanation=explanation,
        generated_at=ml_result.created_at,
    )
