import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.db.session import get_db
from app.models.analysis import Analysis, AnalysisType
from app.models.resume import Resume
from app.schemas.analysis import AnalysisResult, JobAnalysisRequest
from app.services.gemini import GeminiError, analyze_resume_general, analyze_resume_job
from app.services.scoring import score_general_analysis, score_job_analysis

router = APIRouter(prefix="/api", tags=["analyses"])


def _get_owned_resume(db: Session, resume_id: uuid.UUID, user_id: str) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or str(resume.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


def _to_result(analysis: Analysis) -> AnalysisResult:
    details = analysis.job_details or {}
    return AnalysisResult.model_validate(
        {
            "id": analysis.id,
            "resume_id": analysis.resume_id,
            "analysis_type": analysis.analysis_type.value
            if isinstance(analysis.analysis_type, AnalysisType)
            else analysis.analysis_type,
            "overall_score": analysis.overall_score,
            "categories": analysis.categories,
            "findings": analysis.findings,
            "created_at": analysis.created_at,
            "target_role": analysis.target_role,
            "requirements": details.get("requirements", []),
            "keywords": details.get("keywords", []),
            "job_fit": details.get("job_fit"),
            "missing_keywords": details.get("missing_keywords", []),
        }
    )


@router.post("/resumes/{resume_id}/analyze", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
def analyze_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisResult:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)

    try:
        observations = analyze_resume_general(resume.extracted_text)
    except GeminiError as exc:
        # Never fabricate an analysis on failure — surface a clean error instead.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    overall_score, categories, findings = score_general_analysis(observations)

    analysis = Analysis(
        id=uuid.uuid4(),
        resume_id=resume.id,
        user_id=uuid.UUID(current_user.user_id),
        analysis_type=AnalysisType.general,
        overall_score=overall_score,
        categories=[category.model_dump() for category in categories],
        findings=[finding.model_dump(mode="json") for finding in findings],
        observations=observations.model_dump(mode="json"),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return _to_result(analysis)


@router.post(
    "/resumes/{resume_id}/analyze-job", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED
)
def analyze_resume_for_job(
    resume_id: uuid.UUID,
    payload: JobAnalysisRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisResult:
    resume = _get_owned_resume(db, resume_id, current_user.user_id)

    try:
        observations = analyze_resume_job(resume.extracted_text, payload.job_description)
    except GeminiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    overall_score, categories, findings, requirements, keywords, job_fit, missing = score_job_analysis(observations)

    target_role = payload.target_role.strip() if payload.target_role else None

    analysis = Analysis(
        id=uuid.uuid4(),
        resume_id=resume.id,
        user_id=uuid.UUID(current_user.user_id),
        analysis_type=AnalysisType.job,
        overall_score=overall_score,
        categories=[category.model_dump() for category in categories],
        findings=[finding.model_dump(mode="json") for finding in findings],
        observations=observations.model_dump(mode="json"),
        target_role=target_role or None,
        job_details={
            "requirements": [r.model_dump(mode="json") for r in requirements],
            "keywords": [k.model_dump(mode="json") for k in keywords],
            "job_fit": job_fit.model_dump(mode="json"),
            "missing_keywords": missing,
        },
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return _to_result(analysis)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalysisResult:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None or str(analysis.user_id) != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _to_result(analysis)


@router.get("/resumes/{resume_id}/analyses", response_model=list[AnalysisResult])
def list_resume_analyses(
    resume_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AnalysisResult]:
    _get_owned_resume(db, resume_id, current_user.user_id)
    stmt = (
        select(Analysis)
        .where(Analysis.resume_id == resume_id, Analysis.user_id == uuid.UUID(current_user.user_id))
        .order_by(Analysis.created_at.desc())
    )
    return [_to_result(analysis) for analysis in db.scalars(stmt)]
