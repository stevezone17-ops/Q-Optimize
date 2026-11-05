"""Domain models, configurations, and result schemas for Adaptive QAOA research."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, model_validator
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.quantum.config import (
    SimulationMode,
    ClassicalOptimizerType,
    QuantumBackendType,
)
from backend.app.solvers.quantum.models import (
    CircuitMetadata,
    QuantumExecutionStatus,
)
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    InitializationStrategyType,
    DepthGrowthStrategy,
    StoppingConditionType,
    OptimizerScheduleType,
)


class AdaptiveStrategyConfiguration(BaseModel):
    """Hyperparameters governing adaptive QAOA strategies."""
    strategy_type: AdaptiveStrategyType = Field(
        AdaptiveStrategyType.FULL_ADAPTIVE,
        description="Core adaptive strategy mode"
    )
    init_strategy: InitializationStrategyType = Field(
        InitializationStrategyType.LINEAR_RAMP,
        description="Initial parameter selection technique"
    )
    initial_depth: int = Field(1, ge=1, le=10, description="Starting circuit depth p")
    max_depth: int = Field(5, ge=1, le=10, description="Maximum circuit depth p ceiling")
    depth_growth: DepthGrowthStrategy = Field(
        DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
        description="Protocol for dynamic layer/depth expansion"
    )
    stagnation_patience: int = Field(
        3, ge=1, le=50,
        description="Iterations without threshold improvement before triggering depth expansion or stopping"
    )
    improvement_threshold: float = Field(
        1e-3, ge=1e-8, le=1.0,
        description="Relative improvement needed to reset stagnation counter"
    )
    fourier_q_order: int = Field(
        2, ge=1, le=10,
        description="Number of Fourier coefficients (q) for parameter dimension reduction"
    )
    primary_optimizer: ClassicalOptimizerType = Field(
        ClassicalOptimizerType.COBYLA,
        description="Primary classical optimizer"
    )
    fallback_optimizer: Optional[ClassicalOptimizerType] = Field(
        ClassicalOptimizerType.NELDER_MEAD,
        description="Secondary fallback optimizer invoked upon stagnation"
    )
    optimizer_schedule: OptimizerScheduleType = Field(
        OptimizerScheduleType.ADAPTIVE_FALLBACK,
        description="Optimizer switching and scheduling policy"
    )
    max_evaluations_total: int = Field(
        2000, ge=10, le=50000,
        description="Maximum cumulative quantum expectation evaluations across all depths"
    )
    warm_start_execution_id: Optional[str] = Field(
        None, description="Prior quantum execution ID to extract seed parameters from"
    )
    warm_start_parameters: Optional[Dict[str, List[float]]] = Field(
        None, description="Explicit prior gamma/beta vectors to warm-start"
    )

    @model_validator(mode="after")
    def validate_depth_bounds(self) -> "AdaptiveStrategyConfiguration":
        if self.max_depth < self.initial_depth:
            raise ValueError(f"max_depth ({self.max_depth}) cannot be less than initial_depth ({self.initial_depth})")
        return self


class AdaptiveQAOAConfiguration(BaseModel):
    """Full execution configuration combining quantum simulation settings and adaptive strategy."""
    shots: int = Field(1024, ge=10, le=50000, description="Measurement shots per circuit execution")
    simulation_mode: SimulationMode = Field(
        SimulationMode.IDEAL_SHOTS,
        description="Simulation fidelity: ideal_shots, statevector_exact, or noisy_simulation"
    )
    backend_name: str = Field("aer_simulator", description="Target Qiskit Aer backend")
    seed: Optional[int] = Field(42, description="Random seed for simulation reproducibility")
    noise_model_enabled: bool = Field(False, description="Whether to simulate depolarization noise")
    noise_error_rate: float = Field(0.001, ge=0.0, le=0.1, description="Depolarizing error rate")
    time_limit_seconds: float = Field(60.0, ge=1.0, le=600.0, description="Total timeout in seconds")
    strategy_config: AdaptiveStrategyConfiguration = Field(
        default_factory=AdaptiveStrategyConfiguration,
        description="Adaptive parameter and depth controller configuration"
    )


class AdaptiveQAOARequest(BaseModel):
    """Request payload to execute an Adaptive QAOA optimization process."""
    problem_id: str = Field(..., description="Target problem instance ID")
    config: AdaptiveQAOAConfiguration = Field(
        default_factory=AdaptiveQAOAConfiguration,
        description="Adaptive QAOA execution parameters"
    )


class AdaptiveIteration(BaseModel):
    """Detailed record of a single adaptive step or optimizer iteration."""
    iteration_index: int
    current_depth: int
    active_optimizer: str
    gamma: List[float]
    beta: List[float]
    expected_energy: float
    best_energy: float
    eval_count: int
    gradient_norm: Optional[float] = None
    action_taken: str = "continued_optimization"
    timestamp_offset: float


class AdaptiveDecisionLog(BaseModel):
    """Audit log entry of an adaptive decision (depth increase, optimizer switch, stopping)."""
    timestamp_offset: float
    from_depth: int
    to_depth: int
    trigger_reason: str
    action_summary: str
    active_optimizer: str


class AdaptiveQAOAResult(BaseModel):
    """Comprehensive scientific output schema for an Adaptive QAOA experiment."""
    execution_id: str = Field(default_factory=lambda: f"aqaoa_{uuid.uuid4().hex[:12]}")
    problem_id: str
    problem_type: ProblemType
    status: QuantumExecutionStatus = QuantumExecutionStatus.COMPLETED
    strategy_type: AdaptiveStrategyType
    initial_depth: int
    final_depth: int
    stopping_reason: StoppingConditionType
    best_gamma: List[float]
    best_beta: List[float]
    best_bitstring: str
    best_solution: Dict[str, Any]
    objective_value: float
    expected_energy: float
    is_feasible: bool
    constraint_violations: List[str] = Field(default_factory=list)
    approximation_ratio: Optional[float] = None
    exact_optimal_value: Optional[float] = None
    optimality_gap_percent: Optional[float] = None
    total_evaluations: int
    total_circuit_executions: int
    execution_time_ms: float
    iterations_log: List[AdaptiveIteration] = Field(default_factory=list)
    decisions_log: List[AdaptiveDecisionLog] = Field(default_factory=list)
    circuit_metadata: Optional[CircuitMetadata] = None
    hardware_transparency_note: str = (
        "Execution ran on classical CPU simulation via Qiskit Aer. "
        "No physical quantum hardware speedup is claimed."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdaptiveExperimentMetadata(BaseModel):
    """Summary metadata descriptor for indexing adaptive QAOA experiments."""
    execution_id: str
    problem_id: str
    problem_type: str
    strategy_type: str
    initial_depth: int
    final_depth: int
    depth_growth_strategy: str
    stopping_reason: str
    objective_value: float
    is_feasible: bool
    approximation_ratio: Optional[float] = None
    total_evaluations: int
    execution_time_ms: float
    created_at: datetime
