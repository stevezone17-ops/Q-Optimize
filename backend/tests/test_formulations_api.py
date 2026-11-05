"""Integration tests for formulation API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_generate_and_get_formulation_by_problem_id(client: TestClient):
    """Create a problem, generate formulation, and retrieve by formulation ID."""
    # 1. Create a Max-Cut problem
    prob_res = client.post(
        "/api/v1/problems",
        json={
            "name": "API Max-Cut Problem",
            "problem_type": "max_cut",
            "instance": {
                "nodes": ["A", "B", "C"],
                "edges": [["A", "B", 2.0], ["B", "C", 3.0]],
            },
        },
    )
    assert prob_res.status_code == 201
    problem_id = prob_res.json()["id"]

    # 2. Generate formulation
    gen_res = client.post(
        "/api/v1/formulations/generate",
        json={"problem_id": problem_id},
    )
    assert gen_res.status_code == 201
    formulation = gen_res.json()
    assert formulation["problem_id"] == problem_id
    assert formulation["qubo"] is not None
    assert formulation["ising"] is not None
    assert len(formulation["qubo"]["variable_order"]) == 3
    assert len(formulation["ising"]["variable_order"]) == 3

    formulation_id = formulation["id"]

    # 3. Retrieve formulation
    get_res = client.get(f"/api/v1/formulations/{formulation_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == formulation_id

    # 4. Get metadata
    meta_res = client.get(f"/api/v1/formulations/{formulation_id}/metadata")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["formulation_id"] == formulation_id
    assert len(meta_data["variable_order"]) == 3

    # 5. Export coefficients
    export_res = client.get(f"/api/v1/formulations/{formulation_id}/export?format=all")
    assert export_res.status_code == 200
    exp = export_res.json()
    assert "qubo_dense_matrix" in exp
    assert "ising_latex" in exp


def test_generate_formulation_direct_adhoc(client: TestClient):
    """Generate formulation directly from instance data without pre-registering."""
    req_payload = {
        "problem_type": "assignment",
        "instance": {
            "agents": ["A1", "A2"],
            "tasks": ["T1", "T2"],
            "cost_matrix": [[5.0, 9.0], [2.0, 6.0]],
        },
        "penalty_coefficients": {"A": 15.0, "B": 15.0},
    }
    gen_res = client.post("/api/v1/formulations/generate", json=req_payload)
    assert gen_res.status_code == 201
    data = gen_res.json()
    assert data["qubo"]["penalties"]["A"] == 15.0
    assert len(data["qubo"]["variable_order"]) == 4


def test_qubo_only_and_ising_only_endpoints(client: TestClient):
    """Test /qubo and /ising endpoints individually."""
    # 1. QUBO only
    qubo_res = client.post(
        "/api/v1/formulations/qubo",
        json={
            "problem_type": "max_cut",
            "instance": {
                "nodes": ["U", "V"],
                "edges": [["U", "V", 4.0]],
            },
        },
    )
    assert qubo_res.status_code == 200
    qubo = qubo_res.json()
    assert qubo["variable_order"] == ["U", "V"]
    assert qubo["quadratic_terms"]["U,V"] == 8.0

    # 2. Ising from QUBO
    ising_res = client.post(
        "/api/v1/formulations/ising",
        json={"qubo": qubo},
    )
    assert ising_res.status_code == 200
    ising = ising_res.json()
    assert ising["couplings"]["Z_U,Z_V"] == 2.0  # J = b / 4 = 8 / 4 = 2.0


def test_verify_formulation_endpoint(client: TestClient):
    """Test /formulations/verify endpoint."""
    verify_payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 1.0], ["B", "C", 2.0]],
        },
    }
    res = client.post("/api/v1/formulations/verify", json=verify_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_verified"] is True
    assert data["num_states_tested"] == 8
    assert data["max_energy_discrepancy"] < 1e-8
