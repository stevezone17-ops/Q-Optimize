"""Unit tests for Stage 6.4: Adaptive QAOA Optimizer Selection & Scheduling."""

import pytest

from backend.app.solvers.quantum.config import (
    ClassicalOptimizerType,
    SimulationMode,
)
from backend.app.solvers.quantum.adaptive.adaptive_config import OptimizerScheduleType
from backend.app.solvers.quantum.adaptive.optimizer_controller import (
    AdaptiveOptimizerController,
    OptimizerTransitionRecord,
)
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import AdaptiveOptimizerError


def test_optimizer_recommendations():
    """Verify recommendation heuristic for simulation physics and noise."""
    # Shots or noisy simulation requires derivative-free optimizer
    rec_shots = AdaptiveOptimizerController.recommend_initial_optimizer(
        simulation_mode=SimulationMode.IDEAL_SHOTS,
        p_depth=3,
        noise_enabled=False,
    )
    assert rec_shots == ClassicalOptimizerType.COBYLA

    rec_noisy = AdaptiveOptimizerController.recommend_initial_optimizer(
        simulation_mode=SimulationMode.NOISY_SIMULATION,
        p_depth=2,
        noise_enabled=True,
    )
    assert rec_noisy == ClassicalOptimizerType.COBYLA

    # Exact statevector with higher depth allows SLSQP
    rec_exact = AdaptiveOptimizerController.recommend_initial_optimizer(
        simulation_mode=SimulationMode.STATEVECTOR_EXACT,
        p_depth=4,
        noise_enabled=False,
    )
    assert rec_exact == ClassicalOptimizerType.SLSQP


def test_static_optimizer_schedule():
    """Verify static schedule never transitions and raises on forced transition."""
    ctrl = AdaptiveOptimizerController(
        primary_optimizer=ClassicalOptimizerType.COBYLA,
        schedule_type=OptimizerScheduleType.STATIC,
    )
    assert ctrl.current_optimizer == ClassicalOptimizerType.COBYLA

    ctrl.record_step(gamma=[0.1], beta=[0.2], energy=-1.5, eval_count=10)
    assert ctrl.evaluations_by_optimizer[ClassicalOptimizerType.COBYLA.value] == 10
    assert ctrl.best_energy == -1.5

    should_switch, _ = ctrl.should_transition(stagnation_count=10, cumulative_evals=500)
    assert should_switch is False

    with pytest.raises(AdaptiveOptimizerError):
        ctrl.execute_transition()


def test_adaptive_fallback_schedule():
    """Verify fallback schedule transitions upon stagnation and logs transition record."""
    ctrl = AdaptiveOptimizerController(
        primary_optimizer=ClassicalOptimizerType.COBYLA,
        fallback_optimizer=ClassicalOptimizerType.NELDER_MEAD,
        schedule_type=OptimizerScheduleType.ADAPTIVE_FALLBACK,
        stagnation_patience=3,
    )

    # Initial state
    assert ctrl.current_optimizer == ClassicalOptimizerType.COBYLA
    assert len(ctrl.transitions) == 0

    # Record some steps
    ctrl.record_step(gamma=[0.2], beta=[0.4], energy=-2.0, eval_count=5)
    ctrl.record_step(gamma=[0.25], beta=[0.35], energy=-2.1, eval_count=5)
    assert ctrl.best_energy == -2.1

    # Before patience threshold
    should_switch, _ = ctrl.should_transition(stagnation_count=2, cumulative_evals=10)
    assert should_switch is False

    # At patience threshold
    should_switch, reason = ctrl.should_transition(stagnation_count=3, cumulative_evals=10)
    assert should_switch is True
    assert "Energy stagnation detected" in reason

    # Execute transition
    new_opt = ctrl.execute_transition(reason)
    assert new_opt == ClassicalOptimizerType.NELDER_MEAD
    assert ctrl.current_optimizer == ClassicalOptimizerType.NELDER_MEAD
    assert len(ctrl.transitions) == 1

    trans = ctrl.transitions[0]
    assert trans.from_optimizer == ClassicalOptimizerType.COBYLA.value
    assert trans.to_optimizer == ClassicalOptimizerType.NELDER_MEAD.value
    assert trans.energy_at_transition == -2.1
    assert trans.total_evals_at_transition == 10

    # Further transition attempt is rejected
    should_switch_again, _ = ctrl.should_transition(stagnation_count=5, cumulative_evals=20)
    assert should_switch_again is False
    with pytest.raises(AdaptiveOptimizerError):
        ctrl.execute_transition()

    # Resetting for new depth restores primary optimizer
    ctrl.reset_for_new_depth()
    assert ctrl.current_optimizer == ClassicalOptimizerType.COBYLA


def test_multi_stage_optimizer_schedule():
    """Verify multi-stage progression from coarse exploration to fine refinement."""
    ctrl = AdaptiveOptimizerController(
        primary_optimizer=ClassicalOptimizerType.NELDER_MEAD,
        fallback_optimizer=ClassicalOptimizerType.SLSQP,
        schedule_type=OptimizerScheduleType.MULTI_STAGE,
        stagnation_patience=4,
        max_evaluations_total=100,
    )
    assert ctrl.active_stage == 1

    ctrl.record_step(gamma=[0.1], beta=[0.1], energy=-0.5, eval_count=35)
    should_switch, reason = ctrl.should_transition(stagnation_count=1, cumulative_evals=35)
    assert should_switch is True
    assert "Stage 1 exploration completed" in reason

    new_opt = ctrl.execute_transition(reason)
    assert new_opt == ClassicalOptimizerType.SLSQP
    assert ctrl.active_stage == 2
    assert len(ctrl.transitions) == 1
