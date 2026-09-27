"""
POST /v1/transaction/process
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.ml_result import MLResult
from app.models.schemas import (
    FraudScoreDetail,
    RoutingDetail,
    TransactionRequest,
    TransactionResponse,
)
from app.models.transaction import Transaction, TransactionStatus
from app.services.failure_service import FailureService
from app.services.fraud_service import FraudService
from app.services.gateway_service import GatewayService
from app.services.rag_explainer import RAGExplainerService
from app.services.routing_service import RoutingService

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.post("/transaction/process", response_model=TransactionResponse)
async def process_transaction(
    payload: TransactionRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    txn_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # ── Step 1: Fraud features ─────────────────────────────
    fraud_features = {
        "TransactionAmt": payload.amount,
        "card1": payload.card1,
        "card2": payload.card2,
        "P_emaildomain": payload.email_domain,
        "addr1": payload.addr1,
        "addr2": payload.addr2,
        "DeviceType": payload.device_type,
        "DeviceInfo": payload.device_info,
        "dist1": payload.dist1,
        "dist2": payload.dist2,
    }

    # ── Step 2: Fraud scoring ─────────────────────────────
    fraud_prob, fraud_shap = await FraudService.score(fraud_features)
    fraud_flag = fraud_prob >= settings.fraud_threshold

    # ── Step 3: Create transaction ────────────────────────
    transaction = Transaction(
        id=txn_id,
        idempotency_key=idempotency_key,
        amount=payload.amount,
        card1=payload.card1,
        card2=payload.card2,
        email_domain=payload.email_domain,
        addr1=payload.addr1,
        addr2=payload.addr2,
        device_type=payload.device_type,
        device_info=payload.device_info,
        dist1=payload.dist1,
        dist2=payload.dist2,
        fraud_score=fraud_prob,
        fraud_flag=fraud_flag,
    )

    db.add(transaction)
    await db.flush()  # ✅ critical

    # ── Step 4: Fraud rejection ───────────────────────────
    if fraud_flag:
        transaction.status = TransactionStatus.REJECTED

        db.add(
            MLResult(
                transaction_id=txn_id,
                model_name="fraud",
                prediction=fraud_prob,
                confidence=fraud_prob,
                shap_values=fraud_shap,
                raw_features=fraud_features,
            )
        )

        await db.commit()

        return TransactionResponse(
            transaction_id=txn_id,
            status=TransactionStatus.REJECTED,
            fraud_score=FraudScoreDetail(
                fraud_probability=round(fraud_prob, 4),
                fraud_flag=True,
                shap_values=fraud_shap,
            ),
            idempotency_cached=False,
            processed_at=now,
        )

    # ── Step 5: Routing ───────────────────────────────────
    all_health = await GatewayService.get_all_health(db)

    gateway_health_map = {
        gh.gateway_name: {
            "success_rate": gh.success_rate,
            "avg_latency_ms": gh.avg_latency_ms,
            "circuit_state": gh.circuit_state,
            "total_requests": gh.total_requests,
        }
        for gh in all_health
    }

    selected_gateway, gateway_scores = await RoutingService.select_gateway(
        gateway_health_map
    )
    transaction.selected_gateway = selected_gateway

    db.add(
        MLResult(
            transaction_id=txn_id,
            model_name="routing",
            prediction=gateway_scores.get(selected_gateway, 0.0),
            confidence=gateway_scores.get(selected_gateway, 0.0),
            raw_features=gateway_health_map.get(selected_gateway, {}),
        )
    )

    # ── Step 6: Execute payment ───────────────────────────
    gateway_result = await GatewayService.execute(
        selected_gateway, fraud_features, db
    )

    if gateway_result["success"]:
        transaction.status = TransactionStatus.APPROVED
        transaction.gateway_response = gateway_result["gateway_response"]

        await db.commit()

        return TransactionResponse(
            transaction_id=txn_id,
            status=TransactionStatus.APPROVED,
            fraud_score=FraudScoreDetail(
                fraud_probability=round(fraud_prob, 4),
                fraud_flag=False,
                shap_values=fraud_shap,
            ),
            routing=RoutingDetail(
                selected_gateway=selected_gateway,
                gateway_scores=gateway_scores,
            ),
            gateway_response=gateway_result["gateway_response"],
            idempotency_cached=False,
            processed_at=now,
        )

    # ── Step 7: Failure flow ──────────────────────────────
    gateway_error = gateway_result.get("gateway_error", {})

    failure_prob, diagnosis = await FailureService.diagnose(
        gateway_error, fraud_shap
    )

    explanation = await RAGExplainerService.explain(
        transaction_id=str(txn_id),
        shap_values={**fraud_shap, **diagnosis.get("shap_values", {})},
        gateway_error=gateway_error,
        gateway=selected_gateway,
    )

    transaction.status = TransactionStatus.FAILED
    transaction.gateway_response = gateway_error

    db.add(
        MLResult(
            transaction_id=txn_id,
            model_name="failure",
            prediction=failure_prob,
            confidence=failure_prob,
            shap_values=diagnosis.get("shap_values"),
            raw_features=gateway_error,
            llm_explanation=explanation,
        )
    )

    await db.commit()

    return TransactionResponse(
        transaction_id=txn_id,
        status=TransactionStatus.FAILED,
        fraud_score=FraudScoreDetail(
            fraud_probability=round(fraud_prob, 4),
            fraud_flag=False,
            shap_values=fraud_shap,
        ),
        routing=RoutingDetail(
            selected_gateway=selected_gateway,
            gateway_scores=gateway_scores,
        ),
        gateway_response=gateway_error,
        failure_diagnosis=diagnosis,
        explanation=explanation,
        idempotency_cached=False,
        processed_at=now,
    )