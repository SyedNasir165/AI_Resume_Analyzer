from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str | None
    file_type: str
    status: str
    char_count: int
    warnings: list[str]
    created_at: datetime
    confirmed_at: datetime | None


class ResumeDetail(ResumeSummary):
    extracted_text: str


class PasteTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class ConfirmResumeRequest(BaseModel):
    edited_text: str | None = Field(default=None, max_length=200_000)
