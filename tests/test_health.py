from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Australian Legal Case Analyser API"
    assert data["version"] == "1.0.0"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["model"] == "Gemini 2.5 Flash"
    assert "index_exists" in data
