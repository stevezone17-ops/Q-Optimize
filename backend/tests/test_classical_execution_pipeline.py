"""Tests for Classical Solver Execution Pipeline (Stage 4.5)."""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.models import SolverStatus, OptimalityStatus
from backend.app.solvers.classical.execution import ClassicalExecutionPipeline


@pytest.fixture
def client():
    return TestClient(app)


def test_sync_execution_pipeline(client: TestClient):
    """POST /api/v1/solvers/classical/execute runs synchronously and records execution."""
    payload = {
        "solver_id": "exact",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C"],
            "edges": [
                ["A", "B", 2.0],
                ["B", "C", 3.0],
                ["C", "A", 1.0],
            ],
        },
        "background": False,
    }

    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["solver_id"] == "exact"
    assert data["status"] == "COMPLETED"
    assert data["is_feasible"] is True
    assert data["objective_value"] == 5.0
    assert "execution_id" in data

    # Verify execution record is queryable
    exec_id = data["execution_id"]
    res_record = client.get(f"/api/v1/solvers/classical/executions/{exec_id}")
    assert res_record.status_code == 200
    rec = res_record.json()
    assert rec["execution_id"] == exec_id
    assert rec["status"] == "COMPLETED"
    assert rec["result"] is not None
    assert rec["result"]["objective_value"] == 5.0


def test_async_background_execution_pipeline(client: TestClient):
    """POST /api/v1/solvers/classical/execute with background=True returns 202 Accepted and completes asynchronously."""
    payload = {
        "solver_id": "genetic_algorithm",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                ["A", "B", 1.0],
                ["B", "C", 2.0],
                ["C", "D", 1.0],
                ["D", "A", 2.0],
            ],
        },
        "background": True,
        "config": {
            "population_size": 20,
            "generations": 20,
            "mutation_rate": 0.05,
        },
    }

    res = client.post("/api/v1/solvers/classical/execute", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert "execution_id" in data
    exec_id = data["execution_id"]
    assert data["status"] in ("PENDING", "RUNNING")

    # Poll status endpoint until completed (with timeout safety)
    max_wait_seconds = 5.0
    start_time = time.time()
    final_status = None

    while time.time() - start_time < max_wait_seconds:
        status_res = client.get(f"/api/v1/solvers/classical/executions/{exec_id}/status")
        assert status_res.status_code == 200
        st = status_res.json()
        if st["is_completed"]:
            final_status = st["status"]
            break
        time.sleep(0.05)

    assert final_status == "COMPLETED"

    # Verify full result retrieval
    full_res = client.get(f"/api/v1/solvers/classical/executions/{exec_id}")
    assert full_res.status_code == 200
    full_data = full_res.json()
    assert full_data["status"] == "COMPLETED"
    assert full_data["result"] is not None
    assert full_data["result"]["is_feasible"] is True


def test_explicit_async_execute_endpoint(client: TestClient):
    """POST /api/v1/solvers/classical/execute/async returns 202 and tracks progress."""
    payload = {
        "solver_id": "simulated_annealing",
        "problem_type": "assignment",
        "instance": {
            "agents": ["A1", "A2"],
            "tasks": ["T1", "T2"],
            "cost_matrix": [[5.0, 2.0], [1.0, 6.0]],
        },
        "config": {
            "max_iterations": 50,
            "steps_per_temperature": 5,
        },
    }

    res = client.post("/api/v1/solvers/classical/execute/async", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert "execution_id" in data


def test_execution_status_404_on_unknown_id(client: TestClient):
    """Non-existent execution IDs return 404."""
    res = client.get("/api/v1/solvers/classical/executions/non_existent_exec_999")
    assert res.status_code == 404

    res_st = client.get("/api/v1/solvers/classical/executions/non_existent_exec_999/status")
    assert res_st.status_code == 404


def test_list_executions(client: TestClient):
    """GET /api/v1/solvers/classical/executions returns list of recent runs."""
    res = client.get("/api/v1/solvers/classical/executions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_cancel_execution(client: TestClient):
    """POST /api/v1/solvers/classical/executions/{id}/cancel sends cooperative cancellation."""
    # Submit a background execution
    payload = {
        "solver_id": "genetic_algorithm",
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 1.0]],
        },
        "background": True,
        "config": {"generations": 500},
    }
    res = client.post("/api/v1/solvers/classical/execute/async", json=payload)
    exec_id = res.json()["execution_id"]

    cancel_res = client.post(f"/api/v1/solvers/classical/executions/{exec_id}/cancel")
    assert cancel_res.status_code == 200
    data = cancel_res.json()
    assert data["execution_id"] == exec_id
