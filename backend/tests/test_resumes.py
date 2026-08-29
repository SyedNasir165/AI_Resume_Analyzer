import io
import uuid

from docx import Document

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.main import app

USER_A = TokenPayload(user_id=str(uuid.uuid4()), email="a@example.com")
USER_B = TokenPayload(user_id=str(uuid.uuid4()), email="b@example.com")


def _as_user(token_payload: TokenPayload) -> None:
    app.dependency_overrides[get_current_user] = lambda: token_payload


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def teardown_function() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def test_upload_txt_resume_success(client) -> None:
    _as_user(USER_A)

    resume_text = (
        b"Jane Doe\nSoftware Engineer with 5 years of experience building backend systems, "
        b"leading a team of four engineers, and shipping production APIs used by thousands "
        b"of customers daily."
    )
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", resume_text, "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_confirmation"
    assert body["file_type"] == "txt"
    assert "Jane Doe" in body["extracted_text"]
    assert body["warnings"] == []


def test_upload_docx_resume_success(client) -> None:
    _as_user(USER_A)
    docx_bytes = _make_docx_bytes(["Jane Doe", "Software Engineer", "Built things at Acme Corp for 5 years."])

    response = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_type"] == "docx"
    assert "Acme Corp" in body["extracted_text"]


def test_upload_rejects_unsupported_extension(client) -> None:
    _as_user(USER_A)

    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.jpg", b"not a real image", "image/jpeg")},
    )

    assert response.status_code == 400


def test_upload_rejects_empty_file(client) -> None:
    _as_user(USER_A)

    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", b"", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_warns_on_corrupt_docx(client) -> None:
    _as_user(USER_A)

    response = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                b"this is not a valid docx file",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 422


def test_paste_text_resume_success(client) -> None:
    _as_user(USER_A)

    response = client.post("/api/resumes/paste", json={"text": "Jane Doe, Software Engineer."})

    assert response.status_code == 201
    assert response.json()["file_type"] == "txt"


def test_paste_rejects_empty_text(client) -> None:
    _as_user(USER_A)

    response = client.post("/api/resumes/paste", json={"text": "   "})

    assert response.status_code == 400


def test_list_resumes_only_returns_current_users_resumes(client) -> None:
    _as_user(USER_A)
    client.post("/api/resumes/paste", json={"text": "User A's resume text."})

    _as_user(USER_B)
    client.post("/api/resumes/paste", json={"text": "User B's resume text."})

    response = client.get("/api/resumes")

    assert response.status_code == 200
    resumes = response.json()
    assert len(resumes) == 1


def test_confirm_resume_marks_it_confirmed(client) -> None:
    _as_user(USER_A)
    created = client.post("/api/resumes/paste", json={"text": "Original text."}).json()

    response = client.patch(f"/api/resumes/{created['id']}/confirm", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["confirmed_at"] is not None


def test_confirm_resume_can_apply_edited_text(client) -> None:
    _as_user(USER_A)
    created = client.post("/api/resumes/paste", json={"text": "Original text."}).json()

    response = client.patch(f"/api/resumes/{created['id']}/confirm", json={"edited_text": "Corrected text."})

    assert response.status_code == 200
    assert response.json()["extracted_text"] == "Corrected text."


def test_cannot_access_another_users_resume(client) -> None:
    _as_user(USER_A)
    created = client.post("/api/resumes/paste", json={"text": "User A's private resume."}).json()

    _as_user(USER_B)
    response = client.get(f"/api/resumes/{created['id']}")

    assert response.status_code == 404


def test_delete_resume_removes_it(client) -> None:
    _as_user(USER_A)
    created = client.post("/api/resumes/paste", json={"text": "To be deleted."}).json()

    delete_response = client.delete(f"/api/resumes/{created['id']}")
    get_response = client.get(f"/api/resumes/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
