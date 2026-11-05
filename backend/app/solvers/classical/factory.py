"""Factory for creating and resolving classical solvers."""

from typing import List
from backend.app.solvers.classical.base import IClassicalSolver
from backend.app.solvers.classical.models import SolverMetadata
from backend.app.solvers.classical.registry import ClassicalSolverRegistry


class ClassicalSolverFactory:
    """Factory service for discovering and resolving classical solvers."""

    @staticmethod
    def get_solver(solver_id: str) -> IClassicalSolver:
        """Resolve a solver by its identifier."""
        return ClassicalSolverRegistry.get(solver_id)

    @staticmethod
    def list_solvers() -> List[SolverMetadata]:
        """List metadata for all registered classical solvers."""
        return ClassicalSolverRegistry.list_all()

