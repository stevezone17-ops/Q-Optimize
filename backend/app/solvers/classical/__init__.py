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
from backend.app.solvers.classical.exact import ExactSolver
from backend.app.solvers.classical.genetic_algorithm import GeneticAlgorithmSolver

__all__ = [
    "SolverStatus",
    "OptimalityStatus",
    "ConvergencePoint",
    "SolverConfiguration",
    "SolverMetadata",
    "SolverRequest",
    "SolverResult",
    "IClassicalSolver",
    "ExactSolver",
    "GeneticAlgorithmSolver",
    "ClassicalSolverError",
    "SolverNotFoundError",
    "SolverNotImplementedError",
    "SolverConfigurationError",
    "SolverTimeoutError",
    "UnsupportedProblemTypeError",
    "ClassicalSolverRegistry",
    "ClassicalSolverFactory",
]
