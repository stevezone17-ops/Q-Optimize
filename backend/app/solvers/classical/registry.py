"""Registry for classical optimization solvers."""

from typing import Dict, Type, List, Optional, Any
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.base import IClassicalSolver
from backend.app.solvers.classical.models import SolverMetadata, SolverConfiguration, SolverResult
from backend.app.solvers.classical.exceptions import SolverNotFoundError, SolverNotImplementedError
from backend.app.solvers.classical.exact import ExactSolver
from backend.app.solvers.classical.genetic_algorithm import GeneticAlgorithmSolver
from backend.app.solvers.classical.simulated_annealing import SimulatedAnnealingSolver


class ClassicalSolverRegistry:
    """Central registry for discovering, registering, and retrieving classical solvers."""

    _solvers: Dict[str, IClassicalSolver] = {}

    @classmethod
    def register(cls, solver: IClassicalSolver) -> None:
        """Register a solver instance."""
        cls._solvers[solver.solver_id.lower()] = solver

    @classmethod
    def get(cls, solver_id: str) -> IClassicalSolver:
        """Retrieve a solver by ID, raising SolverNotFoundError if missing."""
        clean_id = solver_id.strip().lower()
        if clean_id not in cls._solvers:
            available = list(cls._solvers.keys())
            raise SolverNotFoundError(
                f"Classical solver '{solver_id}' not found in registry. Available solvers: {available}"
            )
        return cls._solvers[clean_id]

    @classmethod
    def list_all(cls) -> List[SolverMetadata]:
        """Return discovery metadata for all registered solvers."""
        return [solver.get_metadata() for solver in cls._solvers.values()]

    @classmethod
    def reset_defaults(cls) -> None:
        """Reset registry to default built-in solvers."""
        cls._solvers.clear()
        cls.register(ExactSolver())
        cls.register(GeneticAlgorithmSolver())
        cls.register(SimulatedAnnealingSolver())


# Initialize default registry
ClassicalSolverRegistry.reset_defaults()
