"""Test configuration and fixtures using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.middleware import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter_for_tests():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

