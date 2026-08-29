import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.db.session import get_db
from app.models.resume import FileType, Resume, ResumeStatus
from app.schemas.resume import ConfirmResumeRequest, PasteTextRequest, ResumeDetail, ResumeSummary
from app.services.extraction import ExtractionError, extract_docx, extract_pdf, extract_txt

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

EXTRACTORS = {
    "pdf": (FileType.pdf, extract_pdf),
    "docx": (FileType.docx, extract_docx),
    "txt": (FileType.txt, extract_txt),
}


def _get_owned_resume(db: Session, resume_id: uuid.UUID, user_id: str) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or str(resume.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.post("/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def upload_resume(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile,
) -> Resume:
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in EXTRACTORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file.",
        )

    content = file.file.read()

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is too large. The maximum size is 5 MB.",
        )

    file_type, extractor = EXTRACTORS[extension]

    try:
        result = extractor(content)
    except ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    resume = Resume(
        user_id=uuid.UUID(current_user.user_id),
        original_filename=filename,
        file_type=file_type,
        extracted_text=result.text,
        char_count=len(result.text),
        warnings=result.warnings,
        status=ResumeStatus.pending_confirmation,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/paste", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def paste_resume_text(
    payload: PasteTextRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Resume:
    result = extract_txt(payload.text.encode("utf-8"))

    if not result.text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pasted text cannot be empty.")

    resume = Resume(
        user_id=uuid.UUID(current_user.user_id),
        original_filename=None,
        file_type=FileType.txt,
        extracted_text=result.text,
        char_count=len(result.text),
        warnings=result.warnings,
        status=ResumeStatus.pending_confirmation,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeSummary])
def list_resumes(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Resume]:
    stmt = (
        select(Resume)
        .where(Resume.user_id == uuid.UUID(current_user.user_id))
        .order_by(Resume.created_at.desc())
    )
    return list(db.scalars(stmt))


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Resume:
    return _get_owned_resume(db, resume_id, current_user.user_id)


@router.patch("/{resume_id}/confirm", response_model=ResumeDetail)
def confirm_resume(
    resume_id: uuid.UUID,
    payload: ConfirmResumeRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Resume:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)

    final_text = payload.edited_text.strip() if payload.edited_text is not None else resume.extracted_text

    if not final_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot confirm an empty resume.")

    resume.extracted_text = final_text
    resume.char_count = len(final_text)
    resume.status = ResumeStatus.confirmed
    resume.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)
    db.delete(resume)
    db.commit()
