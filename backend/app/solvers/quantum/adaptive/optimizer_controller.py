"""Adaptive classical optimizer selection, switching, and scheduling controller."""

import math
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from backend.app.solvers.quantum.config import (
    ClassicalOptimizerType,
    SimulationMode,
)
from backend.app.solvers.quantum.adaptive.adaptive_config import OptimizerScheduleType
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import AdaptiveOptimizerError


class OptimizerTransitionRecord(BaseModel):
    """Audit log entry for an optimizer switch or stage change."""
    transition_index: int
    from_optimizer: str
    to_optimizer: str
    reason: str
    from_stage: int
    to_stage: int
    energy_at_transition: float
    total_evals_at_transition: int


class AdaptiveOptimizerController:
    """
    Manages classical optimizer selection, adaptive fallback, and multi-stage scheduling
    for QAOA variational parameter discovery.
    """

    def __init__(
        self,
        primary_optimizer: ClassicalOptimizerType = ClassicalOptimizerType.COBYLA,
        fallback_optimizer: Optional[ClassicalOptimizerType] = ClassicalOptimizerType.NELDER_MEAD,
        schedule_type: OptimizerScheduleType = OptimizerScheduleType.ADAPTIVE_FALLBACK,
        stagnation_patience: int = 3,
        max_evaluations_total: int = 2000,
    ):
        self.primary_optimizer = primary_optimizer
        self.fallback_optimizer = fallback_optimizer
        self.schedule_type = schedule_type
        self.stagnation_patience = max(1, stagnation_patience)
        self.max_evaluations_total = max_evaluations_total

        self.current_optimizer: ClassicalOptimizerType = primary_optimizer
        self.active_stage: int = 1
        self.transitions: List[OptimizerTransitionRecord] = []
        self.evaluations_by_optimizer: Dict[str, int] = {
            primary_optimizer.value: 0
        }
        if fallback_optimizer:
            self.evaluations_by_optimizer[fallback_optimizer.value] = 0

        self.best_gamma: List[float] = []
        self.best_beta: List[float] = []
        self.best_energy: float = float("inf")
        self._has_switched: bool = False

    @staticmethod
    def recommend_initial_optimizer(
        simulation_mode: SimulationMode,
        p_depth: int = 1,
        noise_enabled: bool = False,
    ) -> ClassicalOptimizerType:
        """
        Recommend most suitable classical optimizer based on simulation physics and noise:
        - Exact statevector: SLSQP (gradient-guided) or COBYLA.
        - Finite shots / noisy: COBYLA or Nelder-Mead (derivative-free, robust to stochastic noise).
        """
        if noise_enabled or simulation_mode in (SimulationMode.IDEAL_SHOTS, SimulationMode.NOISY_SIMULATION):
            # Stochastic objective function requires derivative-free optimizer
            return ClassicalOptimizerType.COBYLA
        else:
            # Smooth analytical landscape allows gradient-assisted or bounded optimizers
            if p_depth <= 2:
                return ClassicalOptimizerType.COBYLA
            else:
                return ClassicalOptimizerType.SLSQP

    def record_step(
        self,
        gamma: List[float],
        beta: List[float],
        energy: float,
        eval_count: int = 1,
    ) -> bool:
        """
        Record an optimization evaluation step, track energy progress, and update best point.
        Returns True if a new global best energy was found.
        """
        opt_name = self.current_optimizer.value
        self.evaluations_by_optimizer[opt_name] = (
            self.evaluations_by_optimizer.get(opt_name, 0) + eval_count
        )

        is_new_best = False
        if energy < self.best_energy:
            self.best_energy = energy
            self.best_gamma = list(gamma)
            self.best_beta = list(beta)
            is_new_best = True

        return is_new_best

    def should_transition(
        self,
        stagnation_count: int,
        cumulative_evals: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if the optimizer should switch or advance to the next schedule stage.
        """
        if self.schedule_type == OptimizerScheduleType.STATIC:
            return False, None

        if self.schedule_type == OptimizerScheduleType.ADAPTIVE_FALLBACK:
            if not self._has_switched and self.fallback_optimizer is not None:
                if stagnation_count >= self.stagnation_patience:
                    return (
                        True,
                        f"Energy stagnation detected ({stagnation_count} steps >= patience {self.stagnation_patience})"
                    )

        elif self.schedule_type == OptimizerScheduleType.MULTI_STAGE:
            # Stage 1: Coarse exploration (e.g. 30% of eval budget or stagnation)
            if self.active_stage == 1:
                if stagnation_count >= self.stagnation_patience or cumulative_evals >= int(0.35 * self.max_evaluations_total):
                    return (
                        True,
                        f"Stage 1 exploration completed (evals={cumulative_evals}, stagnation={stagnation_count})"
                    )

        return False, None

    def execute_transition(self, reason: str = "stagnation_triggered") -> ClassicalOptimizerType:
        """
        Execute optimizer transition and record audit entry.
        """
        if self.schedule_type == OptimizerScheduleType.STATIC:
            raise AdaptiveOptimizerError("Cannot transition under STATIC optimizer schedule.")

        if self.schedule_type == OptimizerScheduleType.ADAPTIVE_FALLBACK:
            if self._has_switched or self.fallback_optimizer is None:
                raise AdaptiveOptimizerError("Fallback optimizer already invoked or none specified.")

            old_opt = self.current_optimizer
            new_opt = self.fallback_optimizer
            self.current_optimizer = new_opt
            self._has_switched = True

            record = OptimizerTransitionRecord(
                transition_index=len(self.transitions) + 1,
                from_optimizer=old_opt.value,
                to_optimizer=new_opt.value,
                reason=reason,
                from_stage=1,
                to_stage=2,
                energy_at_transition=self.best_energy if not math.isinf(self.best_energy) else 0.0,
                total_evals_at_transition=sum(self.evaluations_by_optimizer.values()),
            )
            self.transitions.append(record)
            return self.current_optimizer

        elif self.schedule_type == OptimizerScheduleType.MULTI_STAGE:
            old_opt = self.current_optimizer
            new_opt = self.fallback_optimizer or ClassicalOptimizerType.SLSQP
            self.current_optimizer = new_opt
            self.active_stage += 1

            record = OptimizerTransitionRecord(
                transition_index=len(self.transitions) + 1,
                from_optimizer=old_opt.value,
                to_optimizer=new_opt.value,
                reason=reason,
                from_stage=self.active_stage - 1,
                to_stage=self.active_stage,
                energy_at_transition=self.best_energy if not math.isinf(self.best_energy) else 0.0,
                total_evals_at_transition=sum(self.evaluations_by_optimizer.values()),
            )
            self.transitions.append(record)
            return self.current_optimizer

        raise AdaptiveOptimizerError(f"Unsupported transition for schedule {self.schedule_type}")

    def reset_for_new_depth(self) -> None:
        """
        Reset controller state when circuit depth grows (p -> p+1),
        reverting back to primary optimizer for the new layer landscape.
        """
        self.current_optimizer = self.primary_optimizer
        self._has_switched = False
        self.active_stage = 1
