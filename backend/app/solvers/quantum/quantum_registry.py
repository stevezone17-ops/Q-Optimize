"""Registry for quantum solvers and backend providers."""

from typing import Dict, Any, List, Optional
import logging
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.models import QuantumBackendInfo

logger = logging.getLogger(__name__)


class QuantumSolverRegistry:
    """Singleton registry tracking available quantum algorithms, solvers, and backends."""

    _instance: Optional["QuantumSolverRegistry"] = None

    def __init__(self):
        self._backend_manager = QuantumBackendManager()
        self._solvers: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> "QuantumSolverRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def backend_manager(self) -> QuantumBackendManager:
        return self._backend_manager

    def register_solver(self, solver_id: str, solver_class: Any) -> None:
        """Register a quantum solver implementation."""
        self._solvers[solver_id] = solver_class
        logger.info("Registered quantum solver '%s'", solver_id)

    def get_solver(self, solver_id: str) -> Any:
        """Retrieve a registered quantum solver."""
        if solver_id not in self._solvers:
            raise KeyError(
                f"Quantum solver '{solver_id}' not found. Registered: {list(self._solvers.keys())}"
            )
        return self._solvers[solver_id]

    def list_solvers(self) -> List[str]:
        """List registered quantum solver identifiers."""
        return list(self._solvers.keys())

    def list_backends(self) -> List[QuantumBackendInfo]:
        """List all available quantum execution backends."""
        return self._backend_manager.list_available_backends()
