from enum import Enum

from pydantic import BaseModel


class CheckStatus(str, Enum):
    passed = "pass"
    warning = "warning"


class ValidationCheck(BaseModel):
    name: str
    status: CheckStatus
    detail: str
    items: list[str] = []


class ValidationReport(BaseModel):
    ok: bool
    checks: list[ValidationCheck]
