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
    JobObservations,
    KeywordImportance,
    KeywordObservation,
    LanguageObservation,
    MatchType,
    RequirementCategory,
    RequirementKind,
    RequirementObservation,
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


def _canned_job_observations() -> JobObservations:
    return JobObservations(
        requirements=[
            RequirementObservation(
                text="3 years Python",
                kind=RequirementKind.required,
                category=RequirementCategory.skill,
                evidence_text="4 years Python",
                evidence_strength=3,
            ),
            RequirementObservation(
                text="Kubernetes",
                kind=RequirementKind.preferred,
                category=RequirementCategory.tool,
                evidence_text=None,
                evidence_strength=0,
            ),
        ],
        keywords=[
            KeywordObservation(
                term="Python", importance=KeywordImportance.high, present_in_resume=True, match_type=MatchType.exact
            ),
            KeywordObservation(
                term="Kubernetes", importance=KeywordImportance.high, present_in_resume=False, match_type=MatchType.none
            ),
        ],
        sections=SectionsObservation(
            contact=ContactObservation(present=True, has_email=True, has_phone=True),
            summary=SummaryObservation(present=True, quality=SummaryQuality.strong),
            experience=SectionPresence(present=True),
            education=SectionPresence(present=True),
            skills=SectionPresence(present=True),
        ),
        bullets=[],
        ats_risks=[],
        language=LanguageObservation(spelling_grammar_issue_count=0, passive_voice_count=0, filler_word_count=0),
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


# --- job-specific analysis ---

JOB_BODY = {"target_role": "Backend Engineer", "job_description": "We need a Python engineer with 3+ years of experience building APIs."}


def test_job_analysis_success(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_job", lambda _r, _j: _canned_job_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.post(f"/api/resumes/{resume_id}/analyze-job", json=JOB_BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "job"
    assert body["target_role"] == "Backend Engineer"
    assert 0 <= body["overall_score"] <= 100
    assert len(body["categories"]) == 6
    assert len(body["requirements"]) == 2
    assert body["job_fit"]["strong"] == ["3 years Python"]
    assert body["job_fit"]["missing"] == ["Kubernetes"]
    assert "Kubernetes" in body["missing_keywords"]


def test_job_analysis_requires_job_description(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.post(f"/api/resumes/{resume_id}/analyze-job", json={"job_description": "short"})

    assert response.status_code == 422  # fails min_length validation


def test_job_analysis_surfaces_ai_failure_as_502(client, monkeypatch):
    def _boom(_r, _j):
        raise GeminiError("rate-limited")

    monkeypatch.setattr(analyses_api, "analyze_resume_job", _boom)
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.post(f"/api/resumes/{resume_id}/analyze-job", json=JOB_BODY)

    assert response.status_code == 502


def test_cannot_job_analyze_another_users_resume(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_job", lambda _r, _j: _canned_job_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    _as_user(USER_B)
    response = client.post(f"/api/resumes/{resume_id}/analyze-job", json=JOB_BODY)

    assert response.status_code == 404


def test_job_analysis_persists_and_reloads_details(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_job", lambda _r, _j: _canned_job_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze-job", json=JOB_BODY).json()["id"]

    fetched = client.get(f"/api/analyses/{analysis_id}").json()

    assert fetched["analysis_type"] == "job"
    assert fetched["target_role"] == "Backend Engineer"
    assert len(fetched["requirements"]) == 2
    assert fetched["job_fit"]["missing"] == ["Kubernetes"]


def test_version_analysis_reports_previous_score(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    original_id = _create_resume(client)

    # analyze the original (the "before")
    before = client.post(f"/api/resumes/{original_id}/analyze").json()

    # create a tailored version and analyze it (the "after")
    version_id = client.post(
        f"/api/resumes/{original_id}/versions", json={"edited_text": "Improved resume text."}
    ).json()["id"]
    after = client.post(f"/api/resumes/{version_id}/analyze").json()

    assert after["previous_score"] == before["overall_score"]


def test_original_analysis_has_no_previous_score(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)

    result = client.post(f"/api/resumes/{resume_id}/analyze").json()

    assert result["previous_score"] is None


def test_download_report_txt(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    response = client.get(f"/api/analyses/{analysis_id}/report?format=txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.content.decode("utf-8")
    assert "Resume Quality Report" in body
    assert "Overall score:" in body
    assert "heuristic estimate" in body


def test_download_report_pdf(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_job", lambda _r, _j: _canned_job_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze-job", json=JOB_BODY).json()["id"]

    response = client.get(f"/api/analyses/{analysis_id}/report?format=pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_cannot_download_another_users_report(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    _as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis_id}/report?format=txt")

    assert response.status_code == 404


def test_delete_analysis(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    delete_response = client.delete(f"/api/analyses/{analysis_id}")
    get_response = client.get(f"/api/analyses/{analysis_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_cannot_delete_another_users_analysis(client, monkeypatch):
    monkeypatch.setattr(analyses_api, "analyze_resume_general", lambda _text: _canned_observations())
    _as_user(USER_A)
    resume_id = _create_resume(client)
    analysis_id = client.post(f"/api/resumes/{resume_id}/analyze").json()["id"]

    _as_user(USER_B)
    response = client.delete(f"/api/analyses/{analysis_id}")

    assert response.status_code == 404
