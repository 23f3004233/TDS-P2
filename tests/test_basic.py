"""Basic tests for the quiz solver."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "LLM Quiz Solver"
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_quiz_endpoint_missing_fields():
    """Test quiz endpoint with missing fields."""
    response = client.post("/quiz", json={})
    assert response.status_code == 422  # Validation error


def test_quiz_endpoint_invalid_secret():
    """Test quiz endpoint with invalid secret."""
    response = client.post(
        "/quiz",
        json={
            "email": settings.email,
            "secret": "wrong_secret",
            "url": "https://example.com/quiz"
        }
    )
    assert response.status_code == 403


def test_quiz_endpoint_invalid_email():
    """Test quiz endpoint with wrong email."""
    response = client.post(
        "/quiz",
        json={
            "email": "wrong@example.com",
            "secret": settings.quiz_secret,
            "url": "https://example.com/quiz"
        }
    )
    assert response.status_code == 403


def test_quiz_endpoint_valid_request():
    """Test quiz endpoint with valid request."""
    if not settings.quiz_secret:
        pytest.skip("QUIZ_SECRET not set")
    
    response = client.post(
        "/quiz",
        json={
            "email": settings.email,
            "secret": settings.quiz_secret,
            "url": "https://tds-llm-analysis.s-anand.net/demo"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"