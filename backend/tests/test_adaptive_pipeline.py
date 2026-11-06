"""Unit and integration tests for Stage 6.7: Unified Adaptive QAOA Execution Pipeline."""

import pytest
import time
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.quantum.config import SimulationMode, ClassicalOptimizerType
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    InitializationStrategyType,
    DepthGrowthStrategy,
    StoppingConditionType,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOARequest,
    AdaptiveQAOAConfiguration,
    AdaptiveStrategyConfiguration,
    AdaptiveQAOAResult,
    AdaptiveExecutionRecord,
)
from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
from backend.app.db.mongodb import db_manager

client = TestClient(app)


@pytest.fixture
def sample_max_cut_problem():
    """Seed a deterministic 4-node Max-Cut problem into storage."""
    prob_id = "test-adaptive-maxcut-4"
    problem_doc = {
        "id": prob_id,
        "problem_id": prob_id,
        "name": "Adaptive Max-Cut 4-node test",
        "problem_type": ProblemType.MAX_CUT.value,
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                ["A", "B", 1.0],
                ["B", "C", 1.0],
                ["C", "D", 1.0],
                ["D", "A", 1.0],
            ]
        },
        "created_at": "2026-11-05T12:00:00Z"
    }
    db_manager.memory_insert("problems", prob_id, problem_doc)
    return prob_id


def test_adaptive_pipeline_sync_execution(sample_max_cut_problem):
    """Verify synchronous end-to-end execution of Adaptive QAOA on Max-Cut."""
    req = AdaptiveQAOARequest(
        problem_id=sample_max_cut_problem,
        config=AdaptiveQAOAConfiguration(
            shots=512,
            simulation_mode=SimulationMode.STATEVECTOR_EXACT,
            seed=42,
            strategy_config=AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.FULL_ADAPTIVE,
                init_strategy=InitializationStrategyType.LINEAR_RAMP,
                initial_depth=1,
                max_depth=2,
                depth_growth=DepthGrowthStrategy.FIXED_INCREMENTAL,
                stagnation_patience=2,
                max_evaluations_total=50,
            )
        )
    )

    result = AdaptiveQAOAExecutionPipeline.execute_sync(req)
    assert isinstance(result, AdaptiveQAOAResult)
    assert result.problem_id == sample_max_cut_problem
    assert result.final_depth >= 1
    assert len(result.best_gamma) == result.final_depth
    assert len(result.best_beta) == result.final_depth
    assert result.is_feasible is True
    assert result.objective_value >= 2.0  # C_4 has max cut 4, QAOA finds at least 2 or 4
    assert result.exact_optimal_value == 4.0
    assert result.approximation_ratio is not None
    assert result.approximation_ratio > 0.0
    assert len(result.iterations_log) > 0
    assert result.circuit_metadata is not None
    assert "classical CPU simulation" in result.hardware_transparency_note


@pytest.mark.asyncio
async def test_adaptive_pipeline_async_dispatch_and_polling(sample_max_cut_problem):
    """Verify asynchronous background dispatch, status polling, and execution record retrieval."""
    req = AdaptiveQAOARequest(
        problem_id=sample_max_cut_problem,
        config=AdaptiveQAOAConfiguration(
            shots=256,
            simulation_mode=SimulationMode.STATEVECTOR_EXACT,
            strategy_config=AdaptiveStrategyConfiguration(
                initial_depth=1,
                max_depth=1,
                depth_growth=DepthGrowthStrategy.NONE,
                max_evaluations_total=20,
            )
        )
    )

    record = await AdaptiveQAOAExecutionPipeline.submit_async(req)
    assert isinstance(record, AdaptiveExecutionRecord)
    exec_id = record.execution_id

    # Wait for completion (small problem finishes quickly)
    max_wait = 10.0
    start = time.perf_counter()
    status_resp = None
    while time.perf_counter() - start < max_wait:
        status_resp = await AdaptiveQAOAExecutionPipeline.get_status(exec_id)
        if status_resp and status_resp.is_completed:
            break
        time.sleep(0.1)

    assert status_resp is not None
    assert status_resp.is_completed is True

    # Retrieve full record
    full_rec = await AdaptiveQAOAExecutionPipeline.get_execution(exec_id)
    assert full_rec is not None
    assert full_rec.result is not None
    assert full_rec.result.objective_value is not None

    # List executions
    all_execs = await AdaptiveQAOAExecutionPipeline.list_executions(limit=10)
    assert any(e.execution_id == exec_id for e in all_execs)


@pytest.mark.asyncio
async def test_adaptive_pipeline_cancellation(sample_max_cut_problem):
    """Verify cooperative cancellation of an execution."""
    req = AdaptiveQAOARequest(
        problem_id=sample_max_cut_problem,
        config=AdaptiveQAOAConfiguration(
            shots=1024,
            simulation_mode=SimulationMode.STATEVECTOR_EXACT,
            strategy_config=AdaptiveStrategyConfiguration(
                initial_depth=1,
                max_depth=5,
                max_evaluations_total=5000,
            )
        )
    )

    record = await AdaptiveQAOAExecutionPipeline.submit_async(req)
    exec_id = record.execution_id

    cancel_resp = await AdaptiveQAOAExecutionPipeline.cancel_execution(exec_id)
    assert cancel_resp is not None
    assert cancel_resp.status in ["CANCELLED", "COMPLETED"]


def test_api_adaptive_execute_endpoints(sample_max_cut_problem):
    """Test REST API endpoints for Adaptive QAOA execution."""
    payload = {
        "problem_id": sample_max_cut_problem,
        "config": {
            "shots": 256,
            "simulation_mode": "statevector_exact",
            "strategy_config": {
                "strategy_type": "standard",
                "initial_depth": 1,
                "max_depth": 1,
                "depth_growth": "none",
                "max_evaluations_total": 20,
            }
        }
    }

    # Synchronous endpoint
    res_sync = client.post("/api/v1/solvers/quantum/adaptive/execute", json=payload)
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    assert sync_data["problem_id"] == sample_max_cut_problem
    assert sync_data["final_depth"] == 1
    assert "objective_value" in sync_data

    # Asynchronous endpoint
    res_async = client.post("/api/v1/solvers/quantum/adaptive/execute/async", json=payload)
    assert res_async.status_code == 200
    async_data = res_async.json()
    exec_id = async_data["execution_id"]
    assert exec_id.startswith("aqexec-")

    # Polling endpoint
    res_stat = client.get(f"/api/v1/solvers/quantum/adaptive/executions/{exec_id}/status")
    assert res_stat.status_code == 200
    assert "status" in res_stat.json()

    # Get execution
    res_get = client.get(f"/api/v1/solvers/quantum/adaptive/executions/{exec_id}")
    assert res_get.status_code == 200
    assert res_get.json()["execution_id"] == exec_id

    # List executions
    res_list = client.get("/api/v1/solvers/quantum/adaptive/executions")
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)

    # Cancel execution
    res_cancel = client.post(f"/api/v1/solvers/quantum/adaptive/executions/{exec_id}/cancel")
    assert res_cancel.status_code == 200
