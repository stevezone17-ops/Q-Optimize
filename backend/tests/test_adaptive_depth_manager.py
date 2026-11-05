"""Unit tests for Stage 6.5: Adaptive QAOA Circuit Depth & Layer Growth Management."""

import pytest

from backend.app.solvers.quantum.adaptive.adaptive_config import DepthGrowthStrategy
from backend.app.solvers.quantum.adaptive.depth_manager import (
    AdaptiveDepthManager,
    DepthGrowthEvent,
)
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import DepthLimitExceededError


def test_depth_manager_initialization_and_bounds():
    """Verify initialization checks and depth ceiling guardrails."""
    # Valid
    mgr = AdaptiveDepthManager(initial_depth=1, max_depth=5)
    assert mgr.current_depth == 1
    assert mgr.max_depth == 5
    assert mgr.can_grow() is True

    # Invalid initial depth
    with pytest.raises(ValueError, match="initial_depth"):
        AdaptiveDepthManager(initial_depth=0, max_depth=5)

    # Invalid max < initial
    with pytest.raises(ValueError, match="cannot be less"):
        AdaptiveDepthManager(initial_depth=4, max_depth=2)

    # Exceeding global safety ceiling 10
    with pytest.raises(ValueError, match="safety ceiling"):
        AdaptiveDepthManager(initial_depth=1, max_depth=12)


def test_depth_manager_none_strategy():
    """Verify NONE growth strategy never permits layer expansion."""
    mgr = AdaptiveDepthManager(
        initial_depth=2,
        max_depth=5,
        growth_strategy=DepthGrowthStrategy.NONE,
    )
    assert mgr.can_grow() is False
    should_grow, _ = mgr.should_grow(stagnation_count=10, energy_improvement=0.0)
    assert should_grow is False

    with pytest.raises(DepthLimitExceededError):
        mgr.grow_depth(current_gamma=[0.1, 0.2], current_beta=[0.3, 0.4], best_energy=-1.0)


def test_depth_manager_fixed_incremental():
    """Verify FIXED_INCREMENTAL strategy expands layers step-by-step to max_depth."""
    mgr = AdaptiveDepthManager(
        initial_depth=1,
        max_depth=3,
        growth_strategy=DepthGrowthStrategy.FIXED_INCREMENTAL,
    )

    # First step
    should_grow, reason = mgr.should_grow(stagnation_count=0, energy_improvement=0.5)
    assert should_grow is True
    assert "Fixed incremental" in reason

    p2, g2, b2 = mgr.grow_depth(
        current_gamma=[0.2],
        current_beta=[0.8],
        best_energy=-1.2,
    )
    assert p2 == 2
    assert mgr.current_depth == 2
    assert len(g2) == 2 and len(b2) == 2

    # Second step: 2 -> 3
    p3, g3, b3 = mgr.grow_depth(
        current_gamma=g2,
        current_beta=b2,
        best_energy=-1.5,
    )
    assert p3 == 3
    assert mgr.current_depth == 3
    assert len(g3) == 3

    # At max depth, cannot grow further
    assert mgr.can_grow() is False
    with pytest.raises(DepthLimitExceededError):
        mgr.grow_depth(g3, b3, best_energy=-1.8)


def test_depth_manager_improvement_triggered():
    """Verify IMPROVEMENT_TRIGGERED strategy respects stagnation patience and threshold."""
    mgr = AdaptiveDepthManager(
        initial_depth=1,
        max_depth=4,
        growth_strategy=DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
        stagnation_patience=3,
        improvement_threshold=1e-3,
    )

    # Stagnation count below patience
    should_grow, _ = mgr.should_grow(stagnation_count=2, energy_improvement=1e-4)
    assert should_grow is False

    # Stagnation count reaching patience
    should_grow, reason = mgr.should_grow(stagnation_count=3, energy_improvement=1e-4)
    assert should_grow is True
    assert "Energy improvement" in reason

    p_new, g_new, b_new = mgr.grow_depth(
        current_gamma=[0.4],
        current_beta=[0.6],
        best_energy=-2.5,
        reason=reason,
    )
    assert p_new == 2
    assert len(g_new) == 2 and len(b_new) == 2
    assert len(mgr.growth_history) == 1

    event = mgr.growth_history[0]
    assert event.from_depth == 1
    assert event.to_depth == 2
    assert event.energy_before_growth == -2.5
    assert len(event.parameters_before["gamma"]) == 1
    assert len(event.parameters_after["gamma"]) == 2
