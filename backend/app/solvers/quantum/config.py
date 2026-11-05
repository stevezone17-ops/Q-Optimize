"""Configuration enums, hardware descriptors, and resource bounds for quantum execution."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SimulationMode(str, Enum):
    """Execution simulation target."""
    IDEAL_SHOTS = "ideal_shots"
    STATEVECTOR_EXACT = "statevector_exact"
    NOISY_SIMULATION = "noisy_simulation"


class QuantumBackendType(str, Enum):
    """Quantum execution backend categorization."""
    AER_SIMULATOR = "aer_simulator"
    AER_STATEVECTOR = "aer_statevector"
    LOCAL_STATEVECTOR = "local_statevector"


class ClassicalOptimizerType(str, Enum):
    """Classical parameter optimizers for QAOA variational loop."""
    COBYLA = "COBYLA"
    SLSQP = "SLSQP"
    NELDER_MEAD = "Nelder-Mead"
    L_BFGS_B = "L-BFGS-B"


class ParameterInitializationStrategy(str, Enum):
    """Initialization strategy for QAOA variational parameters (gamma, beta)."""
    RANDOM = "random"
    ZEROS = "zeros"
    LINEAR_RAMP = "linear_ramp"
    CUSTOM = "custom"


class QuantumResourceLimits(BaseModel):
    """Hard ceiling boundaries on quantum simulation resource consumption."""
    max_qubits: int = Field(24, description="Maximum qubits allowed for shot-based simulation")
    max_statevector_qubits: int = Field(16, description="Maximum qubits allowed for statevector simulation")
    max_shots: int = Field(50000, description="Maximum allowable shots per circuit execution")
    min_shots: int = Field(10, description="Minimum allowable shots")
    max_p_depth: int = Field(10, description="Maximum QAOA layers (p)")
    max_optimizer_iterations: int = Field(500, description="Maximum iterations for variational parameter optimizer")
    default_timeout_seconds: float = Field(120.0, description="Default execution timeout")
    max_timeout_seconds: float = Field(600.0, description="Maximum allowable timeout in seconds")


default_quantum_limits = QuantumResourceLimits()
