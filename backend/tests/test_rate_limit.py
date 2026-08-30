import uuid

import app.api.analyses as analyses_api
from app.api.deps import ai_rate_limiter, get_current_user
from app.core.rate_limit import RateLimiter
from app.core.security import TokenPayload
from app.main import app
from tests.test_analyses import _canned_observations

USER = TokenPayload(user_id=str(uuid.uuid4()), email="rl@example.com")


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def test_rate_limiter_unit_allows_then_blocks():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("k") is True
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    # A different key has its own budget.
    assert limiter.allow("other") is True


def test_rate_limiter_is_per_key():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False


def test_analyze_endpoint_returns_429_when_over_limit(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _t: _canned_observations())
    app.dependency_overrides[get_current_user] = lambda: USER
    # Shrink the shared limiter for this test.
    ai_rate_limiter.max_requests = 2
    ai_rate_limiter.reset()

    resume_id = client.post("/api/resumes/paste", json={"text": "Jane Doe."}).json()["id"]

    first = client.post(f"/api/resumes/{resume_id}/analyze")
    second = client.post(f"/api/resumes/{resume_id}/analyze")
    third = client.post(f"/api/resumes/{resume_id}/analyze")

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429

    # Restore a generous limit so other tests are unaffected.
    ai_rate_limiter.max_requests = 20
    ai_rate_limiter.reset()
