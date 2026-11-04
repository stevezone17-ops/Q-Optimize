"""Solver interface specifications for classical and quantum solvers (Phases 4 & 5)."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field


class SolverResult(BaseModel):
    """Standardized result contract for all solvers."""
    solver_name: str
    solver_version: str
    candidate_solution: Any
    objective_value: float
    is_feasible: bool
    constraint_violations: list[str] = Field(default_factory=list)
    runtime_seconds: float
    iterations: int
    seed: int
    optimality_proven: bool = False
    termination_reason: str
    warnings: list[str] = Field(default_factory=list)


class ISolver(ABC):
    """Common solver contract for both classical algorithms and QAOA simulation."""

    @abstractmethod
    def solve(self, problem_instance: Dict[str, Any], config: Dict[str, Any], seed: int) -> SolverResult:
        raise NotImplementedError("Solvers are scheduled for Phases 4 and 5.")
