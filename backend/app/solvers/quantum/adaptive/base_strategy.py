"""Abstract base class for all Adaptive QAOA strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class StrategyMetadata(BaseModel):
    """Metadata describing an adaptive QAOA strategy."""
    strategy_id: str
    name: str
    description: str
    supported_problem_types: List[str]
    default_parameters: Dict[str, Any]
    requires_prior_parameters: bool = False
    supports_dynamic_depth: bool = False
    supports_fourier_parameterization: bool = False


class IAdaptiveStrategy(ABC):
    """
    Contract for adaptive QAOA strategy controllers.
    Each strategy governs parameter initialization, layer expansion,
    or optimizer scheduling within the hybrid loop.
    """

    @property
    @abstractmethod
    def strategy_id(self) -> str:
        """Unique machine-readable strategy identifier."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed scientific description of the adaptive strategy."""
        pass

    @property
    @abstractmethod
    def supported_problem_types(self) -> List[str]:
        """Problem types supported by this strategy (e.g. max_cut, assignment, tsp)."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate strategy-specific hyperparameter configuration.
        Raises ValueError or returns False if invalid.
        """
        pass

    @abstractmethod
    def adapt(self, context: Any) -> Any:
        """
        Execute adaptive adjustment based on current iteration state,
        energy convergence history, or parameter landscape.
        """
        pass

    def get_metadata(self) -> StrategyMetadata:
        """Export standardized strategy metadata."""
        return StrategyMetadata(
            strategy_id=self.strategy_id,
            name=self.name,
            description=self.description,
            supported_problem_types=self.supported_problem_types,
            default_parameters=getattr(self, "default_parameters", {}),
            requires_prior_parameters=getattr(self, "requires_prior_parameters", False),
            supports_dynamic_depth=getattr(self, "supports_dynamic_depth", False),
            supports_fourier_parameterization=getattr(self, "supports_fourier_parameterization", False),
        )
