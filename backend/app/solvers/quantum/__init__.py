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
    QAOAOptimizationResult,
    QuantumSamplingResult,
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
from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.optimizer import QAOAOptimizer
from backend.app.solvers.quantum.execution_engine import QuantumExecutionEngine

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
    "QAOACircuitBuilder",
    "QAOAOptimizer",
    "QAOAOptimizationResult",
    "QuantumExecutionEngine",
    "QuantumSamplingResult",
]
