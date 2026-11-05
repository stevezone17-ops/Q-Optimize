"""Tests for Classical Benchmarking and Performance Evaluation Engine (Stage 4.6)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.benchmarking import (
    BenchmarkRequest,
    BenchmarkResult,
    ClassicalBenchmarkEngine,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_run_classical_benchmark_max_cut(client: TestClient):
    """POST /api/v1/solvers/classical/benchmark executes multi-solver comparison on Max-Cut."""
    payload = {
        "name": "Max-Cut 4-Node Test Benchmark",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                ["A", "B", 3.0],
                ["B", "C", 2.0],
                ["C", "D", 4.0],
                ["D", "A", 1.0],
                ["A", "C", 5.0],
            ],
        },
        "solver_ids": ["exact", "genetic_algorithm", "simulated_annealing"],
        "solver_configs": {
            "genetic_algorithm": {"generations": 30, "population_size": 30},
            "simulated_annealing": {"max_iterations": 100, "steps_per_temperature": 10},
        },
        "trials": 2,
        "base_seed": 42,
    }

    res = client.post("/api/v1/solvers/classical/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "benchmark_id" in data
    assert data["name"] == "Max-Cut 4-Node Test Benchmark"
    assert data["problem_type"] == "max_cut"
    assert data["exact_optimum"] is not None
    assert data["exact_optimum"] > 0
    assert len(data["summaries"]) == 3

    # Check solver summaries
    solver_ids = [s["solver_id"] for s in data["summaries"]]
    assert set(solver_ids) == {"exact", "genetic_algorithm", "simulated_annealing"}

    exact_summary = next(s for s in data["summaries"] if s["solver_id"] == "exact")
    assert exact_summary["trials_count"] == 1
    assert exact_summary["feasibility_rate"] == 1.0
    assert exact_summary["optimality_gap_percent"] == 0.0

    ga_summary = next(s for s in data["summaries"] if s["solver_id"] == "genetic_algorithm")
    assert ga_summary["trials_count"] == 2
    assert ga_summary["feasibility_rate"] == 1.0
    assert ga_summary["optimality_gap_percent"] is not None
    assert ga_summary["optimality_gap_percent"] >= 0.0

    sa_summary = next(s for s in data["summaries"] if s["solver_id"] == "simulated_annealing")
    assert sa_summary["trials_count"] == 2
    assert sa_summary["feasibility_rate"] == 1.0
    assert sa_summary["optimality_gap_percent"] is not None
    assert sa_summary["optimality_gap_percent"] >= 0.0


def test_run_classical_benchmark_multiple_trials(client: TestClient):
    """Verify stochastic solver standard deviation across multiple trials."""
    payload = {
        "name": "Stochastic Variance Test",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["N1", "N2", "N3", "N4", "N5"],
            "edges": [
                ["N1", "N2", 1.0],
                ["N2", "N3", 2.0],
                ["N3", "N4", 3.0],
                ["N4", "N5", 4.0],
                ["N5", "N1", 5.0],
            ],
        },
        "solver_ids": ["genetic_algorithm"],
        "solver_configs": {
            "genetic_algorithm": {"generations": 20, "population_size": 20},
        },
        "trials": 3,
        "base_seed": 100,
    }

    res = client.post("/api/v1/solvers/classical/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["summaries"]) == 1
    summary = data["summaries"][0]
    assert summary["trials_count"] == 3
    assert summary["feasibility_rate"] == 1.0
    assert summary["mean_objective"] > 0
    assert summary["std_objective"] >= 0.0


def test_benchmark_get_and_list(client: TestClient):
    """GET /api/v1/solvers/classical/benchmarks returns list and GET /{id} retrieves item."""
    # First create a benchmark
    payload = {
        "name": "Persistent Benchmark Test",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B"],
            "edges": [["A", "B", 1.0]],
        },
        "solver_ids": ["exact"],
    }
    create_res = client.post("/api/v1/solvers/classical/benchmark", json=payload)
    assert create_res.status_code == 200
    bench_id = create_res.json()["benchmark_id"]

    # Retrieve by ID
    get_res = client.get(f"/api/v1/solvers/classical/benchmarks/{bench_id}")
    assert get_res.status_code == 200
    b_data = get_res.json()
    assert b_data["benchmark_id"] == bench_id
    assert b_data["name"] == "Persistent Benchmark Test"

    # List benchmarks
    list_res = client.get("/api/v1/solvers/classical/benchmarks?limit=10")
    assert list_res.status_code == 200
    b_list = list_res.json()
    assert any(b["benchmark_id"] == bench_id for b in b_list)


def test_benchmark_404_not_found(client: TestClient):
    """GET non-existent benchmark returns 404."""
    res = client.get("/api/v1/solvers/classical/benchmarks/non_existent_bench_999")
    assert res.status_code == 404


def test_benchmark_assignment_problem(client: TestClient):
    """Benchmark comparing Hungarian exact vs GA and SA on 3x3 Assignment problem."""
    payload = {
        "name": "Assignment 3x3 Benchmark",
        "problem_type": "assignment",
        "instance": {
            "agents": ["A1", "A2", "A3"],
            "tasks": ["T1", "T2", "T3"],
            "cost_matrix": [
                [10.0, 5.0, 15.0],
                [4.0, 12.0, 8.0],
                [9.0, 6.0, 3.0],
            ],
        },
        "solver_ids": ["exact", "genetic_algorithm", "simulated_annealing"],
        "solver_configs": {
            "genetic_algorithm": {"generations": 25, "population_size": 25},
            "simulated_annealing": {"max_iterations": 100, "steps_per_temperature": 10},
        },
        "trials": 1,
    }

    res = client.post("/api/v1/solvers/classical/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["problem_type"] == "assignment"
    assert data["exact_optimum"] == 12.0  # Hungarian exact optimum is 12.0
    for s in data["summaries"]:
        assert s["feasibility_rate"] == 1.0
        assert s["optimality_gap_percent"] is not None
