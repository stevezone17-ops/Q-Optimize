"""Registry for classical optimization solvers."""

from typing import Dict, Type, List, Optional, Any
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.base import IClassicalSolver
from backend.app.solvers.classical.models import SolverMetadata, SolverConfiguration, SolverResult
from backend.app.solvers.classical.exceptions import SolverNotFoundError, SolverNotImplementedError
from backend.app.solvers.classical.exact import ExactSolver
from backend.app.solvers.classical.genetic_algorithm import GeneticAlgorithmSolver


class SimulatedAnnealingStub(IClassicalSolver):
    """Stub representation of Simulated Annealing prior to Stage 4.4 implementation."""
    @property
    def solver_id(self) -> str:
        return "simulated_annealing"

    @property
    def name(self) -> str:
        return "Simulated Annealing (SA)"

    @property
    def description(self) -> str:
        return "Thermodynamic single-solution trajectory with Metropolis acceptance rule and geometric cooling schedules."

    @property
    def supported_problem_types(self) -> List[ProblemType]:
        return [ProblemType.MAX_CUT, ProblemType.ASSIGNMENT, ProblemType.TSP]

    @property
    def is_implemented(self) -> bool:
        return False

    @property
    def stage_introduced(self) -> str:
        return "Stage 4.4"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "initial_temperature": {"type": "float", "default": 100.0, "description": "Initial system temperature"},
            "final_temperature": {"type": "float", "default": 0.01, "description": "Stopping temperature"},
            "cooling_schedule": {"type": "string", "default": "exponential", "description": "Cooling schedule type"},
            "cooling_rate": {"type": "float", "default": 0.95, "description": "Geometric temperature decay factor"},
            "iterations_per_temperature": {"type": "integer", "default": 50, "description": "Steps at each temperature step"},
            "max_iterations": {"type": "integer", "default": 5000, "description": "Safety cutoff iteration count"},
            "seed": {"type": "integer", "default": 42, "description": "Deterministic random seed"},
            "time_limit_seconds": {"type": "float", "default": 60.0, "description": "Max execution time"},
        }

    def solve(
        self,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Optional[SolverConfiguration] = None,
        seed: Optional[int] = 42,
    ) -> SolverResult:
        super().solve(problem_type, instance, config, seed)


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
        cls.register(SimulatedAnnealingStub())


# Initialize default registry
ClassicalSolverRegistry.reset_defaults()
