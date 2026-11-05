"""Classical optimization solver engine package."""

from backend.app.solvers.classical.models import (
    SolverStatus,
    OptimalityStatus,
    ConvergencePoint,
    SolverConfiguration,
    SolverMetadata,
    SolverRequest,
    SolverResult,
)
from backend.app.solvers.classical.base import IClassicalSolver
from backend.app.solvers.classical.exceptions import (
    ClassicalSolverError,
    SolverNotFoundError,
    SolverNotImplementedError,
    SolverConfigurationError,
    SolverTimeoutError,
    UnsupportedProblemTypeError,
)
from backend.app.solvers.classical.registry import ClassicalSolverRegistry
from backend.app.solvers.classical.factory import ClassicalSolverFactory

__all__ = [
    "SolverStatus",
    "OptimalityStatus",
    "ConvergencePoint",
    "SolverConfiguration",
    "SolverMetadata",
    "SolverRequest",
    "SolverResult",
    "IClassicalSolver",
    "ClassicalSolverError",
    "SolverNotFoundError",
    "SolverNotImplementedError",
    "SolverConfigurationError",
    "SolverTimeoutError",
    "UnsupportedProblemTypeError",
    "ClassicalSolverRegistry",
    "ClassicalSolverFactory",
]
