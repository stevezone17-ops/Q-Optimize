"""V1 API Router aggregation."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, problems, formulations, experiments

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(problems.router)
api_v1_router.include_router(formulations.router)
api_v1_router.include_router(experiments.router)
