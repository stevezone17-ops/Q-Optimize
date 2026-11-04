"""Tests for health check endpoints."""


def test_root_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data
    assert "database" in data


def test_api_v1_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "phase" in data
    assert "max_cut" in data["supported_problems"]
    assert "assignment" in data["supported_problems"]
    assert "tsp" in data["supported_problems"]
