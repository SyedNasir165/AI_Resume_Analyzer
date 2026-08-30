"""Deterministic pre-export validation.

This is a trust gate, not an AI step: it uses fixed rules to catch the failure modes the product
must never allow through — a tailored version silently losing a real fact (contact details,
employment dates) or introducing figures the user hasn't confirmed. Everything here is a pure
function of the two texts, so the same inputs always produce the same report.

When a resume has no original to compare against, the comparison checks are skipped and only the
self-consistency checks (duplicate bullets, contact present) run.
"""

import re

from app.schemas.validation import CheckStatus, ValidationCheck, ValidationReport

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
# A "figure": a percentage or a multi-digit number (skip lone small numbers to avoid noise).
_FIGURE_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%|\b\d{2,}(?:,\d{3})*(?:\.\d+)?\b")


def _emails(text: str) -> set[str]:
    return {m.group().lower() for m in _EMAIL_RE.finditer(text)}


def _phones(text: str) -> set[str]:
    # Normalize to digits only so formatting differences don't cause false positives, and require a
    # realistic phone length (>= 10 digits) so date ranges like "2020-2023" aren't mistaken for phones.
    numbers = {re.sub(r"\D", "", m.group()) for m in _PHONE_RE.finditer(text)}
    return {n for n in numbers if len(n) >= 10}


def _years(text: str) -> set[str]:
    return set(_YEAR_RE.findall(text))


def _figures(text: str) -> set[str]:
    return {m.group().replace(",", "") for m in _FIGURE_RE.finditer(text)}


def _bullet_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("-•*").strip()
        if line:
            lines.append(line)
    return lines


def _duplicate_bullets(text: str) -> list[str]:
    seen: dict[str, int] = {}
    for line in _bullet_lines(text):
        seen[line] = seen.get(line, 0) + 1
    return [line for line, count in seen.items() if count > 1]


def validate_resume(text: str, original_text: str | None) -> ValidationReport:
    checks: list[ValidationCheck] = []

    # --- self-consistency checks (always run) ---
    duplicates = _duplicate_bullets(text)
    checks.append(
        ValidationCheck(
            name="No duplicate bullet points",
            status=CheckStatus.warning if duplicates else CheckStatus.passed,
            detail="A line appears more than once." if duplicates else "No duplicated lines found.",
            items=duplicates,
        )
    )

    has_contact = bool(_emails(text) or _phones(text))
    checks.append(
        ValidationCheck(
            name="Contact information present",
            status=CheckStatus.passed if has_contact else CheckStatus.warning,
            detail="An email or phone number is present." if has_contact else "No email or phone number was found.",
        )
    )

    # --- comparison checks (only when there is an original to compare against) ---
    if original_text is not None:
        missing_contacts = sorted(
            (_emails(original_text) - _emails(text)) | (_phones(original_text) - _phones(text))
        )
        checks.append(
            ValidationCheck(
                name="Original contact details preserved",
                status=CheckStatus.warning if missing_contacts else CheckStatus.passed,
                detail="Contact details from your original are missing." if missing_contacts else "All original contact details are still present.",
                items=missing_contacts,
            )
        )

        missing_years = sorted(_years(original_text) - _years(text))
        checks.append(
            ValidationCheck(
                name="Dates preserved",
                status=CheckStatus.warning if missing_years else CheckStatus.passed,
                detail="Year(s) from your original are missing — check no employment/education dates were dropped." if missing_years else "All dates from your original are still present.",
                items=missing_years,
            )
        )

        new_figures = sorted(_figures(text) - _figures(original_text))
        checks.append(
            ValidationCheck(
                name="New figures are accurate",
                status=CheckStatus.warning if new_figures else CheckStatus.passed,
                detail="These figures are new since your original — confirm each is accurate before exporting." if new_figures else "No new figures were introduced.",
                items=new_figures,
            )
        )

    ok = all(check.status == CheckStatus.passed for check in checks)
    return ValidationReport(ok=ok, checks=checks)
