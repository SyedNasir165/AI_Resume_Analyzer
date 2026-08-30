"""Schemas for the AI Improvement Coach.

The coach helps a user strengthen a weak resume bullet. Its hard rule: it may only use facts that
are already in the resume bullet or that the user explicitly provides as answers. It must never
invent a metric, employer, date, or achievement. Any claim it cannot ground is flagged
`unverified` so the UI can force the user to confirm or remove it before it is accepted.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# --- AI output schemas (strictly validated) ---

class CoachQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questions: list[str] = Field(default_factory=list)


class FactSource(str, Enum):
    resume = "resume"
    user_answer = "user_answer"
    unverified = "unverified"


class FactUsed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    source: FactSource


class BulletRewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    improved_bullet: str
    facts_used: list[FactUsed] = Field(default_factory=list)


# --- API request schemas ---

class QuestionsRequest(BaseModel):
    bullet_text: str = Field(min_length=1, max_length=2000)


class AnswerItem(BaseModel):
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=2000)


class RewriteRequest(BaseModel):
    bullet_text: str = Field(min_length=1, max_length=2000)
    answers: list[AnswerItem] = Field(default_factory=list)


class CreateVersionRequest(BaseModel):
    edited_text: str = Field(min_length=1, max_length=200_000)
    version_label: str | None = Field(default=None, max_length=120)
