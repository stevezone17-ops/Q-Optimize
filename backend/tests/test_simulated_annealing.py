"""Tests for Simulated Annealing optimization engine (Stage 4.4)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.simulated_annealing import SimulatedAnnealingSolver
from backend.app.solvers.classical.models import SolverConfiguration, OptimalityStatus, SolverStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sa_solver():
    return SimulatedAnnealingSolver()


def test_sa_max_cut_solver(sa_solver):
    """Simulated Annealing solves Max-Cut with valid feasibility and convergence checkpoints."""
    instance = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 3.0],
            ["B", "C", 2.0],
            ["C", "D", 4.0],
            ["D", "A", 1.0],
            ["A", "C", 5.0],
        ],
    }

    config = SolverConfiguration(
        seed=42,
        extra_params={
            "initial_temperature": 50.0,
            "final_temperature": 0.1,
            "cooling_rate": 0.9,
            "steps_per_temperature": 10,
            "max_iterations": 200,
        },
    )

    result = sa_solver.solve(ProblemType.MAX_CUT, instance, config=config)

    assert result.status == SolverStatus.COMPLETED
    assert result.is_feasible is True
    assert result.objective_value > 0.0
    assert result.optimality_status == OptimalityStatus.HEURISTIC_FEASIBLE
    assert len(result.candidate_solution) == 4
    assert set(result.candidate_solution.keys()) == {"A", "B", "C", "D"}
    assert len(result.convergence_history) >= 2
    # Verify temperature values in convergence checkpoints
    for pt in result.convergence_history:
        assert pt.temperature is not None
        assert pt.temperature > 0.0


def test_sa_assignment_solver(sa_solver):
    """Simulated Annealing solves Assignment with 1-to-1 matching and feasibility."""
    instance = {
        "agents": ["Worker_1", "Worker_2", "Worker_3"],
        "tasks": ["Task_A", "Task_B", "Task_C"],
        "cost_matrix": [
            [10.0, 5.0, 15.0],
            [4.0, 12.0, 8.0],
            [9.0, 6.0, 3.0],
        ],
    }

    config = SolverConfiguration(
        seed=101,
        extra_params={
            "initial_temperature": 100.0,
            "final_temperature": 0.05,
            "cooling_rate": 0.85,
            "steps_per_temperature": 20,
            "max_iterations": 300,
        },
    )

    result = sa_solver.solve(ProblemType.ASSIGNMENT, instance, config=config)

    assert result.status == SolverStatus.COMPLETED
    assert result.is_feasible is True
    assert len(result.constraint_violations) == 0
    # Candidate should map each agent to a unique task
    assigned_tasks = list(result.candidate_solution.values())
    assert len(set(assigned_tasks)) == 3
    assert set(assigned_tasks) == {"Task_A", "Task_B", "Task_C"}
    # Optimal assignment for this matrix is Worker_1->Task_B (5), Worker_2->Task_A (4), Worker_3->Task_C (3) = 12.0
    assert result.objective_value <= 18.0


def test_sa_tsp_solver(sa_solver):
    """Simulated Annealing solves TSP with valid Hamiltonian cycle."""
    instance = {
        "cities": ["NYC", "BOS", "DC", "PHL"],
        "distance_matrix": [
            [0.0, 215.0, 225.0, 95.0],
            [215.0, 0.0, 440.0, 310.0],
            [225.0, 440.0, 0.0, 140.0],
            [95.0, 310.0, 140.0, 0.0],
        ],
        "start_city": "NYC",
    }

    config = SolverConfiguration(
        seed=77,
        extra_params={
            "initial_temperature": 100.0,
            "final_temperature": 0.1,
            "cooling_rate": 0.9,
            "steps_per_temperature": 15,
            "max_iterations": 250,
        },
    )

    result = sa_solver.solve(ProblemType.TSP, instance, config=config)

    assert result.status == SolverStatus.COMPLETED
    assert result.is_feasible is True
    assert len(result.candidate_solution) == 4
    # Designated start city NYC must be preserved at index 0
    assert result.candidate_solution[0] == "NYC"
    assert set(result.candidate_solution) == {"NYC", "BOS", "DC", "PHL"}
    assert result.objective_value > 0.0


def test_sa_cooling_schedules(sa_solver):
    """Verify both exponential and linear cooling schedules execute successfully."""
    instance = {
        "nodes": ["A", "B", "C"],
        "edges": [
            ["A", "B", 1.0],
            ["B", "C", 2.0],
            ["C", "A", 3.0],
        ],
    }

    for schedule in ["exponential", "linear"]:
        config = SolverConfiguration(
            seed=42,
            extra_params={
                "initial_temperature": 20.0,
                "final_temperature": 0.5,
                "cooling_schedule": schedule,
                "cooling_rate": 0.8,
                "steps_per_temperature": 5,
                "max_iterations": 50,
            },
        )
        res = sa_solver.solve(ProblemType.MAX_CUT, instance, config=config)
        assert res.status == SolverStatus.COMPLETED
        assert res.is_feasible is True
        assert res.metadata["cooling_schedule"] == schedule


def test_sa_deterministic_seed_reproducibility(sa_solver):
    """Identical seeds produce identical solutions and trajectories."""
    instance = {
        "nodes": ["A", "B", "C", "D", "E"],
        "edges": [
            ["A", "B", 2.0],
            ["B", "C", 3.0],
            ["C", "D", 1.0],
            ["D", "E", 4.0],
            ["E", "A", 5.0],
        ],
    }

    config1 = SolverConfiguration(
        seed=12345,
        extra_params={
            "initial_temperature": 40.0,
            "final_temperature": 0.1,
            "steps_per_temperature": 10,
            "max_iterations": 100,
        },
    )
    config2 = SolverConfiguration(
        seed=12345,
        extra_params={
            "initial_temperature": 40.0,
            "final_temperature": 0.1,
            "steps_per_temperature": 10,
            "max_iterations": 100,
        },
    )

    res1 = sa_solver.solve(ProblemType.MAX_CUT, instance, config=config1)
    res2 = sa_solver.solve(ProblemType.MAX_CUT, instance, config=config2)

    assert res1.objective_value == res2.objective_value
    assert res1.candidate_solution == res2.candidate_solution
    assert len(res1.convergence_history) == len(res2.convergence_history)
    for p1, p2 in zip(res1.convergence_history, res2.convergence_history):
        assert p1.iteration == p2.iteration
        assert p1.best_objective == p2.best_objective
        assert p1.temperature == p2.temperature


def test_sa_api_execute_endpoint(client: TestClient):
    """POST /api/v1/solvers/classical/execute executes Simulated Annealing."""
    payload = {
        "solver_id": "simulated_annealing",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["Node_1", "Node_2", "Node_3"],
            "edges": [
                ["Node_1", "Node_2", 2.5],
                ["Node_2", "Node_3", 1.5],
            ],
        },
        "config": {
            "seed": 99,
            "extra_params": {
                "initial_temperature": 25.0,
                "final_temperature": 0.5,
                "max_iterations": 50,
            },
        },
    }

    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["solver_id"] == "simulated_annealing"
    assert data["status"] == "COMPLETED"
    assert data["is_feasible"] is True
    assert data["objective_value"] > 0
    assert len(data["convergence_history"]) >= 2
