"""Schemas for resume analysis.

Two distinct layers live here:

1. The **AI observation schema** (`GeneralObservations` and its parts) — the strict, validated
   shape Gemini must return. Gemini reports *objective observations only* (booleans, counts,
   classifications, extracted text). It never returns a score. Malformed AI output is rejected
   against this schema, never silently accepted.

2. The **API response schema** (`AnalysisResult`, `CategoryScore`, `Finding`) — what the backend
   returns to the frontend after application code has computed the deterministic score from the
   validated observations.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. AI observation schema — the strict shape Gemini must return.
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AffectedArea(str, Enum):
    ats = "ats"
    recruiter = "recruiter"
    both = "both"


class BulletIssue(str, Enum):
    weak_verb = "weak_verb"
    no_metric = "no_metric"
    too_long = "too_long"
    too_short = "too_short"
    passive_voice = "passive_voice"
    filler_words = "filler_words"
    repetitive = "repetitive"


class SummaryQuality(str, Enum):
    strong = "strong"
    weak = "weak"
    missing = "missing"


class ContactObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    present: bool
    has_email: bool
    has_phone: bool


class SummaryObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    present: bool
    quality: SummaryQuality


class SectionPresence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    present: bool


class SectionsObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contact: ContactObservation
    summary: SummaryObservation
    experience: SectionPresence
    education: SectionPresence
    skills: SectionPresence


class BulletObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    section: str
    issues: list[BulletIssue] = Field(default_factory=list)


class DateConsistencyObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consistent_format: bool
    has_overlaps: bool


class AtsRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    severity: Severity
    description: str


class LanguageObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spelling_grammar_issue_count: int = Field(ge=0)
    passive_voice_count: int = Field(ge=0)
    filler_word_count: int = Field(ge=0)


class AiFinding(BaseModel):
    """A specific, human-readable problem tied to a location in the resume.

    The suggestion must never invent facts (metrics, employers, dates); when a metric would
    strengthen a bullet but isn't present, the suggestion should tell the user to add their own
    real number, not fabricate one.
    """

    model_config = ConfigDict(extra="forbid")
    severity: Severity
    location_text: str = Field(description="The exact resume text this finding refers to.")
    problem: str
    why_it_matters: str
    suggestion: str
    affects: AffectedArea


class GeneralObservations(BaseModel):
    """Top-level validated shape of Gemini's response for a general (no-job) analysis."""

    model_config = ConfigDict(extra="forbid")
    sections: SectionsObservation
    bullets: list[BulletObservation] = Field(default_factory=list)
    date_consistency: DateConsistencyObservation
    ats_risks: list[AtsRisk] = Field(default_factory=list)
    language: LanguageObservation
    findings: list[AiFinding] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. API response schema — computed, deterministic result returned to the client.
# ---------------------------------------------------------------------------

class CategoryScore(BaseModel):
    name: str
    score: int
    max_score: int
    reason: str


class Finding(BaseModel):
    severity: Severity
    location_text: str
    problem: str
    why_it_matters: str
    suggestion: str
    affects: AffectedArea


class AnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    analysis_type: str
    overall_score: int
    categories: list[CategoryScore]
    findings: list[Finding]
    created_at: datetime
