from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-resume-analyzer-api"}


def test_root_returns_running_status() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"service": "AI Resume Analyzer API", "status": "running"}
