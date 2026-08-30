import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FileType(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"


class ResumeStatus(str, enum.Enum):
    pending_confirmation = "pending_confirmation"
    confirmed = "confirmed"


class Resume(Base):
    """A single uploaded/pasted resume, holding only extracted text — never the raw
    uploaded file — per the project's "don't store more than needed" privacy rule.
    """

    __tablename__ = "resumes"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # A tailored version points back to the resume it was derived from. The original (parent) is
    # never modified when a version is created — the master resume stays intact.
    parent_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("public.resumes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    version_label: Mapped[str | None] = mapped_column(String, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, native_enum=False, length=16), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, native_enum=False, length=32), nullable=False, default=ResumeStatus.pending_confirmation
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
