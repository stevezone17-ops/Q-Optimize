"""Unit tests for Stage 6.1: Adaptive QAOA Architecture & Research Framework."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    InitializationStrategyType,
    DepthGrowthStrategy,
    StoppingConditionType,
    OptimizerScheduleType,
)
from backend.app.solvers.quantum.adaptive.base_strategy import IAdaptiveStrategy, StrategyMetadata
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    AdaptiveQAOAError,
    AdaptiveStrategyNotFoundError,
    IncompatibleWarmStartError,
    DepthLimitExceededError,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveStrategyConfiguration,
    AdaptiveQAOAConfiguration,
    AdaptiveQAOARequest,
)
from backend.app.solvers.quantum.adaptive.strategy_registry import (
    AdaptiveStrategyRegistry,
    StandardQAOAStrategy,
    FourierQAOAStrategy,
    DynamicDepthStrategy,
    WarmStartStrategy,
    AdaptiveOptimizerStrategy,
    FullAdaptiveQAOAStrategy,
)
from backend.app.solvers.quantum.adaptive.strategy_factory import AdaptiveStrategyFactory

client = TestClient(app)


def test_adaptive_strategy_registry_discovery():
    """Verify built-in strategies are registered and discoverable."""
    strategies = AdaptiveStrategyRegistry.list_strategies()
    assert len(strategies) >= 6
    strategy_ids = {s.strategy_id for s in strategies}
    expected = {
        AdaptiveStrategyType.STANDARD.value,
        AdaptiveStrategyType.FOURIER.value,
        AdaptiveStrategyType.DYNAMIC_DEPTH.value,
        AdaptiveStrategyType.WARM_START.value,
        AdaptiveStrategyType.ADAPTIVE_OPTIMIZER.value,
        AdaptiveStrategyType.FULL_ADAPTIVE.value,
    }
    assert expected.issubset(strategy_ids)


def test_adaptive_strategy_factory_instantiation():
    """Verify factory instantiates proper concrete strategy classes."""
    for strat_type in AdaptiveStrategyType:
        strat = AdaptiveStrategyFactory.create_strategy(strat_type)
        assert isinstance(strat, IAdaptiveStrategy)
        assert strat.strategy_id == strat_type.value
        assert len(strat.name) > 0
        assert len(strat.description) > 0
        assert len(strat.supported_problem_types) > 0


def test_adaptive_strategy_not_found():
    """Verify requesting an unknown strategy raises AdaptiveStrategyNotFoundError."""
    with pytest.raises(AdaptiveStrategyNotFoundError):
        AdaptiveStrategyRegistry.get("quantum_teleportation_qaoa")

    with pytest.raises(AdaptiveStrategyNotFoundError):
        AdaptiveStrategyFactory.create_strategy("unknown_strategy_xyz")


def test_adaptive_configuration_validation():
    """Verify Pydantic and strategy level configuration validation."""
    # Valid default config
    cfg = AdaptiveStrategyConfiguration()
    assert cfg.initial_depth == 1
    assert cfg.max_depth == 5
    assert AdaptiveStrategyFactory.validate_configuration(cfg) is True

    # Invalid depth bounds (max < init)
    with pytest.raises(ValueError):
        AdaptiveStrategyConfiguration(initial_depth=5, max_depth=2)

    # Strategy level validation
    fourier_strat = FourierQAOAStrategy()
    assert fourier_strat.validate_config({"fourier_q_order": 3}) is True
    with pytest.raises(ValueError, match="fourier_q_order"):
        fourier_strat.validate_config({"fourier_q_order": 0})


def test_api_list_strategies():
    """Test REST endpoint GET /api/v1/solvers/quantum/adaptive/strategies."""
    res = client.get("/api/v1/solvers/quantum/adaptive/strategies")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    ids = [d["strategy_id"] for d in data]
    assert "full_adaptive" in ids
    assert "fourier" in ids


def test_api_get_strategy_by_id():
    """Test REST endpoint GET /api/v1/solvers/quantum/adaptive/strategies/{strategy_id}."""
    res = client.get("/api/v1/solvers/quantum/adaptive/strategies/full_adaptive")
    assert res.status_code == 200
    data = res.json()
    assert data["strategy_id"] == "full_adaptive"
    assert "Adaptive" in data["name"]

    # Nonexistent
    res_err = client.get("/api/v1/solvers/quantum/adaptive/strategies/nonexistent")
    assert res_err.status_code == 404


def test_api_validate_adaptive_configuration():
    """Test REST endpoint POST /api/v1/solvers/quantum/adaptive/validate."""
    payload = {
        "problem_id": "prob_test_123",
        "config": {
            "shots": 2048,
            "strategy_config": {
                "strategy_type": "full_adaptive",
                "initial_depth": 1,
                "max_depth": 4,
            }
        }
    }
    res = client.post("/api/v1/solvers/quantum/adaptive/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["strategy"] == "full_adaptive"

    # Invalid payload (max_depth < initial_depth)
    bad_payload = {
        "problem_id": "prob_test_123",
        "config": {
            "strategy_config": {
                "strategy_type": "full_adaptive",
                "initial_depth": 4,
                "max_depth": 2,
            }
        }
    }
    res_bad = client.post("/api/v1/solvers/quantum/adaptive/validate", json=bad_payload)
    assert res_bad.status_code in (400, 422)
