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
# 1b. AI observation schema for JOB-SPECIFIC analysis.
# ---------------------------------------------------------------------------

class RequirementKind(str, Enum):
    required = "required"
    preferred = "preferred"


class RequirementCategory(str, Enum):
    skill = "skill"
    tool = "tool"
    experience = "experience"
    education = "education"
    certification = "certification"
    responsibility = "responsibility"
    soft_skill = "soft_skill"


class KeywordImportance(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class MatchType(str, Enum):
    exact = "exact"
    synonym = "synonym"
    none = "none"


class RequirementObservation(BaseModel):
    """One requirement extracted from the job description, matched against the resume.

    evidence_strength is the model's objective read of how well the resume supports this
    requirement (0 = none, 1 = weak/indirect, 2 = relevant but lacks detail/outcome, 3 = strong).
    The app derives the matched/partial/missing status from this number — the model never sets a
    status directly, so status and strength can't disagree.
    """

    model_config = ConfigDict(extra="forbid")
    text: str
    kind: RequirementKind
    category: RequirementCategory
    evidence_text: str | None = None
    evidence_strength: int = Field(ge=0, le=3)


class KeywordObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str
    importance: KeywordImportance
    present_in_resume: bool
    match_type: MatchType


class JobObservations(BaseModel):
    """Top-level validated shape of Gemini's response for a job-specific analysis."""

    model_config = ConfigDict(extra="forbid")
    requirements: list[RequirementObservation] = Field(default_factory=list)
    keywords: list[KeywordObservation] = Field(default_factory=list)
    sections: SectionsObservation
    bullets: list[BulletObservation] = Field(default_factory=list)
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


class MatchStatus(str, Enum):
    matched = "matched"
    partial = "partial"
    missing = "missing"


class RequirementResult(BaseModel):
    text: str
    kind: RequirementKind
    category: RequirementCategory
    match_status: MatchStatus
    evidence_text: str | None
    evidence_strength: int


class KeywordResult(BaseModel):
    term: str
    importance: KeywordImportance
    present: bool
    match_type: MatchType


class JobFitSummary(BaseModel):
    strong: list[str]
    partial: list[str]
    missing: list[str]


class JobAnalysisRequest(BaseModel):
    target_role: str | None = Field(default=None, max_length=200)
    job_description: str = Field(min_length=20, max_length=50_000)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    analysis_type: str
    overall_score: int
    categories: list[CategoryScore]
    findings: list[Finding]
    created_at: datetime

    # Present only for job-specific analyses; empty/None for general analyses.
    target_role: str | None = None
    requirements: list[RequirementResult] = Field(default_factory=list)
    keywords: list[KeywordResult] = Field(default_factory=list)
    job_fit: JobFitSummary | None = None
    missing_keywords: list[str] = Field(default_factory=list)

    # When the analyzed resume is a tailored version, the most recent score of the same type on
    # its original — for a before/after comparison. None when there is no prior analysis to compare.
    previous_score: int | None = None
