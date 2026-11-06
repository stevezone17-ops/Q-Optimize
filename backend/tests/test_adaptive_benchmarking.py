"""Unit & Integration Tests for Adaptive QAOA Benchmarking and Ablation Studies (Stage 6.9)."""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.quantum.adaptive.benchmarking import (
    AdaptiveBenchmarkEngine,
    AdaptiveBenchmarkRequest,
    AdaptiveAblationVariant,
    AdaptiveBenchmarkResult,
)


@pytest.fixture
def small_maxcut_instance():
    """Small 3-node triangle graph (3 qubits)."""
    return {
        "nodes": ["0", "1", "2"],
        "edges": [
            ["0", "1", 2.0],
            ["1", "2", 3.0],
            ["0", "2", 1.0],
        ],
    }


@pytest.mark.asyncio
async def test_adaptive_benchmark_engine_direct_execution(small_maxcut_instance):
    """Test direct execution of AdaptiveBenchmarkEngine across standard and adaptive variants."""
    req = AdaptiveBenchmarkRequest(
        name="Unit Test Adaptive QAOA Ablation Study",
        problem_type=ProblemType.MAX_CUT,
        instance=small_maxcut_instance,
        include_variants=[
            AdaptiveAblationVariant.STANDARD_BASELINE,
            AdaptiveAblationVariant.FULL_ADAPTIVE,
            AdaptiveAblationVariant.ABLATION_FOURIER,
        ],
        initial_depth=1,
        max_depth=2,
        shots=256,
        max_evaluations_total=15,
        trials=1,
        base_seed=42,
    )

    result = await AdaptiveBenchmarkEngine.run_benchmark(req)

    assert isinstance(result, AdaptiveBenchmarkResult)
    assert result.benchmark_id.startswith("aqbench-")
    assert result.problem_type == ProblemType.MAX_CUT
    assert result.exact_optimum is not None
    assert result.exact_optimum == 5.0  # Max-Cut of triangle (weights 2+3+1): removing weight 1 edge cuts 2+3=5.0
    assert len(result.summaries) == 3
    assert len(result.ablation_insights) >= 1
    assert "classical CPU emulation via Qiskit Aer" in result.hardware_transparency_note

    # Verify each variant summary
    variant_ids = [s.variant_id for s in result.summaries]
    assert AdaptiveAblationVariant.STANDARD_BASELINE.value in variant_ids
    assert AdaptiveAblationVariant.FULL_ADAPTIVE.value in variant_ids
    assert AdaptiveAblationVariant.ABLATION_FOURIER.value in variant_ids

    for s in result.summaries:
        assert s.trials_count == 1
        assert s.best_objective > 0.0
        assert s.mean_objective > 0.0
        assert s.mean_evaluations > 0
        assert s.mean_circuit_executions > 0
        assert s.feasibility_rate == 1.0
        assert s.approximation_ratio is not None
        assert 0.0 < s.approximation_ratio <= 1.0


@pytest.mark.asyncio
async def test_adaptive_benchmark_retrieval_and_listing(small_maxcut_instance):
    """Test retrieving and listing saved adaptive benchmarks."""
    req = AdaptiveBenchmarkRequest(
        name="Persistence Test Benchmark",
        problem_type=ProblemType.MAX_CUT,
        instance=small_maxcut_instance,
        include_variants=[AdaptiveAblationVariant.STANDARD_BASELINE],
        initial_depth=1,
        max_depth=1,
        shots=128,
        max_evaluations_total=10,
        trials=1,
        base_seed=123,
    )

    created = await AdaptiveBenchmarkEngine.run_benchmark(req)
    fetched = await AdaptiveBenchmarkEngine.get_benchmark(created.benchmark_id)

    assert fetched is not None
    assert fetched.benchmark_id == created.benchmark_id
    assert fetched.name == "Persistence Test Benchmark"

    b_list = await AdaptiveBenchmarkEngine.list_benchmarks(limit=10)
    assert isinstance(b_list, list)
    assert any(b["benchmark_id"] == created.benchmark_id for b in b_list)


@pytest.mark.asyncio
async def test_api_adaptive_benchmark_endpoints(small_maxcut_instance):
    """Test FastAPI REST endpoints for Adaptive QAOA benchmarking."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Run Benchmark via POST
        payload = {
            "name": "API Test Benchmark",
            "problem_type": "max_cut",
            "instance": small_maxcut_instance,
            "include_variants": ["standard_baseline", "full_adaptive"],
            "initial_depth": 1,
            "max_depth": 2,
            "shots": 256,
            "max_evaluations_total": 15,
            "trials": 1,
            "base_seed": 77,
        }

        resp = await client.post("/api/v1/solvers/quantum/adaptive/benchmarks", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "benchmark_id" in data
        assert len(data["summaries"]) == 2
        bench_id = data["benchmark_id"]

        # 2. Get Benchmark by ID via GET
        resp_get = await client.get(f"/api/v1/solvers/quantum/adaptive/benchmarks/{bench_id}")
        assert resp_get.status_code == 200
        data_get = resp_get.json()
        assert data_get["benchmark_id"] == bench_id
        assert data_get["exact_optimum"] == 5.0

        # 3. List Benchmarks via GET
        resp_list = await client.get("/api/v1/solvers/quantum/adaptive/benchmarks?limit=5")
        assert resp_list.status_code == 200
        data_list = resp_list.json()
        assert isinstance(data_list, list)
        assert any(b["benchmark_id"] == bench_id for b in data_list)
