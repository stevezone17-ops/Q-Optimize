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
    assert data["version"] == "1.0.0"
    assert "phase" in data
    assert "max_cut" in data["supported_problems"]
    assert "assignment" in data["supported_problems"]
    assert "tsp" in data["supported_problems"]


def test_health_probes(client):
    live_res = client.get("/api/v1/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "live"

    ready_res = client.get("/api/v1/health/ready")
    assert ready_res.status_code in (200, 503)
    assert "status" in ready_res.json()


def test_health_degraded_on_resource_pressure(client, monkeypatch):
    from backend.app.workers.job_queue import job_queue_manager

    monkeypatch.setattr(
        job_queue_manager,
        "check_system_resources",
        lambda: (False, "Memory usage 99.5% exceeds threshold"),
    )
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert any("resource_pressure" in r for r in data["degraded_reasons"])
