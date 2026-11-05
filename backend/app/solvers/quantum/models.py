"""Domain models, configurations, and result schemas for quantum solvers."""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator
from backend.app.solvers.quantum.config import (
    SimulationMode,
    QuantumBackendType,
    ClassicalOptimizerType,
    ParameterInitializationStrategy,
    default_quantum_limits,
)


class QuantumBackendInfo(BaseModel):
    """Metadata descriptor for a quantum simulation backend."""
    backend_id: str
    name: str
    backend_type: QuantumBackendType
    is_simulator: bool = True
    is_hardware: bool = False
    hardware_transparency_note: str = (
        "Execution runs on classical quantum circuit simulation via Qiskit Aer. "
        "No physical quantum hardware speedup is claimed."
    )
    max_qubits: int
    supported_methods: List[str]
    is_available: bool = True
    qiskit_version: Optional[str] = None
    aer_version: Optional[str] = None


class QAOAConfiguration(BaseModel):
    """Execution hyperparameters and simulation configuration for QAOA."""
    p_depth: int = Field(1, ge=1, le=10, description="Number of QAOA alternating layers (p)")
    shots: int = Field(1024, ge=10, le=50000, description="Number of measurement shots")
    simulation_mode: SimulationMode = Field(
        SimulationMode.IDEAL_SHOTS,
        description="Target simulation mode: ideal_shots, statevector_exact, or noisy_simulation"
    )
    backend_name: str = Field("aer_simulator", description="Target backend identifier")
    optimizer: ClassicalOptimizerType = Field(
        ClassicalOptimizerType.COBYLA,
        description="Classical optimizer for the variational parameter loop"
    )
    max_iterations: int = Field(100, ge=1, le=500, description="Max optimizer iterations")
    optimizer_tol: Optional[float] = Field(1e-4, ge=1e-8, le=1.0, description="Optimizer tolerance")
    seed: Optional[int] = Field(42, description="Random seed for simulation and initialization")
    init_strategy: ParameterInitializationStrategy = Field(
        ParameterInitializationStrategy.RANDOM,
        description="Parameter initialization strategy"
    )
    initial_gamma: Optional[List[float]] = Field(None, description="Explicit initial gamma angles if strategy is custom")
    initial_beta: Optional[List[float]] = Field(None, description="Explicit initial beta angles if strategy is custom")
    noise_model_enabled: bool = Field(False, description="Whether to simulate depolarization/readout noise")
    noise_error_rate: float = Field(0.001, ge=0.0, le=0.1, description="Noise gate error probability")
    time_limit_seconds: float = Field(60.0, ge=1.0, le=600.0, description="Execution timeout in seconds")

    @field_validator("initial_gamma", "initial_beta")
    @classmethod
    def validate_custom_angles(cls, v: Optional[List[float]], info) -> Optional[List[float]]:
        # Checked in execution when p_depth is known
        return v


class CircuitMetadata(BaseModel):
    """Structural properties and gate statistics of a compiled QAOA quantum circuit."""
    num_qubits: int
    num_clbits: int
    p_depth: int
    total_gates: int
    two_qubit_gates: int
    circuit_depth: int
    parameter_count: int
    has_measurements: bool
    qubit_variable_map: Dict[int, str] = Field(default_factory=dict)


class QuantumConvergencePoint(BaseModel):
    """Single step along the classical variational parameter optimization trajectory."""
    iteration: int
    expected_energy: float
    best_expected_energy: float
    gamma: List[float]
    beta: List[float]
    eval_count: int
    timestamp_offset: float


class QuantumExecutionStatus(str, Enum):
    """Lifecycle status of a quantum simulation task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class QAOAOptimizationResult(BaseModel):
    """Output from the classical variational parameter optimization loop."""
    optimal_gamma: List[float]
    optimal_beta: List[float]
    best_expected_energy: float
    initial_expected_energy: float
    total_evaluations: int
    iterations: int
    convergence_history: List[QuantumConvergencePoint] = Field(default_factory=list)
    termination_reason: str
    evaluation_mode: str
    optimizer_name: str

