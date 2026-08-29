from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app

client = TestClient(app)


def test_me_requires_authentication() -> None:
    response = client.get("/api/me")

    assert response.status_code == 401


def test_me_returns_current_user_when_authenticated() -> None:
    app.dependency_overrides[get_current_user] = lambda: TokenPayload(
        user_id="user-123", email="test@example.com"
    )
    try:
        response = client.get("/api/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"id": "user-123", "email": "test@example.com"}
