"""Adaptive QAOA convergence tracking, rolling improvement metrics, and intelligent stopping."""

import time
import math
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from pydantic import BaseModel, Field

from backend.app.solvers.quantum.adaptive.adaptive_config import StoppingConditionType


class ConvergenceMetrics(BaseModel):
    """Statistical summary of optimization convergence trajectory."""
    initial_energy: float
    final_energy: float
    best_energy: float
    total_evaluations: int
    total_iterations: int
    stagnation_count: int
    rolling_energy_variance: float
    mean_improvement_rate: float
    elapsed_time_seconds: float
    stopping_reason: StoppingConditionType


class AdaptiveConvergenceMonitor:
    """
    Monitors energy expectations, parameter step sizes, stagnation windows,
    and computational budgets to govern adaptive decision actions and stopping conditions.
    """

    def __init__(
        self,
        improvement_threshold: float = 1e-3,
        stagnation_patience: int = 3,
        parameter_tolerance: float = 1e-4,
        max_evaluations: int = 2000,
        max_iterations: int = 150,
        time_limit_seconds: float = 60.0,
        target_energy: Optional[float] = None,
        rolling_window_size: int = 5,
    ):
        self.improvement_threshold = improvement_threshold
        self.stagnation_patience = max(1, stagnation_patience)
        self.parameter_tolerance = parameter_tolerance
        self.max_evaluations = max_evaluations
        self.max_iterations = max_iterations
        self.time_limit_seconds = time_limit_seconds
        self.target_energy = target_energy
        self.rolling_window_size = max(2, rolling_window_size)

        self.energy_history: List[float] = []
        self.eval_counts: List[int] = []
        self.parameter_shifts: List[float] = []
        self.best_energy: float = float("inf")
        self.best_gamma: List[float] = []
        self.best_beta: List[float] = []

        self.stagnation_count: int = 0
        self.cumulative_evaluations: int = 0
        self.cumulative_iterations: int = 0
        self._start_time: float = time.perf_counter()
        self._last_parameters: Optional[np.ndarray] = None

    def record_evaluation(
        self,
        gamma: List[float],
        beta: List[float],
        energy: float,
        eval_count: int = 1,
    ) -> Tuple[bool, float]:
        """
        Record an optimization evaluation.
        Returns:
            Tuple of (is_new_best, energy_improvement).
        """
        self.cumulative_evaluations += eval_count
        self.cumulative_iterations += 1
        self.energy_history.append(energy)
        self.eval_counts.append(eval_count)

        # Compute parameter step distance
        current_param_vec = np.array(gamma + beta, dtype=float)
        if self._last_parameters is not None and len(self._last_parameters) == len(current_param_vec):
            shift = float(np.linalg.norm(current_param_vec - self._last_parameters))
        else:
            shift = 0.0
        self.parameter_shifts.append(shift)
        self._last_parameters = current_param_vec

        is_new_best = False
        improvement = 0.0

        if math.isinf(self.best_energy):
            improvement = 0.0
            self.best_energy = energy
            self.best_gamma = list(gamma)
            self.best_beta = list(beta)
            self.stagnation_count = 0
            is_new_best = True
        else:
            improvement = self.best_energy - energy
            if improvement > self.improvement_threshold:
                self.best_energy = energy
                self.best_gamma = list(gamma)
                self.best_beta = list(beta)
                self.stagnation_count = 0
                is_new_best = True
            else:
                self.stagnation_count += 1

        return is_new_best, improvement

    def check_stopping_condition(
        self,
        can_grow_depth: bool,
        can_switch_optimizer: bool,
        cancellation_requested: bool = False,
    ) -> Optional[StoppingConditionType]:
        """
        Check whether optimization should stop immediately.
        Returns StoppingConditionType or None if execution should continue.
        """
        if cancellation_requested:
            return StoppingConditionType.CANCELLED

        elapsed = time.perf_counter() - self._start_time
        if elapsed >= self.time_limit_seconds:
            return StoppingConditionType.TIMEOUT

        if self.cumulative_evaluations >= self.max_evaluations:
            return StoppingConditionType.MAX_EVALUATIONS_REACHED

        if self.cumulative_iterations >= self.max_iterations:
            return StoppingConditionType.MAX_ITERATIONS_REACHED

        if self.target_energy is not None and self.best_energy <= self.target_energy:
            return StoppingConditionType.TARGET_ENERGY_REACHED

        # Stagnation stopping: occurs only when neither depth expansion nor optimizer switching is possible
        if not can_grow_depth and not can_switch_optimizer:
            if self.stagnation_count >= self.stagnation_patience:
                # Check parameter shift convergence
                if len(self.parameter_shifts) >= 3 and np.mean(self.parameter_shifts[-3:]) < self.parameter_tolerance:
                    return StoppingConditionType.CONVERGED
                return StoppingConditionType.STAGNATED

        return None

    def evaluate_adaptive_action(
        self,
        can_grow_depth: bool,
        can_switch_optimizer: bool,
        cancellation_requested: bool = False,
    ) -> Tuple[str, Optional[StoppingConditionType], Optional[str]]:
        """
        Determine the next tactical action in the hybrid loop:
        Returns:
            Tuple of (action_name, stopping_reason_if_terminal, diagnostic_reason)
            action_name can be: "TERMINATE", "EXPAND_DEPTH", "SWITCH_OPTIMIZER", "CONTINUE_OPTIMIZATION"
        """
        stop_reason = self.check_stopping_condition(
            can_grow_depth=can_grow_depth,
            can_switch_optimizer=can_switch_optimizer,
            cancellation_requested=cancellation_requested,
        )
        if stop_reason is not None:
            return "TERMINATE", stop_reason, f"Terminated due to {stop_reason.value}"

        # If stagnated, check if optimizer switch or depth expansion is triggered
        if self.stagnation_count >= self.stagnation_patience:
            if can_switch_optimizer:
                return (
                    "SWITCH_OPTIMIZER",
                    None,
                    f"Stagnation count ({self.stagnation_count}) reached patience ({self.stagnation_patience}); triggering optimizer switch."
                )
            elif can_grow_depth:
                return (
                    "EXPAND_DEPTH",
                    None,
                    f"Stagnation count ({self.stagnation_count}) reached patience ({self.stagnation_patience}); triggering depth expansion."
                )

        return "CONTINUE_OPTIMIZATION", None, "Continuing outer-loop optimization"

    def reset_stagnation_for_new_layer(self) -> None:
        """Reset stagnation counters when circuit depth expands."""
        self.stagnation_count = 0
        self._last_parameters = None

    def get_convergence_metrics(self, stopping_reason: StoppingConditionType) -> ConvergenceMetrics:
        """Compute final statistical metrics across the execution trajectory."""
        init_e = self.energy_history[0] if self.energy_history else 0.0
        final_e = self.energy_history[-1] if self.energy_history else 0.0
        elapsed = time.perf_counter() - self._start_time

        if len(self.energy_history) >= 2:
            rolling_slice = self.energy_history[-min(self.rolling_window_size, len(self.energy_history)):]
            rolling_var = float(np.var(rolling_slice))
            diffs = [
                self.energy_history[i] - self.energy_history[i + 1]
                for i in range(len(self.energy_history) - 1)
            ]
            mean_rate = float(np.mean(diffs))
        else:
            rolling_var = 0.0
            mean_rate = 0.0

        return ConvergenceMetrics(
            initial_energy=init_e,
            final_energy=final_e,
            best_energy=self.best_energy if not math.isinf(self.best_energy) else final_e,
            total_evaluations=self.cumulative_evaluations,
            total_iterations=self.cumulative_iterations,
            stagnation_count=self.stagnation_count,
            rolling_energy_variance=rolling_var,
            mean_improvement_rate=mean_rate,
            elapsed_time_seconds=round(elapsed, 4),
            stopping_reason=stopping_reason,
        )
