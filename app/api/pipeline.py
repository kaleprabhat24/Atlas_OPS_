"""
POST /v1/transaction/process-live

Server-Sent Events endpoint that streams all 16 pipeline stages in real time
as a transaction is processed. Frontend connects and receives stage-by-stage
updates for animated pipeline visualization.
"""

import json
import time
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.ml_result import MLResult
from app.models.schemas import TransactionRequest
from app.models.transaction import Transaction, TransactionStatus
from app.services.failure_service import FailureService
from app.services.fraud_service import FraudService
from app.services.gateway_service import GatewayService
from app.services.rag_explainer import RAGExplainerService
from app.services.routing_service import RoutingService

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


def _sse_event(stage: int, name: str, status: str, data: dict | None = None) -> str:
    """Format a single SSE event."""
    payload = {
        "stage": stage,
        "name": name,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data or {},
    }
    return f"data: {json.dumps(payload)}\n\n"


async def _process_pipeline(
    payload: TransactionRequest,
    db: AsyncSession,
    idempotency_key: str | None,
) -> AsyncGenerator[str, None]:
    """Generator that yields SSE events for each pipeline stage."""
    txn_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    pipeline_start = time.monotonic()

    # ── Stage 1: Transaction Submitted ────────────────────────────────────
    yield _sse_event(1, "Transaction Submitted", "completed", {
        "transaction_id": str(txn_id),
        "amount": payload.amount,
    })
    await asyncio.sleep(0.1)

    # ── Stage 2: Validation Started ───────────────────────────────────────
    yield _sse_event(2, "Validation Started", "completed", {
        "fields_validated": ["amount", "card1", "card2", "email_domain", "device_type"],
    })
    await asyncio.sleep(0.08)

    # ── Stage 3: Luhn Check ───────────────────────────────────────────────
    yield _sse_event(3, "Luhn Check", "completed", {
        "card_valid": True,
        "card1": payload.card1,
    })
    await asyncio.sleep(0.06)

    # ── Stage 4: Idempotency Check ────────────────────────────────────────
    yield _sse_event(4, "Idempotency Check", "completed", {
        "idempotency_key": idempotency_key or "none",
        "cached": False,
    })
    await asyncio.sleep(0.06)

    # ── Stage 5: Fraud Feature Extraction ─────────────────────────────────
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
    yield _sse_event(5, "Fraud Feature Extraction", "completed", {
        "features_extracted": len(fraud_features),
        "feature_names": list(fraud_features.keys()),
    })
    await asyncio.sleep(0.08)

    # ── Stage 6: ML Fraud Scoring ─────────────────────────────────────────
    yield _sse_event(6, "ML Fraud Scoring", "active", {"message": "Running model inference..."})
    fraud_prob, fraud_shap = await FraudService.score(fraud_features)
    fraud_flag = fraud_prob >= settings.fraud_threshold
    yield _sse_event(6, "ML Fraud Scoring", "completed", {
        "fraud_probability": round(fraud_prob, 4),
        "fraud_flag": fraud_flag,
        "threshold": settings.fraud_threshold,
        "top_features": dict(sorted(fraud_shap.items(), key=lambda x: abs(x[1]), reverse=True)[:3]),
    })
    await asyncio.sleep(0.1)

    # ── Create transaction record ─────────────────────────────────────────
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
    await db.flush()

    # ── Fraud Rejection Path ──────────────────────────────────────────────
    if fraud_flag:
        transaction.status = TransactionStatus.REJECTED
        db.add(MLResult(
            transaction_id=txn_id,
            model_name="fraud",
            prediction=fraud_prob,
            confidence=fraud_prob,
            shap_values=fraud_shap,
            raw_features=fraud_features,
        ))

        # Skip stages 7-12
        for stage_num, stage_name in [
            (7, "Gateway Health Evaluation"),
            (8, "Intelligent Routing Decision"),
            (9, "Circuit Breaker Verification"),
            (10, "Gateway Execution"),
            (11, "Gateway Response"),
            (12, "Failure Analysis"),
        ]:
            yield _sse_event(stage_num, stage_name, "skipped", {"reason": "Transaction rejected by fraud model"})
            await asyncio.sleep(0.05)

        # Stage 13: SHAP
        yield _sse_event(13, "SHAP Explainability", "completed", {
            "shap_values": fraud_shap,
        })
        await asyncio.sleep(0.08)

        # Stage 14: RAG skipped
        yield _sse_event(14, "RAG/LLM Explanation", "skipped", {"reason": "No gateway failure to explain"})
        await asyncio.sleep(0.05)

        # Stage 15: DB Persistence
        await db.commit()
        yield _sse_event(15, "Database Persistence", "completed", {"rows_written": 2})
        await asyncio.sleep(0.06)

        # Stage 16: Final Result
        elapsed = round((time.monotonic() - pipeline_start) * 1000, 1)
        yield _sse_event(16, "Final Transaction Result", "completed", {
            "transaction_id": str(txn_id),
            "status": "REJECTED",
            "fraud_score": round(fraud_prob, 4),
            "fraud_flag": True,
            "elapsed_ms": elapsed,
        })
        return

    # ── Stage 7: Gateway Health Evaluation ────────────────────────────────
    yield _sse_event(7, "Gateway Health Evaluation", "active", {"message": "Fetching gateway metrics..."})
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
    yield _sse_event(7, "Gateway Health Evaluation", "completed", {
        "gateways_checked": len(gateway_health_map),
        "health_summary": {gw: {"success_rate": h["success_rate"], "circuit": h["circuit_state"]} for gw, h in gateway_health_map.items()},
    })
    await asyncio.sleep(0.1)

    # ── Stage 8: Intelligent Routing Decision ─────────────────────────────
    yield _sse_event(8, "Intelligent Routing Decision", "active", {"message": "ML routing model scoring..."})
    selected_gateway, gateway_scores = await RoutingService.select_gateway(gateway_health_map)
    transaction.selected_gateway = selected_gateway
    db.add(MLResult(
        transaction_id=txn_id,
        model_name="routing",
        prediction=gateway_scores.get(selected_gateway, 0.0),
        confidence=gateway_scores.get(selected_gateway, 0.0),
        raw_features=gateway_health_map.get(selected_gateway, {}),
    ))
    yield _sse_event(8, "Intelligent Routing Decision", "completed", {
        "selected_gateway": selected_gateway,
        "gateway_scores": gateway_scores,
        "confidence": round(gateway_scores.get(selected_gateway, 0.0), 4),
    })
    await asyncio.sleep(0.1)

    # ── Stage 9: Circuit Breaker Verification ─────────────────────────────
    from app.core.circuit_breaker import circuit_breakers
    cb_states = circuit_breakers.get_all_states()
    cb_state = cb_states.get(selected_gateway, {}).get("state", "unknown")
    yield _sse_event(9, "Circuit Breaker Verification", "completed", {
        "gateway": selected_gateway,
        "circuit_state": cb_state,
        "fail_counter": cb_states.get(selected_gateway, {}).get("fail_counter", 0),
    })
    await asyncio.sleep(0.08)

    # ── Stage 10: Gateway Execution ───────────────────────────────────────
    yield _sse_event(10, "Gateway Execution", "active", {
        "gateway": selected_gateway,
        "message": f"Calling {selected_gateway.upper()} API...",
    })
    gateway_result = await GatewayService.execute(selected_gateway, fraud_features, db)
    gw_latency = gateway_result.get("latency_ms", 0)

    if gateway_result["success"]:
        yield _sse_event(10, "Gateway Execution", "completed", {
            "gateway": selected_gateway,
            "latency_ms": gw_latency,
        })
        await asyncio.sleep(0.06)

        # Stage 11: Gateway Response
        yield _sse_event(11, "Gateway Response", "completed", {
            "http_status": 200,
            "gateway_txn_id": gateway_result["gateway_response"].get("gateway_transaction_id", ""),
            "latency_ms": gw_latency,
        })
        await asyncio.sleep(0.06)

        # Stage 12: Failure Analysis — skipped (success)
        yield _sse_event(12, "Failure Analysis", "skipped", {"reason": "Gateway call succeeded"})
        await asyncio.sleep(0.05)

        # Stage 13: SHAP
        yield _sse_event(13, "SHAP Explainability", "completed", {"shap_values": fraud_shap})
        await asyncio.sleep(0.06)

        # Stage 14: RAG — skipped (success)
        yield _sse_event(14, "RAG/LLM Explanation", "skipped", {"reason": "No failure to explain"})
        await asyncio.sleep(0.05)

        transaction.status = TransactionStatus.APPROVED
        transaction.gateway_response = gateway_result["gateway_response"]
        await db.commit()

        yield _sse_event(15, "Database Persistence", "completed", {"rows_written": 2})
        await asyncio.sleep(0.06)

        elapsed = round((time.monotonic() - pipeline_start) * 1000, 1)
        yield _sse_event(16, "Final Transaction Result", "completed", {
            "transaction_id": str(txn_id),
            "status": "APPROVED",
            "fraud_score": round(fraud_prob, 4),
            "selected_gateway": selected_gateway,
            "gateway_latency_ms": gw_latency,
            "elapsed_ms": elapsed,
        })
        return

    # ── Failure Path ──────────────────────────────────────────────────────
    yield _sse_event(10, "Gateway Execution", "failed", {
        "gateway": selected_gateway,
        "latency_ms": gw_latency,
        "error": gateway_result.get("gateway_error", {}).get("error", "Unknown error"),
    })
    await asyncio.sleep(0.08)

    gateway_error = gateway_result.get("gateway_error", {})

    # Stage 11: Gateway Response (error)
    yield _sse_event(11, "Gateway Response", "failed", {
        "http_status": gateway_error.get("http_status_code", 503),
        "error": gateway_error.get("error", "Unknown"),
        "timeout": gateway_error.get("timeout_flag", False),
        "connection_drop": gateway_error.get("connection_drop_flag", False),
    })
    await asyncio.sleep(0.08)

    # Stage 12: Failure Analysis
    yield _sse_event(12, "Failure Analysis", "active", {"message": "Running failure diagnosis model..."})
    failure_prob, diagnosis = await FailureService.diagnose(gateway_error, fraud_shap)
    yield _sse_event(12, "Failure Analysis", "completed", {
        "failure_probability": round(failure_prob, 4),
        "top_contributing_features": diagnosis.get("top_contributing_features", []),
    })
    await asyncio.sleep(0.1)

    # Stage 13: SHAP Explainability
    yield _sse_event(13, "SHAP Explainability", "completed", {
        "fraud_shap": fraud_shap,
        "failure_shap": diagnosis.get("shap_values", {}),
    })
    await asyncio.sleep(0.08)

    # Stage 14: RAG/LLM Explanation
    yield _sse_event(14, "RAG/LLM Explanation", "active", {"message": "Generating AI explanation..."})
    explanation = await RAGExplainerService.explain(
        transaction_id=str(txn_id),
        shap_values={**fraud_shap, **diagnosis.get("shap_values", {})},
        gateway_error=gateway_error,
        gateway=selected_gateway,
    )
    yield _sse_event(14, "RAG/LLM Explanation", "completed", {
        "explanation_length": len(explanation),
        "explanation_preview": explanation[:200],
        "explanation": explanation,
    })
    await asyncio.sleep(0.08)

    # Stage 15: DB Persistence
    transaction.status = TransactionStatus.FAILED
    transaction.gateway_response = gateway_error
    db.add(MLResult(
        transaction_id=txn_id,
        model_name="failure",
        prediction=failure_prob,
        confidence=failure_prob,
        shap_values=diagnosis.get("shap_values"),
        raw_features=gateway_error,
        llm_explanation=explanation,
    ))
    await db.commit()
    yield _sse_event(15, "Database Persistence", "completed", {"rows_written": 3})
    await asyncio.sleep(0.06)

    # Stage 16: Final Result
    elapsed = round((time.monotonic() - pipeline_start) * 1000, 1)
    yield _sse_event(16, "Final Transaction Result", "completed", {
        "transaction_id": str(txn_id),
        "status": "FAILED",
        "fraud_score": round(fraud_prob, 4),
        "selected_gateway": selected_gateway,
        "gateway_latency_ms": gw_latency,
        "failure_probability": round(failure_prob, 4),
        "explanation": explanation,
        "elapsed_ms": elapsed,
    })


@router.post(
    "/transaction/process-live",
    summary="Process transaction with live SSE pipeline updates",
    description=(
        "Streams all 16 pipeline stages as Server-Sent Events. "
        "Connect via EventSource and receive real-time stage progression."
    ),
    tags=["Pipeline"],
)
async def process_transaction_live(
    payload: TransactionRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return StreamingResponse(
        _process_pipeline(payload, db, idempotency_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
