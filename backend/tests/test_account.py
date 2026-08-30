import uuid

import app.api.me as me_api
from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app
from app.services.supabase_admin import SupabaseAdminError

USER = TokenPayload(user_id=str(uuid.uuid4()), email="del@example.com")


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def test_delete_account_requires_auth(client):
    response = client.delete("/api/me")
    assert response.status_code == 401


def test_delete_account_calls_admin_delete(client, monkeypatch):
    called = {}

    def _fake_delete(user_id):
        called["user_id"] = user_id

    monkeypatch.setattr(me_api, "delete_user", _fake_delete)
    app.dependency_overrides[get_current_user] = lambda: USER

    response = client.delete("/api/me")

    assert response.status_code == 204
    assert called["user_id"] == USER.user_id


def test_delete_account_surfaces_admin_failure(client, monkeypatch):
    def _boom(_user_id):
        raise SupabaseAdminError("Account deletion is not configured on the server.")

    monkeypatch.setattr(me_api, "delete_user", _boom)
    app.dependency_overrides[get_current_user] = lambda: USER

    response = client.delete("/api/me")

    assert response.status_code == 502
