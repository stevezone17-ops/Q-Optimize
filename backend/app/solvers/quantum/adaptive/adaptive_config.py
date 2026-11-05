"""Configuration enums and defaults for Adaptive QAOA research."""

from enum import Enum
from typing import Dict, Any


class AdaptiveStrategyType(str, Enum):
    """Supported adaptive QAOA strategy variants."""
    STANDARD = "standard"
    LINEAR_RAMP = "linear_ramp"
    FOURIER = "fourier"
    WARM_START = "warm_start"
    DYNAMIC_DEPTH = "dynamic_depth"
    ADAPTIVE_OPTIMIZER = "adaptive_optimizer"
    FULL_ADAPTIVE = "full_adaptive"


class InitializationStrategyType(str, Enum):
    """Parameter initialization methods for gamma and beta vectors."""
    RANDOM = "random"
    LINEAR_RAMP = "linear_ramp"
    FOURIER = "fourier"
    WARM_START = "warm_start"
    CUSTOM = "custom"


class DepthGrowthStrategy(str, Enum):
    """Dynamic depth / layer growth schedule."""
    NONE = "none"
    FIXED_INCREMENTAL = "fixed_incremental"
    IMPROVEMENT_TRIGGERED = "improvement_triggered"


class StoppingConditionType(str, Enum):
    """Reasons for termination of adaptive QAOA execution."""
    CONVERGED = "converged"
    STAGNATED = "stagnated"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    MAX_EVALUATIONS_REACHED = "max_evaluations_reached"
    TIMEOUT = "timeout"
    TARGET_ENERGY_REACHED = "target_energy_reached"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OptimizerScheduleType(str, Enum):
    """Classical optimizer selection and scheduling protocols."""
    STATIC = "static"
    ADAPTIVE_FALLBACK = "adaptive_fallback"
    MULTI_STAGE = "multi_stage"


DEFAULT_ADAPTIVE_CONFIG: Dict[str, Any] = {
    "initial_depth": 1,
    "max_depth": 5,
    "depth_growth_strategy": DepthGrowthStrategy.IMPROVEMENT_TRIGGERED.value,
    "improvement_threshold": 1e-3,
    "stagnation_patience": 5,
    "max_evaluations_total": 2000,
    "primary_optimizer": "COBYLA",
    "fallback_optimizer": "Nelder-Mead",
    "optimizer_schedule": OptimizerScheduleType.ADAPTIVE_FALLBACK.value,
    "fourier_q_order": 2,
}
