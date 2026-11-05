"""Tests for Genetic Algorithm solver across Max-Cut, Assignment, and TSP (Stage 4.3)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.genetic_algorithm import GeneticAlgorithmSolver
from backend.app.solvers.classical.models import SolverConfiguration, OptimalityStatus, SolverStatus


@pytest.fixture
def client():
    return TestClient(app)


def test_ga_max_cut_optimization():
    """Verify GA solves Max-Cut problem and records convergence trace."""
    solver = GeneticAlgorithmSolver()
    instance = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 2.0],
            ["B", "C", 3.0],
            ["C", "D", 4.0],
            ["D", "A", 5.0],
            ["A", "C", 1.0],
        ],
    }
    config = SolverConfiguration(
        time_limit_seconds=10.0,
        seed=42,
        extra_params={
            "population_size": 40,
            "generations": 60,
            "mutation_rate": 0.05,
            "crossover_rate": 0.8,
            "elitism_count": 2,
        },
    )

    result = solver.solve(ProblemType.MAX_CUT, instance, config, seed=42)

    assert result.status == SolverStatus.COMPLETED
    assert result.is_feasible is True
    # Global optimum is 14.0; GA easily finds it on small cycle
    assert result.objective_value == 14.0
    assert result.optimality_status == OptimalityStatus.HEURISTIC_FEASIBLE
    assert len(result.convergence_history) > 1
    assert result.evaluations > 40


def test_ga_assignment_matching_validity():
    """Verify GA permutation chromosomes maintain 100% 1-to-1 matching feasibility."""
    solver = GeneticAlgorithmSolver()
    instance = {
        "agents": ["A1", "A2", "A3"],
        "tasks": ["T1", "T2", "T3"],
        "cost_matrix": [
            [10.0, 5.0, 8.0],
            [9.0, 8.0, 4.0],
            [3.0, 2.0, 6.0],
        ],
    }
    config = SolverConfiguration(
        time_limit_seconds=10.0,
        seed=42,
        extra_params={
            "population_size": 50,
            "generations": 80,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elitism_count": 2,
        },
    )

    result = solver.solve(ProblemType.ASSIGNMENT, instance, config, seed=42)

    assert result.is_feasible is True
    assert len(result.constraint_violations) == 0
    # Global optimum is 12.0
    assert result.objective_value == 12.0
    assert len(result.candidate_solution) == 3
    # Verify permutation bijection: all tasks used exactly once
    assigned_tasks = list(result.candidate_solution.values())
    assert set(assigned_tasks) == {"T1", "T2", "T3"}


def test_ga_tsp_hamiltonian_cycle():
    """Verify GA Order Crossover (OX) produces valid closed Hamiltonian cycles."""
    solver = GeneticAlgorithmSolver()
    instance = {
        "cities": ["A", "B", "C", "D"],
        "distance_matrix": [
            [0.0, 10.0, 14.14, 10.0],
            [10.0, 0.0, 10.0, 14.14],
            [14.14, 10.0, 0.0, 10.0],
            [10.0, 14.14, 10.0, 0.0],
        ],
    }
    config = SolverConfiguration(
        time_limit_seconds=10.0,
        seed=42,
        extra_params={
            "population_size": 50,
            "generations": 60,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elitism_count": 2,
        },
    )

    result = solver.solve(ProblemType.TSP, instance, config, seed=42)

    assert result.is_feasible is True
    assert len(result.constraint_violations) == 0
    assert len(result.candidate_solution) == 4
    assert set(result.candidate_solution) == {"A", "B", "C", "D"}
    # Optimal perimeter tour is 40.0
    assert abs(result.objective_value - 40.0) < 1e-3


def test_ga_tsp_with_designated_start():
    """Verify GA respects designated starting city."""
    solver = GeneticAlgorithmSolver()
    instance = {
        "cities": ["Paris", "London", "Berlin"],
        "start_city": "London",
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    result = solver.solve(ProblemType.TSP, instance, seed=42)
    assert result.is_feasible is True
    assert result.candidate_solution[0] == "London"
    assert result.objective_value == 2155.0


def test_ga_deterministic_reproducibility():
    """Verify that identical random seeds produce byte-for-byte identical outcomes and convergence traces."""
    solver = GeneticAlgorithmSolver()
    instance = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [["A", "B", 2.0], ["B", "C", 3.0], ["C", "D", 4.0], ["D", "A", 5.0]],
    }
    config = SolverConfiguration(
        time_limit_seconds=5.0,
        seed=12345,
        extra_params={"population_size": 30, "generations": 40},
    )

    run_1 = solver.solve(ProblemType.MAX_CUT, instance, config, seed=12345)
    run_2 = solver.solve(ProblemType.MAX_CUT, instance, config, seed=12345)

    assert run_1.objective_value == run_2.objective_value
    assert run_1.candidate_solution == run_2.candidate_solution
    assert len(run_1.convergence_history) == len(run_2.convergence_history)
    for p1, p2 in zip(run_1.convergence_history, run_2.convergence_history):
        assert p1.iteration == p2.iteration
        assert p1.best_objective == p2.best_objective


def test_api_execute_ga_solver_endpoint(client: TestClient):
    """POST /api/v1/solvers/classical/execute executes GA and returns result."""
    payload = {
        "solver_id": "genetic_algorithm",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [["A", "B", 1.0], ["B", "C", 2.0], ["C", "D", 3.0], ["D", "A", 4.0]],
        },
        "config": {
            "population_size": 30,
            "generations": 40,
        },
        "seed": 42,
    }
    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["solver_id"] == "genetic_algorithm"
    assert data["status"] == "COMPLETED"
    assert data["is_feasible"] is True
    assert data["objective_value"] > 0.0
    assert len(data["convergence_history"]) > 0
