"""Integration tests for problem domain API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_list_problem_types_endpoint(client: TestClient):
    """GET /api/v1/problems/types returns supported types with metadata."""
    res = client.get("/api/v1/problems/types")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    types = [item["type"] for item in data]
    assert "max_cut" in types
    assert "assignment" in types
    assert "tsp" in types

    max_cut_info = next(item for item in data if item["type"] == "max_cut")
    assert max_cut_info["objective_sense"] == "maximize"
    assert "max" in max_cut_info["mathematical_form"]


def test_validate_problem_direct_endpoint(client: TestClient):
    """POST /api/v1/problems/validate checks ad-hoc problem instance."""
    # Valid Max-Cut
    res_valid = client.post(
        "/api/v1/problems/validate",
        json={
            "problem_type": "max_cut",
            "instance": {
                "nodes": ["A", "B"],
                "edges": [["A", "B", 1.0]],
            },
        },
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["is_valid"] is True
    assert data["status"] == "valid"
    assert len(data["issues"]) == 0
    assert len(data["variables"]) == 1

    # Invalid Max-Cut (self-loop)
    res_invalid = client.post(
        "/api/v1/problems/validate",
        json={
            "problem_type": "max_cut",
            "instance": {
                "nodes": ["A", "B"],
                "edges": [["A", "A", 1.0]],
            },
        },
    )
    assert res_invalid.status_code == 200
    data_inv = res_invalid.json()
    assert data_inv["is_valid"] is False
    assert data_inv["status"] == "invalid"
    assert len(data_inv["issues"]) > 0


def test_evaluate_direct_endpoint(client: TestClient):
    """POST /api/v1/problems/evaluate-direct evaluates solution without registering."""
    payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["X", "Y"],
            "edges": [["X", "Y", 10.0]],
        },
        "candidate": {"X": 0, "Y": 1},
    }
    res = client.post("/api/v1/problems/evaluate-direct", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_feasible"] is True
    assert data["objective_value"] == 10.0
    assert data["problem_type"] == "max_cut"


def test_problem_metadata_and_evaluate_by_id(client: TestClient):
    """Create problem, fetch metadata, validate, and evaluate candidate by ID."""
    # 1. Create registered problem
    create_payload = {
        "name": "Metadata & Evaluation Test Assignment",
        "problem_type": "assignment",
        "description": "3x3 Assignment Instance",
        "instance": {
            "agents": ["A1", "A2", "A3"],
            "tasks": ["T1", "T2", "T3"],
            "cost_matrix": [
                [9.0, 2.0, 7.0],
                [6.0, 4.0, 3.0],
                [5.0, 8.0, 1.0],
            ],
        },
    }
    create_res = client.post("/api/v1/problems", json=create_payload)
    assert create_res.status_code == 201
    prob = create_res.json()
    problem_id = prob["id"]
    assert prob["validation_status"] == "valid"
    assert len(prob["variables"]) > 0

    # 2. Get metadata
    meta_res = client.get(f"/api/v1/problems/{problem_id}/metadata")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["problem_id"] == problem_id
    assert meta_data["metadata"]["is_square"] is True
    assert meta_data["metadata"]["agent_count"] == 3

    # 3. Validate by ID
    val_res = client.post(f"/api/v1/problems/{problem_id}/validate")
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    # 4. Evaluate optimal candidate
    eval_payload = {
        "candidate": {
            "A1": "T2",
            "A2": "T1",
            "A3": "T3",
        }
    }
    eval_res = client.post(f"/api/v1/problems/{problem_id}/evaluate", json=eval_payload)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["is_feasible"] is True
    assert eval_data["objective_value"] == 9.0
    assert eval_data["problem_id"] == problem_id

    # 5. Evaluate non-existent problem ID returns 404
    non_existent_res = client.post("/api/v1/problems/non_existent_id_12345/evaluate", json=eval_payload)
    assert non_existent_res.status_code == 404

