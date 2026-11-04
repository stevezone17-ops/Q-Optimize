"""Tests for problem API endpoints."""


def test_create_and_get_max_cut_problem(client):
    payload = {
        "name": "Max-Cut 3-Node Test",
        "problem_type": "max_cut",
        "description": "Integration test for Max-Cut",
        "instance": {
            "nodes": ["Node_1", "Node_2", "Node_3"],
            "edges": [
                ["Node_1", "Node_2", 1.5],
                ["Node_2", "Node_3", 2.0],
            ],
        },
    }
    response = client.post("/api/v1/problems", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Max-Cut 3-Node Test"
    assert created["problem_type"] == "max_cut"
    assert "id" in created

    # Test retrieval
    get_res = client.get(f"/api/v1/problems/{created['id']}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == created["id"]
    assert retrieved["instance"]["nodes"] == ["Node_1", "Node_2", "Node_3"]


def test_create_invalid_problem_fails(client):
    invalid_payload = {
        "name": "Invalid Assignment",
        "problem_type": "assignment",
        "instance": {
            "agents": ["A1", "A2"],
            "tasks": ["T1"],
            "cost_matrix": [[1.0]],  # Mismatched rows and columns
        },
    }
    response = client.post("/api/v1/problems", json=invalid_payload)
    assert response.status_code == 422


def test_parse_draft_workflow(client):
    req_payload = {
        "text": "We need to partition an undirected graph of 4 servers into two clusters to maximize severed connections",
        "problem_type_hint": "max_cut",
    }
    response = client.post("/api/v1/problems/parse-draft", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["problem_type"] == "max_cut"
    assert data["requires_user_confirmation"] is True
    assert "suggested_instance" in data
    assert "nodes" in data["suggested_instance"]
