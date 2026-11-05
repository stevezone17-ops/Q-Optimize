"""Factory for creating and configuring Adaptive QAOA strategies."""

from typing import Union, Dict, Any
from backend.app.solvers.quantum.adaptive.base_strategy import IAdaptiveStrategy
from backend.app.solvers.quantum.adaptive.strategy_registry import AdaptiveStrategyRegistry
from backend.app.solvers.quantum.adaptive.adaptive_config import AdaptiveStrategyType
from backend.app.solvers.quantum.adaptive.adaptive_models import AdaptiveStrategyConfiguration


class AdaptiveStrategyFactory:
    """Factory to instantiate and validate adaptive QAOA strategies."""

    @staticmethod
    def create_strategy(strategy_type: Union[AdaptiveStrategyType, str]) -> IAdaptiveStrategy:
        """Create and return an instance of the requested adaptive strategy."""
        key = strategy_type.value if isinstance(strategy_type, AdaptiveStrategyType) else str(strategy_type).lower()
        strategy_cls = AdaptiveStrategyRegistry.get(key)
        return strategy_cls()

    @staticmethod
    def validate_configuration(config: AdaptiveStrategyConfiguration) -> bool:
        """Validate hyperparameter configuration against target strategy rules."""
        strategy = AdaptiveStrategyFactory.create_strategy(config.strategy_type)
        return strategy.validate_config(config.model_dump())
