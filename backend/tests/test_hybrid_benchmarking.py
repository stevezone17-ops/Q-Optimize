"""Tests for hybrid quantum-classical benchmarking engine (Stage 5.9)."""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.quantum.benchmarking import (
    HybridBenchmarkEngine,
    HybridBenchmarkRequest,
    HybridBenchmarkResult,
)
from backend.app.solvers.quantum.models import QAOAConfiguration


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_hybrid_benchmark_max_cut():
    """Verify hybrid comparative benchmarking on a triangle Max-Cut problem."""
    req = HybridBenchmarkRequest(
        name="Triangle Max-Cut Hybrid Benchmark",
        problem_type=ProblemType.MAX_CUT,
        instance={
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 2.0], ["B", "C", 3.0], ["A", "C", 1.0]],
        },
        include_solvers=["exact", "simulated_annealing", "qaoa"],
        qaoa_config=QAOAConfiguration(
            p_depth=1,
            shots=500,
            max_iterations=10,
            seed=42,
        ),
        classical_configs={
            "simulated_annealing": {"max_iterations": 100, "steps_per_temp": 10}
        },
        trials=2,
        base_seed=42,
    )

    result: HybridBenchmarkResult = await HybridBenchmarkEngine.run_benchmark(req)

    assert result.benchmark_id.startswith("hbench-")
    assert result.problem_type == ProblemType.MAX_CUT
    assert result.exact_optimum is not None
    assert result.exact_optimum > 0  # Exact Max-Cut optimum for this graph is 5.0 (nodes {B} cut edges (A,B)=2 and (B,C)=3)
    assert len(result.summaries) == 3

    # Check that QAOA summary is populated with quantum attributes
    qaoa_summary = next((s for s in result.summaries if s.solver_id == "qaoa"), None)
    assert qaoa_summary is not None
    assert qaoa_summary.is_quantum_simulator is True
    assert qaoa_summary.solver_category == "quantum_variational"
    assert qaoa_summary.circuit_metadata is not None
    assert qaoa_summary.circuit_metadata.num_qubits == 3
    assert qaoa_summary.approximation_ratio is not None
    assert 0.0 <= qaoa_summary.approximation_ratio <= 1.05
    assert qaoa_summary.feasibility_rate == 1.0  # Max-Cut unconstrained, always feasible
    assert qaoa_summary.hardware_transparency_note is not None

    # Check Exact solver summary
    exact_summary = next((s for s in result.summaries if s.solver_id == "exact"), None)
    assert exact_summary is not None
    assert exact_summary.solver_category == "classical_exact"
    assert exact_summary.best_objective == result.exact_optimum
    assert exact_summary.optimality_gap_percent == 0.0
    assert exact_summary.approximation_ratio == 1.0

    # Check persistence retrieval
    fetched = await HybridBenchmarkEngine.get_benchmark(result.benchmark_id)
    assert fetched is not None
    assert fetched.benchmark_id == result.benchmark_id


@pytest.mark.asyncio
async def test_hybrid_benchmark_assignment():
    """Verify hybrid benchmarking on a 2x2 Assignment problem."""
    req = HybridBenchmarkRequest(
        name="2x2 Assignment Hybrid Benchmark",
        problem_type=ProblemType.ASSIGNMENT,
        instance={
            "agents": ["A1", "A2"],
            "tasks": ["T1", "T2"],
            "cost_matrix": [[3.0, 5.0], [2.0, 4.0]],
        },
        include_solvers=["exact", "qaoa"],
        qaoa_config=QAOAConfiguration(
            p_depth=1,
            shots=400,
            max_iterations=8,
            seed=101,
        ),
        trials=1,
        base_seed=101,
    )

    result = await HybridBenchmarkEngine.run_benchmark(req)
    assert result.exact_optimum == 7.0  # (A1->T1 is 3.0, A2->T2 is 4.0 = 7.0)
    assert len(result.summaries) == 2

    qaoa_summary = next(s for s in result.summaries if s.solver_id == "qaoa")
    assert qaoa_summary.circuit_metadata.num_qubits == 4
    assert qaoa_summary.best_objective is not None


def test_hybrid_benchmark_api_endpoints(client: TestClient):
    """Verify REST API endpoints for hybrid quantum-classical benchmarking."""
    payload = {
        "name": "API Triangle Max-Cut Benchmark",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["0", "1", "2"],
            "edges": [["0", "1", 4.0], ["1", "2", 2.0]],
        },
        "include_solvers": ["exact", "qaoa"],
        "qaoa_config": {
            "p_depth": 1,
            "shots": 200,
            "max_iterations": 5,
            "seed": 77,
        },
        "trials": 1,
        "base_seed": 77,
    }

    # 1. Post benchmark
    res = client.post("/api/v1/solvers/quantum/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()
    b_id = data["benchmark_id"]
    assert b_id.startswith("hbench-")
    assert len(data["summaries"]) == 2
    assert "Aer" in data["hardware_transparency_note"]

    # 2. List benchmarks
    res_list = client.get("/api/v1/solvers/quantum/benchmarks")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert any(b["benchmark_id"] == b_id for b in list_data)

    # 3. Get single benchmark
    res_get = client.get(f"/api/v1/solvers/quantum/benchmarks/{b_id}")
    assert res_get.status_code == 200
    assert res_get.json()["benchmark_id"] == b_id
