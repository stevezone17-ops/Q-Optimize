"""Domain models, configurations, and result schemas for classical optimization solvers."""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator
from backend.app.domain.problems.models import ProblemType


class SolverStatus(str, Enum):
    """Execution lifecycle status of an optimization solver."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class OptimalityStatus(str, Enum):
    """Mathematical optimality status of a returned solution."""
    PROVEN_OPTIMAL = "proven_optimal"
    HEURISTIC_FEASIBLE = "heuristic_feasible"
    HEURISTIC_INFEASIBLE = "heuristic_infeasible"
    UNKNOWN = "unknown"


class ConvergencePoint(BaseModel):
    """Single checkpoint along an algorithm's convergence trajectory."""
    iteration: int = Field(..., description="Iteration or generation index")
    best_objective: float = Field(..., description="Best known objective value at this iteration")
    current_objective: Optional[float] = Field(None, description="Current solution objective value")
    mean_fitness: Optional[float] = Field(None, description="Average fitness of population (for GA)")
    temperature: Optional[float] = Field(None, description="Current system temperature (for SA)")
    timestamp_offset: Optional[float] = Field(None, description="Elapsed time in seconds since start")


class SolverConfiguration(BaseModel):
    """Base configuration parameters shared across all classical solvers."""
    time_limit_seconds: Optional[float] = Field(60.0, ge=0.1, le=3600.0, description="Max execution time in seconds")
    seed: Optional[int] = Field(42, description="Random seed for reproducible execution")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="Algorithm-specific parameter overrides")


class SolverMetadata(BaseModel):
    """Descriptor and discovery metadata for a registered solver."""
    solver_id: str
    name: str
    description: str
    supported_problem_types: List[ProblemType]
    is_implemented: bool
    stage_introduced: str
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    default_parameters: Dict[str, Any] = Field(default_factory=dict)


class SolverRequest(BaseModel):
    """Standardized invocation request for a classical optimization solver."""
    solver_id: str = Field(..., description="Identifier of the target solver (e.g. 'exact', 'genetic_algorithm')")
    problem_id: Optional[str] = Field(None, description="ID of a stored canonical problem in MongoDB")
    problem_type: Optional[ProblemType] = Field(None, description="Problem type if passing ad-hoc instance")
    instance: Optional[Dict[str, Any]] = Field(None, description="Ad-hoc instance definition if not using problem_id")
    config: Dict[str, Any] = Field(default_factory=dict, description="Solver configuration parameters")
    seed: Optional[int] = Field(42, description="Deterministic random seed")

    @field_validator("solver_id")
    @classmethod
    def validate_solver_id(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean:
            raise ValueError("solver_id cannot be empty")
        return clean


class SolverResult(BaseModel):
    """Standardized output contract returned by all classical solvers."""
    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:12]}")
    solver_id: str
    solver_name: str
    problem_type: ProblemType
    status: SolverStatus = SolverStatus.COMPLETED
    candidate_solution: Any = Field(..., description="Raw solution representation (e.g. partition, permutation, matching)")
    objective_value: Optional[float] = Field(None, description="Independently evaluated objective value")
    is_feasible: bool = Field(..., description="Whether solution satisfies all canonical constraints")
    constraint_violations: List[str] = Field(default_factory=list, description="Violation details from independent evaluator")
    runtime_seconds: float = Field(..., ge=0.0, description="Pure algorithmic solve time in seconds")
    iterations: int = Field(default=0, ge=0, description="Number of iterations or generations completed")
    evaluations: int = Field(default=0, ge=0, description="Total objective evaluations performed")
    seed: Optional[int] = None
    optimality_status: OptimalityStatus = OptimalityStatus.UNKNOWN
    termination_reason: str = Field(..., description="Why the solver stopped (e.g. 'optimal_found', 'max_iterations')")
    convergence_history: List[ConvergencePoint] = Field(default_factory=list, description="Convergence trace over iterations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Algorithm-specific internal metrics")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
