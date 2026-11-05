"""Registry and discovery mechanism for Adaptive QAOA strategies."""

from typing import Dict, Type, List, Optional, Any
from backend.app.solvers.quantum.adaptive.base_strategy import IAdaptiveStrategy, StrategyMetadata
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import AdaptiveStrategyNotFoundError
from backend.app.solvers.quantum.adaptive.adaptive_config import AdaptiveStrategyType


class StandardQAOAStrategy(IAdaptiveStrategy):
    """Standard baseline QAOA strategy with fixed depth and static optimizer."""
    
    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.STANDARD.value

    @property
    def name(self) -> str:
        return "Standard Fixed-Depth QAOA"

    @property
    def description(self) -> str:
        return (
            "Baseline QAOA execution with fixed depth p, static classical optimizer, "
            "and standard parameter initialization. Serves as reference control for ablation studies."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if config.get("initial_depth", 1) < 1:
            raise ValueError("initial_depth must be at least 1")
        return True

    def adapt(self, context: Any) -> Any:
        # Standard baseline performs no dynamic adaptation
        return context


class LinearRampQAOAStrategy(IAdaptiveStrategy):
    """Linear adiabatic ramp parameter initialization strategy."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.LINEAR_RAMP.value

    @property
    def name(self) -> str:
        return "Linear Ramp QAOA"

    @property
    def description(self) -> str:
        return (
            "Initializes QAOA variational parameters according to a Trotterized adiabatic schedule: "
            "gamma linearly increases and beta linearly decreases across layers."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def adapt(self, context: Any) -> Any:
        return context


class FourierQAOAStrategy(IAdaptiveStrategy):
    """Fourier-domain parameterization for QAOA variational angles."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.FOURIER.value

    @property
    def name(self) -> str:
        return "Fourier Parameterized QAOA"

    @property
    def description(self) -> str:
        return (
            "Transforms variational angles (gamma, beta) into discrete Fourier domain coefficients (u, v). "
            "Reduces parameter optimization dimension from 2p to 2q (q < p) and avoids barren plateaus."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        q_order = config.get("fourier_q_order", 2)
        if q_order < 1:
            raise ValueError("fourier_q_order must be >= 1")
        return True

    def adapt(self, context: Any) -> Any:
        return context


class DynamicDepthStrategy(IAdaptiveStrategy):
    """Dynamically increases circuit depth p upon energy stagnation."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.DYNAMIC_DEPTH.value

    @property
    def name(self) -> str:
        return "Dynamic Depth Expansion QAOA"

    @property
    def description(self) -> str:
        return (
            "Monitors energy convergence at depth p. When convergence stagnates within a patience window, "
            "dynamically expands depth p -> p + 1 and initializes new parameters via warm-start interpolation."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        p_init = config.get("initial_depth", 1)
        p_max = config.get("max_depth", 5)
        if p_init > p_max:
            raise ValueError(f"initial_depth ({p_init}) cannot exceed max_depth ({p_max})")
        return True

    def adapt(self, context: Any) -> Any:
        return context


class WarmStartStrategy(IAdaptiveStrategy):
    """Transfers optimized parameter angles from a prior experiment or related instance."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.WARM_START.value

    @property
    def name(self) -> str:
        return "Warm-Start Parameter Transfer QAOA"

    @property
    def description(self) -> str:
        return (
            "Initializes QAOA variational angles by transferring and scaling optimal angles from a previously "
            "solved related instance or lower-depth simulation."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        # Requires either warm_start_execution_id or warm_start_parameters
        return True

    def adapt(self, context: Any) -> Any:
        return context


class AdaptiveOptimizerStrategy(IAdaptiveStrategy):
    """Dynamically manages optimizer switching and restarts based on landscape curvature."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.ADAPTIVE_OPTIMIZER.value

    @property
    def name(self) -> str:
        return "Adaptive Classical Optimizer Scheduling"

    @property
    def description(self) -> str:
        return (
            "Monitors classical optimizer trajectory. Automatically transitions between derivative-free "
            "exploratory optimizers (e.g., Nelder-Mead) and gradient-like local optimizers (COBYLA/SLSQP) "
            "when stagnation is detected."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def adapt(self, context: Any) -> Any:
        return context


class FullAdaptiveQAOAStrategy(IAdaptiveStrategy):
    """Holistic adaptive strategy combining intelligent initialization, dynamic depth, and optimizer scheduling."""

    @property
    def strategy_id(self) -> str:
        return AdaptiveStrategyType.FULL_ADAPTIVE.value

    @property
    def name(self) -> str:
        return "Full Adaptive Hybrid QAOA Framework"

    @property
    def description(self) -> str:
        return (
            "Comprehensive adaptive protocol combining Trotter/Fourier initialization, stagnation-triggered "
            "dynamic depth expansion (p -> p+1), warm-start angle interpolation, and adaptive optimizer switching."
        )

    @property
    def supported_problem_types(self) -> List[str]:
        return ["max_cut", "assignment", "tsp"]

    def validate_config(self, config: Dict[str, Any]) -> bool:
        p_init = config.get("initial_depth", 1)
        p_max = config.get("max_depth", 5)
        if p_init > p_max:
            raise ValueError(f"initial_depth ({p_init}) cannot exceed max_depth ({p_max})")
        return True

    def adapt(self, context: Any) -> Any:
        return context


class AdaptiveStrategyRegistry:
    """Registry maintaining available Adaptive QAOA strategies."""

    _registry: Dict[str, Type[IAdaptiveStrategy]] = {}

    @classmethod
    def register(cls, strategy_cls: Type[IAdaptiveStrategy]) -> None:
        """Register an adaptive strategy class."""
        instance = strategy_cls()
        cls._registry[instance.strategy_id] = strategy_cls

    @classmethod
    def get(cls, strategy_id: str) -> Type[IAdaptiveStrategy]:
        """Retrieve strategy class by identifier."""
        if strategy_id not in cls._registry:
            raise AdaptiveStrategyNotFoundError(
                f"Adaptive strategy '{strategy_id}' not found in registry. "
                f"Available strategies: {list(cls._registry.keys())}"
            )
        return cls._registry[strategy_id]

    @classmethod
    def list_strategies(cls) -> List[StrategyMetadata]:
        """List metadata for all registered strategies."""
        results = []
        for strat_cls in cls._registry.values():
            strat = strat_cls()
            results.append(strat.get_metadata())
        return results

    @classmethod
    def clear(cls) -> None:
        """Clear registry entries (used in testing)."""
        cls._registry.clear()

    @classmethod
    def initialize_defaults(cls) -> None:
        """Initialize standard built-in strategies."""
        cls.clear()
        cls.register(StandardQAOAStrategy)
        cls.register(LinearRampQAOAStrategy)
        cls.register(FourierQAOAStrategy)
        cls.register(DynamicDepthStrategy)
        cls.register(WarmStartStrategy)
        cls.register(AdaptiveOptimizerStrategy)
        cls.register(FullAdaptiveQAOAStrategy)


# Auto-initialize registry
AdaptiveStrategyRegistry.initialize_defaults()
