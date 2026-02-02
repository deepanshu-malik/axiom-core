"""Tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient

from axiom.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "axiom-core"}


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Axiom API"
    assert "version" in data
    assert data["docs"] == "/docs"
