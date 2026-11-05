"""Classical optimization solver engine package."""

from backend.app.solvers.classical.models import (
    SolverStatus,
    OptimalityStatus,
    ConvergencePoint,
    SolverConfiguration,
    SolverMetadata,
    SolverRequest,
    SolverResult,
    ExecutionRecord,
    ExecutionStatusResponse,
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
from backend.app.solvers.classical.simulated_annealing import SimulatedAnnealingSolver
from backend.app.solvers.classical.execution import ClassicalExecutionPipeline
from backend.app.solvers.classical.benchmarking import (
    BenchmarkRequest,
    BenchmarkResult,
    SolverBenchmarkSummary,
    ClassicalBenchmarkEngine,
)

__all__ = [
    "SolverStatus",
    "OptimalityStatus",
    "ConvergencePoint",
    "SolverConfiguration",
    "SolverMetadata",
    "SolverRequest",
    "SolverResult",
    "ExecutionRecord",
    "ExecutionStatusResponse",
    "ClassicalExecutionPipeline",
    "BenchmarkRequest",
    "BenchmarkResult",
    "SolverBenchmarkSummary",
    "ClassicalBenchmarkEngine",
    "IClassicalSolver",
    "ExactSolver",
    "GeneticAlgorithmSolver",
    "SimulatedAnnealingSolver",
    "ClassicalSolverError",
    "SolverNotFoundError",
    "SolverNotImplementedError",
    "SolverConfigurationError",
    "SolverTimeoutError",
    "UnsupportedProblemTypeError",
    "ClassicalSolverRegistry",
    "ClassicalSolverFactory",
]
