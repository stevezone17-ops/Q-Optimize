"""Quantum solver and simulation package for Q-Optimize."""

from backend.app.solvers.quantum.config import (
    SimulationMode,
    QuantumBackendType,
    ClassicalOptimizerType,
    ParameterInitializationStrategy,
    QuantumResourceLimits,
    default_quantum_limits,
)
from backend.app.solvers.quantum.models import (
    QuantumBackendInfo,
    QAOAConfiguration,
    CircuitMetadata,
    QuantumConvergencePoint,
    QuantumExecutionStatus,
)
from backend.app.solvers.quantum.exceptions import (
    QuantumSolverError,
    BackendNotAvailableError,
    UnsupportedSimulationMethodError,
    QuantumResourceLimitExceeded,
    QubitLimitExceededError,
    ShotLimitExceededError,
    CircuitConstructionError,
    TranspilationError,
    ExecutionTimeoutError,
    CancellationError,
)
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.quantum_registry import QuantumSolverRegistry
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian, QAOAMixerHamiltonian

__all__ = [
    "SimulationMode",
    "QuantumBackendType",
    "ClassicalOptimizerType",
    "ParameterInitializationStrategy",
    "QuantumResourceLimits",
    "default_quantum_limits",
    "QuantumBackendInfo",
    "QAOAConfiguration",
    "CircuitMetadata",
    "QuantumConvergencePoint",
    "QuantumExecutionStatus",
    "QuantumSolverError",
    "BackendNotAvailableError",
    "UnsupportedSimulationMethodError",
    "QuantumResourceLimitExceeded",
    "QubitLimitExceededError",
    "ShotLimitExceededError",
    "CircuitConstructionError",
    "TranspilationError",
    "ExecutionTimeoutError",
    "CancellationError",
    "QuantumBackendManager",
    "QuantumSolverRegistry",
    "QuantumExecutionContext",
    "QAOACostHamiltonian",
    "QAOAMixerHamiltonian",
]
