import uuid

import app.api.coach as coach_api
from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app
from app.schemas.coach import BulletRewrite, CoachQuestions, FactSource, FactUsed
from app.services.gemini import GeminiError

USER_A = TokenPayload(user_id=str(uuid.uuid4()), email="a@example.com")


def _as_user(token_payload: TokenPayload) -> None:
    app.dependency_overrides[get_current_user] = lambda: token_payload


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def test_questions_requires_auth(client):
    response = client.post("/api/coach/questions", json={"bullet_text": "Did stuff."})
    assert response.status_code == 401


def test_questions_success(client, monkeypatch):
    monkeypatch.setattr(
        coach_api, "coach_questions", lambda _t: CoachQuestions(questions=["How many users?", "What tools?"])
    )
    _as_user(USER_A)

    response = client.post("/api/coach/questions", json={"bullet_text": "Built a thing."})

    assert response.status_code == 200
    assert response.json()["questions"] == ["How many users?", "What tools?"]


def test_rewrite_success_with_verification(client, monkeypatch):
    def _rewrite(bullet, answers):
        assert answers == [("How many users?", "50,000")]
        return BulletRewrite(
            improved_bullet="Built a REST API serving 50,000 daily users.",
            facts_used=[
                FactUsed(text="REST API", source=FactSource.resume),
                FactUsed(text="50,000 daily users", source=FactSource.user_answer),
            ],
        )

    monkeypatch.setattr(coach_api, "coach_rewrite", _rewrite)
    _as_user(USER_A)

    response = client.post(
        "/api/coach/rewrite",
        json={"bullet_text": "Built an API.", "answers": [{"question": "How many users?", "answer": "50,000"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert "50,000" in body["improved_bullet"]
    sources = {f["source"] for f in body["facts_used"]}
    assert sources == {"resume", "user_answer"}


def test_rewrite_surfaces_ai_failure_as_502(client, monkeypatch):
    def _boom(_b, _a):
        raise GeminiError("rate-limited")

    monkeypatch.setattr(coach_api, "coach_rewrite", _boom)
    _as_user(USER_A)

    response = client.post("/api/coach/rewrite", json={"bullet_text": "Built an API.", "answers": []})

    assert response.status_code == 502
