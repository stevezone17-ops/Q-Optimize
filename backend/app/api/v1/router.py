"""V1 API Router aggregation."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    problems,
    formulations,
    experiments,
    classical_solvers,
    quantum_solvers,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(problems.router)
api_v1_router.include_router(formulations.router)
api_v1_router.include_router(experiments.router)
api_v1_router.include_router(classical_solvers.router, prefix="/solvers/classical", tags=["Classical Solvers"])
api_v1_router.include_router(quantum_solvers.router, prefix="/solvers/quantum", tags=["Quantum Solvers"])
