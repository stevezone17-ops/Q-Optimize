"""V1 API Router aggregation."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    health,
    problems,
    formulations,
    experiments,
    classical_solvers,
    quantum_solvers,
    adaptive_solvers,
    ai,
    benchmarks,
    analytics,
    datasets,
    exports,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router)

api_v1_router.include_router(health.router)
api_v1_router.include_router(problems.router)
api_v1_router.include_router(formulations.router)
api_v1_router.include_router(experiments.router)
api_v1_router.include_router(classical_solvers.router, prefix="/solvers/classical", tags=["Classical Solvers"])
api_v1_router.include_router(quantum_solvers.router, prefix="/solvers/quantum", tags=["Quantum Solvers"])
api_v1_router.include_router(adaptive_solvers.router, prefix="/solvers/quantum/adaptive", tags=["Adaptive Quantum Solvers"])
api_v1_router.include_router(ai.router)
api_v1_router.include_router(benchmarks.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(datasets.router)
api_v1_router.include_router(exports.router)
