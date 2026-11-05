"""Abstract base interface for all classical optimization algorithms."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.models import (
    SolverConfiguration,
    SolverResult,
    SolverMetadata,
)
from backend.app.solvers.classical.exceptions import (
    UnsupportedProblemTypeError,
    SolverNotImplementedError,
)


class IClassicalSolver(ABC):
    """Abstract interface defining the standardized contract for classical solvers."""

    @property
    @abstractmethod
    def solver_id(self) -> str:
        """Unique lowercase identifier for the solver (e.g. 'exact', 'genetic_algorithm')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the solver."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief scientific description of the solver algorithm."""
        pass

    @property
    @abstractmethod
    def supported_problem_types(self) -> List[ProblemType]:
        """List of ProblemTypes that this solver is equipped to solve."""
        pass

    @property
    @abstractmethod
    def is_implemented(self) -> bool:
        """Whether this solver algorithm is actively implemented and executable."""
        pass

    @property
    def stage_introduced(self) -> str:
        """Phase 4 development stage where this algorithm is implemented."""
        return "Stage 4.1"

    def get_metadata(self) -> SolverMetadata:
        """Generate discovery metadata for this solver."""
        return SolverMetadata(
            solver_id=self.solver_id,
            name=self.name,
            description=self.description,
            supported_problem_types=self.supported_problem_types,
            is_implemented=self.is_implemented,
            stage_introduced=self.stage_introduced,
            config_schema=self.get_config_schema(),
            default_parameters=self.get_default_parameters(),
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON-schema or parameter description for this solver's configuration."""
        return {
            "time_limit_seconds": {"type": "float", "default": 60.0, "description": "Max execution time"},
            "seed": {"type": "integer", "default": 42, "description": "Deterministic random seed"},
        }

    def get_default_parameters(self) -> Dict[str, Any]:
        """Return dictionary of default parameter values."""
        return {
            "time_limit_seconds": 60.0,
            "seed": 42,
        }

    def validate_config(self, config: Dict[str, Any]) -> SolverConfiguration:
        """Validate and parse user-provided configuration dictionary."""
        return SolverConfiguration(**config)

    def check_problem_support(self, problem_type: ProblemType) -> None:
        """Raise an exception if the problem type is not supported by this solver."""
        if problem_type not in self.supported_problem_types:
            raise UnsupportedProblemTypeError(
                f"Solver '{self.solver_id}' does not support problem type '{problem_type.value}'. "
                f"Supported types: {[pt.value for pt in self.supported_problem_types]}"
            )

    @abstractmethod
    def solve(
        self,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Optional[SolverConfiguration] = None,
        seed: Optional[int] = 42,
    ) -> SolverResult:
        """Execute the optimization algorithm and return standardized result."""
        if not self.is_implemented:
            raise SolverNotImplementedError(
                f"Solver '{self.solver_id}' is scheduled for implementation in {self.stage_introduced}. "
                "Current stage: Stage 4.1 (Architecture & Interfaces)."
            )
        self.check_problem_support(problem_type)
        raise NotImplementedError("Subclasses must implement solve().")

