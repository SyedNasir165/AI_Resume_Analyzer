from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import TokenPayload
from app.schemas.coach import BulletRewrite, CoachQuestions, QuestionsRequest, RewriteRequest
from app.services.gemini import GeminiError, coach_questions, coach_rewrite

router = APIRouter(prefix="/api/coach", tags=["coach"])


@router.post("/questions", response_model=CoachQuestions)
def get_coach_questions(
    payload: QuestionsRequest,
    _current_user: Annotated[TokenPayload, Depends(get_current_user)],
) -> CoachQuestions:
    try:
        return coach_questions(payload.bullet_text)
    except GeminiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/rewrite", response_model=BulletRewrite)
def rewrite_bullet(
    payload: RewriteRequest,
    _current_user: Annotated[TokenPayload, Depends(get_current_user)],
) -> BulletRewrite:
    answers = [(item.question, item.answer) for item in payload.answers]
    try:
        return coach_rewrite(payload.bullet_text, answers)
    except GeminiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
