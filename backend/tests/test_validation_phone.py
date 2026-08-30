"""Regression: a date range must not be mistaken for a phone number."""

from app.schemas.validation import CheckStatus
from app.services.validation import validate_resume

ORIGINAL = "Jane Doe\njane.doe@email.com | (555) 123-4567\nAcme Corp (2020-2023)\n- Built an API\n"


def test_dropped_date_range_is_not_reported_as_missing_phone():
    # Version drops the employment date range but keeps the real phone.
    version = "Jane Doe\njane.doe@email.com | (555) 123-4567\nAcme Corp\n- Built an API\n"
    report = validate_resume(version, ORIGINAL)

    contact = next(c for c in report.checks if c.name == "Original contact details preserved")
    # The real phone is preserved, so contact check passes (no "20202023" false positive).
    assert contact.status == CheckStatus.passed
    assert contact.items == []

    # The dropped years are still correctly flagged by the dates check.
    dates = next(c for c in report.checks if c.name == "Dates preserved")
    assert dates.status == CheckStatus.warning
    assert set(dates.items) == {"2020", "2023"}
