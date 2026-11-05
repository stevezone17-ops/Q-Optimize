"""Integration and API tests for Stage 5.7: Unified QAOA Execution Pipeline and Persistence."""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline
from backend.app.solvers.quantum.models import (
    QAOAExecutionRequest,
    QAOAConfiguration,
    QuantumExecutionStatus,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_list_quantum_solvers_and_backends_endpoints(client: TestClient):
    """Verify solver discovery, backend enumeration, and metadata schemas."""
    # 1. Main listing
    res = client.get("/api/v1/solvers/quantum")
    assert res.status_code == 200
    data = res.json()
    assert "solvers" in data
    assert any(s["solver_id"] == "qaoa" for s in data["solvers"])
    assert "backends" in data
    assert "hardware_transparency_note" in data

    # 2. Backends endpoint
    res_b = client.get("/api/v1/solvers/quantum/backends")
    assert res_b.status_code == 200
    backends = res_b.json()
    assert any(b["backend_id"] == "aer_simulator" for b in backends)

    # 3. QAOA metadata
    res_m = client.get("/api/v1/solvers/quantum/qaoa")
    assert res_m.status_code == 200
    meta = res_m.json()
    assert meta["solver_id"] == "qaoa"
    assert "parameter_schema" in meta
    assert "p_depth" in meta["parameter_schema"]


def test_validate_quantum_request_endpoint(client: TestClient):
    """Verify request validation for valid and invalid instances."""
    # Valid Max-Cut
    valid_payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 1.0], ["B", "C", 2.0]]
        },
        "config": {
            "p_depth": 1,
            "shots": 500
        }
    }
    res = client.post("/api/v1/solvers/quantum/validate", json=valid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["num_qubits"] == 3
    assert data["resource_check"] == "PASSED"

    # Invalid shots (> 50000)
    invalid_shots = dict(valid_payload)
    invalid_shots["config"] = {"p_depth": 1, "shots": 100000}
    res_inv = client.post("/api/v1/solvers/quantum/validate", json=invalid_shots)
    assert res_inv.status_code in (400, 422)


def test_synchronous_qaoa_execution(client: TestClient):
    """Verify synchronous end-to-end QAOA execution on a triangle Max-Cut instance."""
    payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["0", "1", "2"],
            "edges": [["0", "1", 2.0], ["1", "2", 3.0], ["0", "2", 1.0]]
        },
        "config": {
            "p_depth": 1,
            "shots": 500,
            "optimizer": "COBYLA",
            "max_iterations": 15,
            "seed": 42,
            "simulation_mode": "statevector_exact",
        }
    }
    res = client.post("/api/v1/solvers/quantum/qaoa/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["solver_id"] == "qaoa"
    assert data["status"] == "COMPLETED"
    assert data["objective_value"] is not None
    assert data["is_feasible"] is True
    assert len(data["optimal_gamma"]) == 1
    assert len(data["optimal_beta"]) == 1
    assert data["runtime_seconds"] > 0.0
    assert "decoding_summary" in data
    assert data["decoding_summary"]["total_samples"] == 500


def test_asynchronous_qaoa_execution_and_polling(client: TestClient):
    """Verify background dispatch, status polling, and execution history persistence."""
    payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B"],
            "edges": [["A", "B", 4.0]]
        },
        "config": {
            "p_depth": 1,
            "shots": 200,
            "max_iterations": 10,
            "seed": 99,
        }
    }
    # 1. Dispatch async
    res_async = client.post("/api/v1/solvers/quantum/qaoa/execute/async", json=payload)
    assert res_async.status_code == 200
    status_data = res_async.json()
    exec_id = status_data["execution_id"]
    assert status_data["solver_id"] == "qaoa"

    # 2. Poll until completed (with timeout safety)
    is_done = False
    for _ in range(30):
        res_poll = client.get(f"/api/v1/solvers/quantum/qaoa/executions/{exec_id}/status")
        assert res_poll.status_code == 200
        poll_data = res_poll.json()
        if poll_data["is_completed"]:
            is_done = True
            break
        time.sleep(0.2)

    assert is_done is True

    # 3. Retrieve full record
    res_rec = client.get(f"/api/v1/solvers/quantum/qaoa/executions/{exec_id}")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["execution_id"] == exec_id
    assert rec_data["status"] == "COMPLETED"
    assert rec_data["result"] is not None

    # 4. Check listing
    res_list = client.get("/api/v1/solvers/quantum/qaoa/executions")
    assert res_list.status_code == 200
    executions = res_list.json()
    assert any(e["execution_id"] == exec_id for e in executions)


def test_cancel_qaoa_execution(client: TestClient):
    """Verify cooperative cancellation endpoint."""
    payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["0", "1"],
            "edges": [["0", "1", 1.0]]
        },
        "config": {
            "p_depth": 1,
            "shots": 200,
            "max_iterations": 50,
        }
    }
    res_async = client.post("/api/v1/solvers/quantum/qaoa/execute/async", json=payload)
    exec_id = res_async.json()["execution_id"]

    # Cancel immediately
    res_cancel = client.post(f"/api/v1/solvers/quantum/qaoa/executions/{exec_id}/cancel")
    assert res_cancel.status_code == 200
    data = res_cancel.json()
    assert data["execution_id"] == exec_id
