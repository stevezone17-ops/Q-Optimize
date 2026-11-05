"""Tests for classical solver architecture, registry, interfaces, and API endpoints (Stage 4.1)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.registry import ClassicalSolverRegistry
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.exceptions import (
    SolverNotFoundError,
    SolverNotImplementedError,
    UnsupportedProblemTypeError,
)
from backend.app.solvers.classical.models import (
    SolverStatus,
    OptimalityStatus,
    SolverRequest,
    SolverResult,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_registry_registration_and_discovery():
    """Verify registry contains all 3 planned algorithms with correct metadata."""
    solvers = ClassicalSolverRegistry.list_all()
    assert len(solvers) == 3

    solver_ids = {s.solver_id for s in solvers}
    assert solver_ids == {"exact", "genetic_algorithm", "simulated_annealing"}

    for s in solvers:
        assert s.is_implemented is False
        assert len(s.supported_problem_types) == 3
        assert ProblemType.MAX_CUT in s.supported_problem_types
        assert ProblemType.ASSIGNMENT in s.supported_problem_types
        assert ProblemType.TSP in s.supported_problem_types


def test_solver_factory_get():
    """Verify factory returns registered solver instances and raises on unknown solver."""
    exact_solver = ClassicalSolverFactory.get_solver("exact")
    assert exact_solver.solver_id == "exact"
    assert exact_solver.name == "Exact Classical Solver"

    ga_solver = ClassicalSolverFactory.get_solver("genetic_algorithm")
    assert ga_solver.solver_id == "genetic_algorithm"

    sa_solver = ClassicalSolverFactory.get_solver("simulated_annealing")
    assert sa_solver.solver_id == "simulated_annealing"

    with pytest.raises(SolverNotFoundError):
        ClassicalSolverFactory.get_solver("non_existent_quantum_solver")


def test_unimplemented_solver_solve_raises():
    """Verify that calling solve() on stubs in Stage 4.1 raises SolverNotImplementedError."""
    exact_solver = ClassicalSolverFactory.get_solver("exact")
    with pytest.raises(SolverNotImplementedError, match="Stage 4.2"):
        exact_solver.solve(
            problem_type=ProblemType.MAX_CUT,
            instance={"nodes": ["A", "B"], "edges": [["A", "B", 1.0]]},
        )


def test_solver_request_validation():
    """Verify Pydantic models validate properly."""
    req = SolverRequest(
        solver_id="Exact ",  # test trimming & lowercasing
        problem_type=ProblemType.MAX_CUT,
        instance={"nodes": ["A", "B"], "edges": [["A", "B", 1.0]]},
        seed=123,
    )
    assert req.solver_id == "exact"
    assert req.seed == 123


def test_api_list_classical_solvers(client: TestClient):
    """GET /api/v1/solvers/classical lists all solvers."""
    res = client.get("/api/v1/solvers/classical")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    ids = [item["solver_id"] for item in data]
    assert "exact" in ids
    assert "genetic_algorithm" in ids
    assert "simulated_annealing" in ids


def test_api_get_classical_solver(client: TestClient):
    """GET /api/v1/solvers/classical/{id} returns details or 404."""
    res = client.get("/api/v1/solvers/classical/exact")
    assert res.status_code == 200
    data = res.json()
    assert data["solver_id"] == "exact"
    assert data["is_implemented"] is False
    assert data["stage_introduced"] == "Stage 4.2"

    res_404 = client.get("/api/v1/solvers/classical/unknown_solver")
    assert res_404.status_code == 404


def test_api_validate_solver_config(client: TestClient):
    """POST /api/v1/solvers/classical/validate checks problem support & config."""
    payload = {
        "solver_id": "exact",
        "problem_type": "max_cut",
        "config": {"time_limit_seconds": 30.0, "seed": 99},
    }
    res = client.post("/api/v1/solvers/classical/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["validated_config"]["seed"] == 99

    # Test invalid time limit
    invalid_payload = {
        "solver_id": "exact",
        "problem_type": "max_cut",
        "config": {"time_limit_seconds": -5.0},
    }
    res_inv = client.post("/api/v1/solvers/classical/validate", json=invalid_payload)
    assert res_inv.status_code == 400


def test_api_execute_unimplemented_solver_returns_501(client: TestClient):
    """POST /api/v1/solvers/classical/execute returns 501 Not Implemented in Stage 4.1."""
    payload = {
        "solver_id": "exact",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B"],
            "edges": [["A", "B", 1.0]],
        },
    }
    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 501
    assert "Stage 4.2" in res.json()["detail"]
