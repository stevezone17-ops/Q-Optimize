"""Unit tests for Stage 6.6: Adaptive QAOA Convergence Monitoring & Intelligent Stopping."""

import pytest
import time

from backend.app.solvers.quantum.adaptive.adaptive_config import StoppingConditionType
from backend.app.solvers.quantum.adaptive.convergence_monitor import (
    AdaptiveConvergenceMonitor,
    ConvergenceMetrics,
)


def test_convergence_monitor_evaluation_and_stagnation():
    """Verify evaluation tracking, best energy updates, and stagnation counting."""
    mon = AdaptiveConvergenceMonitor(
        improvement_threshold=1e-3,
        stagnation_patience=3,
        max_evaluations=1000,
    )

    # Initial evaluation
    is_best, impr = mon.record_evaluation(gamma=[0.1], beta=[0.2], energy=-1.0, eval_count=5)
    assert is_best is True
    assert mon.best_energy == -1.0
    assert mon.stagnation_count == 0
    assert mon.cumulative_evaluations == 5

    # Significant improvement
    is_best, impr = mon.record_evaluation(gamma=[0.12], beta=[0.18], energy=-1.5, eval_count=5)
    assert is_best is True
    assert mon.best_energy == -1.5
    assert mon.stagnation_count == 0
    assert impr == pytest.approx(0.5)

    # Negligible improvement (< 1e-3)
    is_best, impr = mon.record_evaluation(gamma=[0.121], beta=[0.181], energy=-1.5001, eval_count=5)
    assert is_best is False
    assert mon.stagnation_count == 1

    # Another negligible step
    is_best, impr = mon.record_evaluation(gamma=[0.122], beta=[0.182], energy=-1.5002, eval_count=5)
    assert is_best is False
    assert mon.stagnation_count == 2


def test_convergence_monitor_stopping_conditions():
    """Verify immediate detection of resource limits, targets, and cancellation."""
    # Max evaluations
    mon_eval = AdaptiveConvergenceMonitor(max_evaluations=20)
    mon_eval.record_evaluation([0.1], [0.2], energy=-1.0, eval_count=25)
    assert mon_eval.check_stopping_condition(can_grow_depth=True, can_switch_optimizer=True) == StoppingConditionType.MAX_EVALUATIONS_REACHED

    # Max iterations
    mon_iter = AdaptiveConvergenceMonitor(max_iterations=2)
    mon_iter.record_evaluation([0.1], [0.2], energy=-1.0)
    mon_iter.record_evaluation([0.2], [0.3], energy=-1.1)
    assert mon_iter.check_stopping_condition(can_grow_depth=True, can_switch_optimizer=True) == StoppingConditionType.MAX_ITERATIONS_REACHED

    # Target energy reached
    mon_target = AdaptiveConvergenceMonitor(target_energy=-5.0)
    mon_target.record_evaluation([0.1], [0.2], energy=-6.0)
    assert mon_target.check_stopping_condition(can_grow_depth=True, can_switch_optimizer=True) == StoppingConditionType.TARGET_ENERGY_REACHED

    # Cancellation
    mon_cancel = AdaptiveConvergenceMonitor()
    assert mon_cancel.check_stopping_condition(can_grow_depth=True, can_switch_optimizer=True, cancellation_requested=True) == StoppingConditionType.CANCELLED


def test_convergence_monitor_adaptive_action_triggers():
    """Verify state machine triggers optimizer switch vs depth expansion vs termination."""
    mon = AdaptiveConvergenceMonitor(stagnation_patience=2, improvement_threshold=1e-3)

    mon.record_evaluation([0.1], [0.2], energy=-1.0)
    mon.record_evaluation([0.1], [0.2], energy=-1.0) # stagnation 1
    mon.record_evaluation([0.1], [0.2], energy=-1.0) # stagnation 2

    # Case A: Optimizer switch is available
    action_a, stop_a, reason_a = mon.evaluate_adaptive_action(
        can_grow_depth=True,
        can_switch_optimizer=True,
    )
    assert action_a == "SWITCH_OPTIMIZER"
    assert stop_a is None
    assert "optimizer switch" in reason_a

    # Case B: Cannot switch optimizer, but can expand depth
    action_b, stop_b, reason_b = mon.evaluate_adaptive_action(
        can_grow_depth=True,
        can_switch_optimizer=False,
    )
    assert action_b == "EXPAND_DEPTH"
    assert stop_b is None
    assert "depth expansion" in reason_b

    # Case C: Neither depth nor optimizer can change -> TERMINATE (stagnated)
    action_c, stop_c, reason_c = mon.evaluate_adaptive_action(
        can_grow_depth=False,
        can_switch_optimizer=False,
    )
    assert action_c == "TERMINATE"
    assert stop_c in (StoppingConditionType.STAGNATED, StoppingConditionType.CONVERGED)


def test_convergence_metrics_computation():
    """Verify convergence metrics object attributes and calculations."""
    mon = AdaptiveConvergenceMonitor()
    mon.record_evaluation([0.1], [0.2], energy=-1.0)
    mon.record_evaluation([0.2], [0.3], energy=-2.0)
    mon.record_evaluation([0.3], [0.4], energy=-3.0)

    metrics = mon.get_convergence_metrics(StoppingConditionType.CONVERGED)
    assert isinstance(metrics, ConvergenceMetrics)
    assert metrics.initial_energy == -1.0
    assert metrics.final_energy == -3.0
    assert metrics.best_energy == -3.0
    assert metrics.total_iterations == 3
    assert metrics.stopping_reason == StoppingConditionType.CONVERGED
