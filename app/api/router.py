"""
API Router — mounts all v1 endpoints under /v1 prefix.
"""
from fastapi import APIRouter

from app.api import explain, gateways, ml, pipeline, simulate, transaction

v1_router = APIRouter()

v1_router.include_router(transaction.router)
v1_router.include_router(pipeline.router)
v1_router.include_router(explain.router)
v1_router.include_router(gateways.router)
v1_router.include_router(simulate.router)
v1_router.include_router(ml.router)
