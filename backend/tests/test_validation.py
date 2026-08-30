"""Deterministic pre-export validation tests."""

from app.schemas.validation import CheckStatus
from app.services.validation import validate_resume

ORIGINAL = """Jane Doe
jane.doe@email.com | (555) 123-4567

Experience
Acme Corp - Backend Engineer (2020-2023)
- Was responsible for the backend systems
- Built a REST API that reduced latency by 40%

Education
BS Computer Science (2016-2020)
"""


def _check(report, name):
    return next(c for c in report.checks if c.name == name)


def test_identical_text_passes():
    report = validate_resume(ORIGINAL, ORIGINAL)
    assert report.ok is True
    assert all(c.status == CheckStatus.passed for c in report.checks)


def test_dropped_contact_is_flagged():
    version = ORIGINAL.replace("jane.doe@email.com | (555) 123-4567", "")
    report = validate_resume(version, ORIGINAL)
    contact_check = _check(report, "Original contact details preserved")
    assert contact_check.status == CheckStatus.warning
    assert "jane.doe@email.com" in contact_check.items
    assert report.ok is False


def test_dropped_year_is_flagged():
    version = ORIGINAL.replace("(2016-2020)", "")
    report = validate_resume(version, ORIGINAL)
    dates_check = _check(report, "Dates preserved")
    assert dates_check.status == CheckStatus.warning
    assert "2016" in dates_check.items


def test_new_figure_is_flagged_for_confirmation():
    version = ORIGINAL.replace(
        "Built a REST API that reduced latency by 40%",
        "Built a REST API that reduced latency by 40% for 50000 users",
    )
    report = validate_resume(version, ORIGINAL)
    figures_check = _check(report, "New figures are accurate")
    assert figures_check.status == CheckStatus.warning
    assert "50000" in figures_check.items


def test_duplicate_bullets_flagged():
    text = "Experience\n- Did a thing\n- Did a thing\n"
    report = validate_resume(text, None)
    dup_check = _check(report, "No duplicate bullet points")
    assert dup_check.status == CheckStatus.warning
    assert "Did a thing" in dup_check.items


def test_missing_contact_flagged_without_original():
    report = validate_resume("Just some text with no contact.", None)
    contact_check = _check(report, "Contact information present")
    assert contact_check.status == CheckStatus.warning


def test_no_comparison_checks_without_original():
    report = validate_resume(ORIGINAL, None)
    names = {c.name for c in report.checks}
    assert "Original contact details preserved" not in names
    assert "Dates preserved" not in names


def test_phone_format_difference_is_not_flagged():
    # Same number, different formatting -> normalized, so not reported as missing.
    version = ORIGINAL.replace("(555) 123-4567", "555.123.4567")
    report = validate_resume(version, ORIGINAL)
    contact_check = _check(report, "Original contact details preserved")
    assert contact_check.status == CheckStatus.passed
