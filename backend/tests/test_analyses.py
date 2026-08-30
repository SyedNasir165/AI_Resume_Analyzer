import uuid

import pytest

import app.api.analyses as analyses_api
from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app
from app.schemas.analysis import (
    ContactObservation,
    DateConsistencyObservation,
    GeneralObservations,
    LanguageObservation,
    SectionPresence,
    SectionsObservation,
    SummaryObservation,
    SummaryQuality,
)
from app.services.gemini import GeminiError

USER_A = TokenPayload(user_id=str(uuid.uuid4()), email="a@example.com")
USER_B = TokenPayload(user_id=str(uuid.uuid4()), email="b@example.com")


def _as_user(token_payload: TokenPayload) -> None:
    app.dependency_overrides[get_current_user] = lambda: token_payload


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def _canned_observations() -> GeneralObservations:
    return GeneralObservations(
        sections=SectionsObservation(
            contact=ContactObservation(present=True, has_email=True, has_phone=True),
            summary=SummaryObservation(present=True, quality=SummaryQuality.strong),
            experience=SectionPresence(present=True),
            education=SectionPresence(present=True),
            skills=SectionPresence(present=True),
        ),
        bullets=[],
        date_consistency=DateConsistencyObservation(consistent_format=True, has_overlaps=False),
        ats_risks=[],
        language=LanguageObservation(
            spelling_grammar_issue_count=0, passive_voice_count=0, filler_word_count=0
        ),
        findings=[],
    )


def _create_resume(client) -> str:
    return client.post("/api/resumes/paste", json={"text": "Jane Doe, Software Engineer."}).json()["id"]


def test_analyze_resume_success(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.post(f"/api/resumes/{resume_id}/analyze")

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "general"
    assert 0 <= body["overall_score"] <= 100
    assert len(body["categories"]) == 5
    assert body["resume_id"] == resume_id


def test_analyze_resume_surfaces_ai_failure_as_502(client, monkeypatch):
    def _boom(_text):
        raise GeminiError("The analysis service is rate-limited right now.")

    monkeypatch.setattr(analyses_api, "analyze_resume_general", _boom)
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.post(f"/api/resumes/{resume_id}/analyze")

    assert response.status_code == 502
    assert "rate-limited" in response.json()["detail"]


def test_cannot_analyze_another_users_resume(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    _as_user(USER_B)
    response = client.post(f"/api/resumes/{resume_id}/analyze")

    assert response.status_code == 404


def test_get_and_list_analyses(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    get_response = client.get(f"/api/analyses/{analysis_id}")
    list_response = client.get(f"/api/resumes/{resume_id}/analyses")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == analysis_id
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_cannot_read_another_users_analysis(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    _as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis_id}")

    assert response.status_code == 404


def test_score_is_stored_and_reproduced(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    first = client.post(f"/api/resumes/{resume_id}/analyze").json()
    analysis_id = first["id"]
    fetched = client.get(f"/api/analyses/{analysis_id}").json()

    assert first["overall_score"] == fetched["overall_score"]
