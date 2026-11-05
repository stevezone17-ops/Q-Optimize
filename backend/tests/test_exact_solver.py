"""Tests for Exact Classical Solver across Max-Cut, Assignment, and TSP (Stage 4.2)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.exact import ExactSolver
from backend.app.solvers.classical.models import SolverConfiguration, OptimalityStatus, SolverStatus


@pytest.fixture
def client():
    return TestClient(app)


def test_exact_max_cut_cycle_4():
    """Verify ExactSolver achieves global optimum for 4-node weighted graph."""
    solver = ExactSolver()
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

    result = solver.solve(ProblemType.MAX_CUT, instance)

    assert result.status == SolverStatus.COMPLETED
    assert result.is_feasible is True
    # For this graph, the optimal cut partitions {A, C} and {B, D} cutting edges:
    # A-B (2.0), B-C (3.0), C-D (4.0), D-A (5.0) -> sum = 14.0
    assert result.objective_value == 14.0
    assert result.optimality_status == OptimalityStatus.PROVEN_OPTIMAL
    assert result.evaluations == 8  # 2^(4-1) due to symmetry reduction
    assert len(result.constraint_violations) == 0


def test_exact_assignment_2x2_and_3x3():
    """Verify ExactSolver finds global minimum cost matching via Hungarian algorithm."""
    solver = ExactSolver()

    # 2x2 instance
    inst_2x2 = {
        "agents": ["A1", "A2"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [
            [4.0, 7.0],
            [2.0, 5.0],
        ],
    }
    res_2x2 = solver.solve(ProblemType.ASSIGNMENT, inst_2x2)
    assert res_2x2.is_feasible is True
    assert res_2x2.objective_value == 9.0
    assert res_2x2.optimality_status == OptimalityStatus.PROVEN_OPTIMAL

    # 3x3 instance:
    # Costs:
    # A1: T1=10, T2=5, T3=8
    # A2: T1=9,  T2=8, T3=4
    # A3: T1=3,  T2=2, T3=6
    # Optimal: A1->T2(5), A2->T3(4), A3->T1(3) -> Total = 12.0
    inst_3x3 = {
        "agents": ["A1", "A2", "A3"],
        "tasks": ["T1", "T2", "T3"],
        "cost_matrix": [
            [10.0, 5.0, 8.0],
            [9.0, 8.0, 4.0],
            [3.0, 2.0, 6.0],
        ],
    }
    res_3x3 = solver.solve(ProblemType.ASSIGNMENT, inst_3x3)
    assert res_3x3.is_feasible is True
    assert res_3x3.objective_value == 12.0
    assert res_3x3.optimality_status == OptimalityStatus.PROVEN_OPTIMAL


def test_exact_tsp_triangle_and_square():
    """Verify ExactSolver finds shortest Hamiltonian cycle."""
    solver = ExactSolver()

    # 3-city triangle
    inst_tri = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    res_tri = solver.solve(ProblemType.TSP, inst_tri)
    assert res_tri.is_feasible is True
    assert res_tri.objective_value == 2155.0
    assert res_tri.optimality_status == OptimalityStatus.PROVEN_OPTIMAL
    assert len(res_tri.candidate_solution) == 3

    # 4-city metric perimeter
    inst_sq = {
        "cities": ["A", "B", "C", "D"],
        "distance_matrix": [
            [0.0, 10.0, 14.14, 10.0],
            [10.0, 0.0, 10.0, 14.14],
            [14.14, 10.0, 0.0, 10.0],
            [10.0, 14.14, 10.0, 0.0],
        ],
    }
    res_sq = solver.solve(ProblemType.TSP, inst_sq)
    assert res_sq.is_feasible is True
    assert abs(res_sq.objective_value - 40.0) < 1e-4
    assert res_sq.optimality_status == OptimalityStatus.PROVEN_OPTIMAL


def test_exact_tsp_with_designated_start():
    """Verify tour begins with the designated starting city."""
    solver = ExactSolver()
    inst = {
        "cities": ["Paris", "London", "Berlin"],
        "start_city": "London",
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    res = solver.solve(ProblemType.TSP, inst)
    assert res.is_feasible is True
    assert res.candidate_solution[0] == "London"
    assert res.objective_value == 2155.0


def test_exact_solver_size_cutoff_guards():
    """Verify exact solver safely stops and rejects instances exceeding compute limits."""
    solver = ExactSolver()

    # Max-Cut with 25 vertices
    large_nodes = [f"v{i}" for i in range(25)]
    large_edges = [[f"v{i}", f"v{i+1}", 1.0] for i in range(24)]
    with pytest.raises(ValueError, match="exceeds exact solver safety limit"):
        solver.solve(ProblemType.MAX_CUT, {"nodes": large_nodes, "edges": large_edges})

    # TSP with 15 cities
    large_cities = [f"c{i}" for i in range(15)]
    large_dists = [[0.0]*15 for _ in range(15)]
    with pytest.raises(ValueError, match="exceeds exact solver limit of 10"):
        solver.solve(ProblemType.TSP, {"cities": large_cities, "distance_matrix": large_dists})


def test_api_execute_exact_solver_endpoint(client: TestClient):
    """POST /api/v1/solvers/classical/execute runs exact solver and returns proven optimal result."""
    payload = {
        "solver_id": "exact",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                ["A", "B", 2.0],
                ["B", "C", 3.0],
                ["C", "D", 4.0],
                ["D", "A", 5.0],
                ["A", "C", 1.0],
            ],
        },
    }
    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["solver_id"] == "exact"
    assert data["status"] == "COMPLETED"
    assert data["is_feasible"] is True
    assert data["objective_value"] == 14.0
    assert data["optimality_status"] == "proven_optimal"
    assert data["runtime_seconds"] >= 0.0
    assert len(data["constraint_violations"]) == 0

