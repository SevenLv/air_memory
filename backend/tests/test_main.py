"""Tests for the FastAPI application entry point."""

from fastapi.testclient import TestClient

from air_memory.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test that GET /health returns 200 and correct response body."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
