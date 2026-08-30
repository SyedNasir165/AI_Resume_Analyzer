import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisType(str, enum.Enum):
    general = "general"
    job = "job"


class Analysis(Base):
    """A completed analysis of a resume.

    Stores the deterministic score and category breakdown, the human-readable findings, and the
    raw validated AI observations the score was computed from — the last of these makes every
    score reproducible and auditable after the fact.
    """

    __tablename__ = "analyses"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("public.resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_type: Mapped[AnalysisType] = mapped_column(
        Enum(AnalysisType, native_enum=False, length=32), nullable=False, default=AnalysisType.general
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    categories: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    findings: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    observations: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Job-specific analyses only: the target role and the computed requirement/keyword/job-fit
    # detail for display. Null / empty for general analyses.
    target_role: Mapped[str | None] = mapped_column(String, nullable=True)
    job_details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
