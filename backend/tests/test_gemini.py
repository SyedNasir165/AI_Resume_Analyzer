import json
from types import SimpleNamespace

import httpx
import pytest

import app.services.gemini as gemini
from app.schemas.analysis import GeneralObservations, JobObservations
from app.services.gemini import GeminiError, analyze_resume_general, analyze_resume_job

VALID_OBSERVATIONS = {
    "sections": {
        "contact": {"present": True, "has_email": True, "has_phone": True},
        "summary": {"present": True, "quality": "strong"},
        "experience": {"present": True},
        "education": {"present": True},
        "skills": {"present": True},
    },
    "bullets": [{"text": "Did a thing.", "section": "experience", "issues": ["no_metric"]}],
    "date_consistency": {"consistent_format": True, "has_overlaps": False},
    "ats_risks": [],
    "language": {"spelling_grammar_issue_count": 0, "passive_voice_count": 0, "filler_word_count": 0},
    "findings": [],
}


def _fake_settings(api_key="test-key", model="gemini-2.0-flash"):
    return SimpleNamespace(gemini_api_key=api_key, gemini_model=model)


def _gemini_response(payload_text: str, status_code: int = 200):
    body = {"candidates": [{"content": {"parts": [{"text": payload_text}]}}]}

    class _Resp:
        def __init__(self):
            self.status_code = status_code

        def json(self):
            return body

    return _Resp()


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings(api_key=None))
    with pytest.raises(GeminiError):
        analyze_resume_general("some resume text")


def test_valid_response_parses_to_observations(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    monkeypatch.setattr(
        gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(VALID_OBSERVATIONS))
    )
    result = analyze_resume_general("resume text")
    assert isinstance(result, GeneralObservations)
    assert result.sections.contact.has_email is True


def test_malformed_json_raises(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response("not json at all"))
    with pytest.raises(GeminiError):
        analyze_resume_general("resume text")


def test_schema_invalid_json_is_rejected(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    # Valid JSON, but missing required keys / wrong shape.
    monkeypatch.setattr(
        gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps({"unexpected": "shape"}))
    )
    with pytest.raises(GeminiError):
        analyze_resume_general("resume text")


def test_extra_keys_are_rejected(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    payload = {**VALID_OBSERVATIONS, "injected_score": 100}
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(payload)))
    with pytest.raises(GeminiError):
        analyze_resume_general("resume text")


def test_rate_limit_raises(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response("{}", status_code=429))
    with pytest.raises(GeminiError, match="rate-limited"):
        analyze_resume_general("resume text")


def test_network_error_raises(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())

    def _raise(*a, **k):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(gemini.httpx, "post", _raise)
    with pytest.raises(GeminiError):
        analyze_resume_general("resume text")


VALID_JOB_OBSERVATIONS = {
    "requirements": [
        {
            "text": "3 years Python",
            "kind": "required",
            "category": "skill",
            "evidence_text": "4 years Python",
            "evidence_strength": 3,
        }
    ],
    "keywords": [{"term": "Python", "importance": "high", "present_in_resume": True, "match_type": "exact"}],
    "sections": VALID_OBSERVATIONS["sections"],
    "bullets": [],
    "ats_risks": [],
    "language": {"spelling_grammar_issue_count": 0, "passive_voice_count": 0, "filler_word_count": 0},
    "findings": [],
}


def test_job_valid_response_parses(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    monkeypatch.setattr(
        gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(VALID_JOB_OBSERVATIONS))
    )
    result = analyze_resume_job("resume", "job description")
    assert isinstance(result, JobObservations)
    assert result.requirements[0].evidence_strength == 3


def test_job_schema_invalid_is_rejected(monkeypatch):
    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    # evidence_strength out of range (must be 0-3)
    bad = {**VALID_JOB_OBSERVATIONS, "requirements": [{**VALID_JOB_OBSERVATIONS["requirements"][0], "evidence_strength": 9}]}
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(bad)))
    with pytest.raises(GeminiError):
        analyze_resume_job("resume", "job description")


def test_coach_questions_parses(monkeypatch):
    from app.services.gemini import coach_questions

    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    monkeypatch.setattr(
        gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps({"questions": ["How many users?"]}))
    )
    result = coach_questions("Built a thing.")
    assert result.questions == ["How many users?"]


def test_coach_rewrite_parses_and_validates_source_enum(monkeypatch):
    from app.services.gemini import coach_rewrite

    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    good = {"improved_bullet": "Better bullet.", "facts_used": [{"text": "x", "source": "resume"}]}
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(good)))
    result = coach_rewrite("Built a thing.", [])
    assert result.improved_bullet == "Better bullet."


def test_coach_rewrite_rejects_bad_source(monkeypatch):
    from app.services.gemini import coach_rewrite

    monkeypatch.setattr(gemini, "get_settings", lambda: _fake_settings())
    bad = {"improved_bullet": "Better bullet.", "facts_used": [{"text": "x", "source": "made_up"}]}
    monkeypatch.setattr(gemini.httpx, "post", lambda *a, **k: _gemini_response(json.dumps(bad)))
    with pytest.raises(GeminiError):
        coach_rewrite("Built a thing.", [])
