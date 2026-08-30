import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.db.session import get_db
from app.models.resume import Resume
from app.schemas.validation import ValidationReport
from app.services.export import safe_filename, to_docx_bytes, to_txt_bytes
from app.services.validation import validate_resume

router = APIRouter(prefix="/api/resumes", tags=["finalize"])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _get_owned_resume(db: Session, resume_id: uuid.UUID, user_id: str) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or str(resume.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.get("/{resume_id}/validate", response_model=ValidationReport)
def validate_resume_endpoint(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ValidationReport:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)

    original_text: str | None = None
    if resume.parent_resume_id is not None:
        original = db.get(Resume, resume.parent_resume_id)
        # Only compare against an original the same user owns.
        if original is not None and str(original.user_id) == current_user.user_id:
            original_text = original.extracted_text

    return validate_resume(resume.extracted_text, original_text)


@router.get("/{resume_id}/export")
def export_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    format: Annotated[str, Query(pattern="^(txt|docx)$")] = "txt",
) -> Response:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)

    name = resume.version_label or resume.original_filename or "resume"

    if format == "docx":
        content = to_docx_bytes(resume.extracted_text)
        media_type = DOCX_MEDIA_TYPE
        filename = safe_filename(name, "docx")
    else:
        content = to_txt_bytes(resume.extracted_text)
        media_type = "text/plain; charset=utf-8"
        filename = safe_filename(name, "txt")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
