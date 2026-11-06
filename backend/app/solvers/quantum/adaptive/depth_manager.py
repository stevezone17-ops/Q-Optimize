"""Adaptive QAOA circuit depth and dynamic layer growth manager."""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.solvers.quantum.adaptive.adaptive_config import DepthGrowthStrategy
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import DepthLimitExceededError
from backend.app.solvers.quantum.adaptive.transfer import ParameterTransferService


class DepthGrowthEvent(BaseModel):
    """Audit log entry capturing a circuit depth expansion event."""
    from_depth: int
    to_depth: int
    trigger_reason: str
    energy_before_growth: float
    parameters_before: Dict[str, List[float]]
    parameters_after: Dict[str, List[float]]
    timestamp_offset: float


class AdaptiveDepthManager:
    """
    Manages circuit layer progression (p -> p + 1), enforcing depth ceilings
    and orchestrating warm-start parameter transfer.
    """

    def __init__(
        self,
        initial_depth: int = 1,
        max_depth: int = 5,
        growth_strategy: DepthGrowthStrategy = DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
        improvement_threshold: float = 1e-3,
        stagnation_patience: int = 3,
        transfer_method: str = "linear_interpolation",
    ):
        if initial_depth < 1:
            raise ValueError(f"initial_depth must be >= 1, received {initial_depth}")
        if max_depth < initial_depth:
            raise ValueError(
                f"max_depth ({max_depth}) cannot be less than initial_depth ({initial_depth})"
            )
        if max_depth > 10:
            raise ValueError(f"max_depth ({max_depth}) exceeds platform maximum safety ceiling (10)")

        self.initial_depth = initial_depth
        self.max_depth = max_depth
        self.growth_strategy = growth_strategy
        self.improvement_threshold = improvement_threshold
        self.stagnation_patience = max(1, stagnation_patience)
        self.transfer_method = transfer_method

        self.current_depth = initial_depth
        self.growth_history: List[DepthGrowthEvent] = []
        self._start_time = time.perf_counter()

    def can_grow(self) -> bool:
        """Check if circuit depth can be expanded further without exceeding max_depth."""
        if self.growth_strategy == DepthGrowthStrategy.NONE:
            return False
        return self.current_depth < self.max_depth

    def should_grow(
        self,
        stagnation_count: int,
        energy_improvement: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if current optimization convergence state justifies expanding circuit depth.
        """
        if not self.can_grow():
            return False, None

        if self.growth_strategy == DepthGrowthStrategy.FIXED_INCREMENTAL:
            return True, f"Fixed incremental growth triggered from p={self.current_depth}"

        elif self.growth_strategy == DepthGrowthStrategy.IMPROVEMENT_TRIGGERED:
            # Trigger growth if stagnation count exceeds patience AND improvement is negligible
            if stagnation_count >= self.stagnation_patience:
                return (
                    True,
                    f"Energy improvement ({energy_improvement:.2e}) below threshold "
                    f"({self.improvement_threshold:.2e}) for {stagnation_count} steps >= patience {self.stagnation_patience}"
                )

        return False, None

    def grow_depth(
        self,
        current_gamma: List[float],
        current_beta: List[float],
        best_energy: float,
        reason: str = "improvement_triggered",
    ) -> Tuple[int, List[float], List[float]]:
        """
        Expand circuit depth to p + 1 and compute transferred parameters via warm start.
        Returns:
            Tuple of (new_depth, transferred_gamma, transferred_beta).
        """
        if not self.can_grow():
            raise DepthLimitExceededError(
                f"Cannot expand circuit depth: current depth ({self.current_depth}) has reached max_depth ({self.max_depth})"
            )

        target_depth = self.current_depth + 1

        # Use ParameterTransferService to interpolate/extend parameters
        new_gamma, new_beta, _ = ParameterTransferService.transfer_parameters(
            source_gamma=current_gamma,
            source_beta=current_beta,
            target_depth=target_depth,
            method=self.transfer_method,
        )

        event = DepthGrowthEvent(
            from_depth=self.current_depth,
            to_depth=target_depth,
            trigger_reason=reason,
            energy_before_growth=best_energy if not math.isinf(best_energy) else 0.0,
            parameters_before={"gamma": list(current_gamma), "beta": list(current_beta)},
            parameters_after={"gamma": list(new_gamma), "beta": list(new_beta)},
            timestamp_offset=round(time.perf_counter() - self._start_time, 4),
        )
        self.growth_history.append(event)
        self.current_depth = target_depth

        return target_depth, new_gamma, new_beta

    def get_growth_audit(self) -> List[DepthGrowthEvent]:
        """Return sequential history of all depth expansions executed."""
        return list(self.growth_history)
