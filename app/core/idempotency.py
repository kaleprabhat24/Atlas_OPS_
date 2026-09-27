"""
Redis-backed Idempotency Middleware for ATLAS-OPS.

On every POST request:
  1. Read the 'Idempotency-Key' header.
  2. If key exists in Redis → return the cached response.
  3. After handler completes → cache the response body in Redis (TTL = 24 h).

Only POST endpoints are subject to idempotency checks.
"""

import json
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.redis_client import get_redis_pool

logger = get_logger(__name__)

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Apply only to POST
        if request.method != "POST":
            return await call_next(request)

        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)

        if not idempotency_key:
            return await call_next(request)

        redis = get_redis_pool()
        if redis is None:
            # Redis unavailable — skip idempotency, process normally
            return await call_next(request)

        cache_key = f"idempotency:{idempotency_key}"

        # ── 1. CHECK CACHE ─────────────────────────────
        cached = await redis.get(cache_key)
        if cached:
            logger.info(
                "idempotency_cache_hit",
                idempotency_key=idempotency_key,
                path=request.url.path,
            )
            try:
                payload = json.loads(cached)

                # ✅ Safe copy
                body = payload.get("body", {})
                if isinstance(body, dict):
                    body = dict(body)  # avoid mutation
                    body["idempotency_cached"] = True

                return JSONResponse(
                    content=body,
                    status_code=payload.get("status_code", 200),
                    headers={"X-Idempotency-Cached": "true"},
                )
            except (json.JSONDecodeError, KeyError):
                logger.warning("corrupt_idempotency_cache", key=cache_key)

        # ── 2. PROCESS REQUEST ─────────────────────────
        response = await call_next(request)

        # Read response body
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        # ── 3. CACHE RESPONSE ──────────────────────────
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))

            if isinstance(body_json, dict):
                # ✅ ensure flag is False for fresh response
                body_json["idempotency_cached"] = False

                # update response body so client sees it immediately
                body_bytes = json.dumps(body_json).encode("utf-8")

            cache_payload = json.dumps(
                {
                    "status_code": response.status_code,
                    "body": body_json,
                }
            )

            await redis.setex(cache_key, IDEMPOTENCY_TTL, cache_payload)

            logger.info(
                "idempotency_response_cached",
                idempotency_key=idempotency_key,
                status_code=response.status_code,
                ttl=IDEMPOTENCY_TTL,
            )

        except Exception as exc:
            logger.warning(
                "idempotency_cache_write_failed",
                idempotency_key=idempotency_key,
                error=str(exc),
            )

        # ── 4. RETURN RESPONSE ─────────────────────────
        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )