"""Adaptive QAOA Research & Dynamic Parameter Strategies module."""

from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    AdaptiveQAOAError,
    AdaptiveStrategyNotFoundError,
    IncompatibleWarmStartError,
    DepthLimitExceededError,
    AdaptiveConvergenceError,
    AdaptiveOptimizerError,
    IncompatibleTransferError,
)
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    InitializationStrategyType,
    DepthGrowthStrategy,
    StoppingConditionType,
    OptimizerScheduleType,
    DEFAULT_ADAPTIVE_CONFIG,
)
from backend.app.solvers.quantum.adaptive.base_strategy import (
    IAdaptiveStrategy,
    StrategyMetadata,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveStrategyConfiguration,
    AdaptiveQAOAConfiguration,
    AdaptiveQAOARequest,
    AdaptiveIteration,
    AdaptiveDecisionLog,
    AdaptiveQAOAResult,
    AdaptiveExperimentMetadata,
)
from backend.app.solvers.quantum.adaptive.strategy_registry import (
    AdaptiveStrategyRegistry,
    StandardQAOAStrategy,
    LinearRampQAOAStrategy,
    FourierQAOAStrategy,
    DynamicDepthStrategy,
    WarmStartStrategy,
    AdaptiveOptimizerStrategy,
    FullAdaptiveQAOAStrategy,
)
from backend.app.solvers.quantum.adaptive.strategy_factory import AdaptiveStrategyFactory
from backend.app.solvers.quantum.adaptive.initializers import (
    BaseParameterInitializer,
    RandomInitializer,
    LinearRampInitializer,
    FourierInitializer,
    WarmStartInitializer,
    CustomInitializer,
    ParameterInitializerFactory,
)
from backend.app.solvers.quantum.adaptive.transfer import (
    TransferCompatibilityReport,
    TransferParametersRequest,
    TransferParametersResponse,
    ParameterTransferService,
)
from backend.app.solvers.quantum.adaptive.optimizer_controller import (
    OptimizerTransitionRecord,
    AdaptiveOptimizerController,
)
from backend.app.solvers.quantum.adaptive.depth_manager import (
    DepthGrowthEvent,
    AdaptiveDepthManager,
)

__all__ = [
    "AdaptiveQAOAError",
    "AdaptiveStrategyNotFoundError",
    "IncompatibleWarmStartError",
    "DepthLimitExceededError",
    "AdaptiveConvergenceError",
    "AdaptiveOptimizerError",
    "IncompatibleTransferError",
    "AdaptiveStrategyType",
    "InitializationStrategyType",
    "DepthGrowthStrategy",
    "StoppingConditionType",
    "OptimizerScheduleType",
    "DEFAULT_ADAPTIVE_CONFIG",
    "IAdaptiveStrategy",
    "StrategyMetadata",
    "AdaptiveStrategyConfiguration",
    "AdaptiveQAOAConfiguration",
    "AdaptiveQAOARequest",
    "AdaptiveIteration",
    "AdaptiveDecisionLog",
    "AdaptiveQAOAResult",
    "AdaptiveExperimentMetadata",
    "AdaptiveStrategyRegistry",
    "StandardQAOAStrategy",
    "LinearRampQAOAStrategy",
    "FourierQAOAStrategy",
    "DynamicDepthStrategy",
    "WarmStartStrategy",
    "AdaptiveOptimizerStrategy",
    "FullAdaptiveQAOAStrategy",
    "AdaptiveStrategyFactory",
    "BaseParameterInitializer",
    "RandomInitializer",
    "LinearRampInitializer",
    "FourierInitializer",
    "WarmStartInitializer",
    "CustomInitializer",
    "ParameterInitializerFactory",
    "TransferCompatibilityReport",
    "TransferParametersRequest",
    "TransferParametersResponse",
    "ParameterTransferService",
    "OptimizerTransitionRecord",
    "AdaptiveOptimizerController",
    "DepthGrowthEvent",
    "AdaptiveDepthManager",
]
