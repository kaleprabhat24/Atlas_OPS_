"""
ATLAS-OPS Configuration
All settings are loaded from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "ATLAS-OPS"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/atlas_ops"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Fraud Detection ───────────────────────────────────────────────────────
    fraud_threshold: float = 0.65

    # ── Circuit Breaker ───────────────────────────────────────────────────────
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60

    # ── ML Model Paths ────────────────────────────────────────────────────────
    fraud_model_path: str = "app/ml_models/fraud_model.pkl"
    failure_model_path: str = "app/ml_models/failure_model.pkl"
    routing_model_path: str = "app/ml_models/routing_model.pkl"

    # ── OpenAI / LLM ─────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Gateway Base URLs ──────────────────────────────────────────────────────
    stripe_url: str = "https://api.stripe.com/mock"
    razorpay_url: str = "https://api.razorpay.com/mock"
    paypal_url: str = "https://api.paypal.com/mock"
    square_url: str = "https://api.squareup.com/mock"

    # ── Idempotency ───────────────────────────────────────────────────────────
    idempotency_ttl_seconds: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
