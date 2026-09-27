"""
Machine Learning Endpoints
"""
from fastapi import APIRouter
from sklearn.dummy import DummyClassifier

from app.services.ml_loader import get_models

router = APIRouter()

@router.get("/ml/status", tags=["ML Status"])
async def ml_status():
    models = get_models()
    return {
        "fraud_model": "fallback" if isinstance(models.fraud_model, DummyClassifier) else "loaded",
        "routing_model": "fallback" if isinstance(models.routing_model, DummyClassifier) else "loaded",
        "failure_model": "fallback" if isinstance(models.failure_model, DummyClassifier) else "loaded",
    }
