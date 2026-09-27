"""
ATLAS-OPS — FastAPI Application Entrypoint

Startup sequence:
  1. Structured logging
  2. Redis pool
  3. Circuit breakers
  4. ML model loading
  5. DB table creation
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import v1_router
from app.core.circuit_breaker import circuit_breakers
from app.core.config import get_settings
from app.core.database import create_all_tables
from app.core.idempotency import IdempotencyMiddleware
from app.core.logging import get_logger, setup_logging
from app.core.redis_client import close_redis, init_redis
from app.models.schemas import HealthCheckResponse
from app.services.ml_loader import load_all_models

settings = get_settings()

# Setup logging before anything else
setup_logging(log_level="DEBUG" if settings.app_env == "development" else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("atlas_ops_starting", env=settings.app_env)

    # 1. Redis
    await init_redis()
    logger.info("Redis connected")

    # 2. Circuit breakers
    circuit_breakers.initialise()
    logger.info("circuit_breakers_ready")

    # 3. ML models
    load_all_models()
    logger.info("ML models loaded")

    # 4. Database tables
    await create_all_tables()
    logger.info("Database connected")

    logger.info("atlas_ops_ready", host="0.0.0.0", port=8000)
    yield

    # Shutdown
    logger.info("atlas_ops_shutting_down")
    await close_redis()
    logger.info("atlas_ops_stopped")


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ATLAS-OPS",
    description=(
        "Autonomous AI-Driven Payment Operations Platform.\n\n"
        "Chains Fraud Detection → Intelligent Routing → Payment Execution → "
        "Failure Diagnosis → RAG-powered Merchant Explanation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(IdempotencyMiddleware)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(v1_router, prefix="/v1")


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Service health check",
)
async def health_check():
    return HealthCheckResponse(timestamp=datetime.now(timezone.utc))
