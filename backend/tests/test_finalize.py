import io
import uuid

from docx import Document

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app

USER_A = TokenPayload(user_id=str(uuid.uuid4()), email="a@example.com")
USER_B = TokenPayload(user_id=str(uuid.uuid4()), email="b@example.com")

RESUME_TEXT = "Jane Doe\njane.doe@email.com\n- Built an API in 2021\n"


def _as_user(token_payload: TokenPayload) -> None:
    app.dependency_overrides[get_current_user] = lambda: token_payload


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def _create_resume(client, text=RESUME_TEXT) -> str:
    return client.post("/api/resumes/paste", json={"text": text}).json()["id"]


def test_validate_endpoint_returns_report(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.get(f"/api/resumes/{resume_id}/validate")

    assert response.status_code == 200
    body = response.json()
    assert "ok" in body and "checks" in body
    # No parent -> no comparison checks.
    names = {c["name"] for c in body["checks"]}
    assert "Dates preserved" not in names


def test_validate_version_compares_against_original(client):
    _as_user(USER_A)
    original_id = _create_resume(client)
    # A version that drops the year 2021 should trigger the dates warning.
    version = client.post(
        f"/api/resumes/{original_id}/versions", json={"edited_text": "Jane Doe\njane.doe@email.com\n- Built an API\n"}
    ).json()

    response = client.get(f"/api/resumes/{version['id']}/validate")

    body = response.json()
    dates = next(c for c in body["checks"] if c["name"] == "Dates preserved")
    assert dates["status"] == "warning"
    assert "2021" in dates["items"]


def test_export_txt(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)
    stored_text = client.get(f"/api/resumes/{resume_id}").json()["extracted_text"]

    response = client.get(f"/api/resumes/{resume_id}/export?format=txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "attachment" in response.headers["content-disposition"]
    # Export contains exactly the approved resume text — nothing added or removed.
    assert response.content.decode("utf-8") == stored_text


def test_export_docx_is_valid_and_contains_text(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.get(f"/api/resumes/{resume_id}/export?format=docx")

    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
    document = Document(io.BytesIO(response.content))
    joined = "\n".join(p.text for p in document.paragraphs)
    assert "Jane Doe" in joined
    assert "Built an API in 2021" in joined


def test_export_rejects_unknown_format(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)

    response = client.get(f"/api/resumes/{resume_id}/export?format=pdf")

    assert response.status_code == 422  # fails the query pattern


def test_cannot_export_another_users_resume(client):
    _as_user(USER_A)
    resume_id = _create_resume(client)

    _as_user(USER_B)
    response = client.get(f"/api/resumes/{resume_id}/export?format=txt")

    assert response.status_code == 404
