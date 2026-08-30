"""Deterministic Resume Quality scoring for general (no-job) analysis.

This module is the trust anchor of the product: it turns Gemini's *observations* into a numeric
score using fixed, explainable rules in application code. The LLM never produces the score. The
same `GeneralObservations` always yields the same result — there is no randomness, no time
dependence, no external state.

The job-specific ATS Alignment Score (Keyword Coverage / Requirement-Evidence / …) is a separate
rubric handled in a later phase; the categories here are the subset that can be assessed without a
job description, reweighted to total 100.
"""

from app.schemas.analysis import (
    AffectedArea,
    BulletIssue,
    CategoryScore,
    Finding,
    GeneralObservations,
    Severity,
)

# Category maximums (sum to 100).
MAX_ATS_SAFETY = 25
MAX_EXPERIENCE = 25
MAX_STRUCTURE = 20
MAX_CONSISTENCY = 15
MAX_LANGUAGE = 15

# ATS parsing-safety penalties per detected risk, by severity.
ATS_PENALTY = {Severity.high: 8, Severity.medium: 4, Severity.low: 1}

# Bullet issues that make a bullet "weak" for experience-strength purposes.
WEAKENING_ISSUES = {BulletIssue.weak_verb, BulletIssue.no_metric, BulletIssue.passive_voice}

_SEVERITY_ORDER = {Severity.high: 0, Severity.medium: 1, Severity.low: 2}


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _score_ats_safety(obs: GeneralObservations) -> CategoryScore:
    penalty = sum(ATS_PENALTY[risk.severity] for risk in obs.ats_risks)
    score = _clamp(MAX_ATS_SAFETY - penalty, 0, MAX_ATS_SAFETY)
    if not obs.ats_risks:
        reason = "No ATS parsing risks were detected."
    else:
        high = sum(1 for r in obs.ats_risks if r.severity == Severity.high)
        med = sum(1 for r in obs.ats_risks if r.severity == Severity.medium)
        low = sum(1 for r in obs.ats_risks if r.severity == Severity.low)
        reason = f"Detected {high} high, {med} medium, and {low} low-severity ATS parsing risk(s)."
    return CategoryScore(name="ATS Parsing Safety", score=score, max_score=MAX_ATS_SAFETY, reason=reason)


def _score_experience(obs: GeneralObservations) -> CategoryScore:
    total = len(obs.bullets)
    if total == 0:
        return CategoryScore(
            name="Experience & Achievement Strength",
            score=0,
            max_score=MAX_EXPERIENCE,
            reason="No experience bullet points were found to assess.",
        )
    strong = sum(1 for bullet in obs.bullets if not (set(bullet.issues) & WEAKENING_ISSUES))
    score = round(MAX_EXPERIENCE * strong / total)
    reason = f"{strong} of {total} bullet point(s) show strong, specific achievements."
    return CategoryScore(
        name="Experience & Achievement Strength", score=score, max_score=MAX_EXPERIENCE, reason=reason
    )


def _score_structure(obs: GeneralObservations) -> CategoryScore:
    sections = obs.sections
    score = 0
    missing: list[str] = []

    if sections.contact.has_email:
        score += 4
    else:
        missing.append("email address")
    if sections.contact.has_phone:
        score += 2
    else:
        missing.append("phone number")
    if sections.summary.present:
        score += 3
    else:
        missing.append("summary")
    if sections.experience.present:
        score += 5
    else:
        missing.append("experience section")
    if sections.education.present:
        score += 3
    else:
        missing.append("education section")
    if sections.skills.present:
        score += 3
    else:
        missing.append("skills section")

    score = _clamp(score, 0, MAX_STRUCTURE)
    reason = "All key sections and contact details are present." if not missing else f"Missing: {', '.join(missing)}."
    return CategoryScore(name="Structure & Completeness", score=score, max_score=MAX_STRUCTURE, reason=reason)


def _score_consistency(obs: GeneralObservations) -> CategoryScore:
    score = 0
    issues: list[str] = []
    if obs.date_consistency.consistent_format:
        score += 8
    else:
        issues.append("inconsistent date formats")
    if not obs.date_consistency.has_overlaps:
        score += 7
    else:
        issues.append("overlapping dates")
    reason = "Dates are consistent and non-overlapping." if not issues else f"Found: {', '.join(issues)}."
    return CategoryScore(name="Consistency", score=score, max_score=MAX_CONSISTENCY, reason=reason)


def _score_language(obs: GeneralObservations) -> CategoryScore:
    lang = obs.language
    spelling_penalty = min(lang.spelling_grammar_issue_count, 8)
    passive_penalty = min(lang.passive_voice_count // 2, 4)
    filler_penalty = min(lang.filler_word_count // 2, 3)
    score = _clamp(MAX_LANGUAGE - spelling_penalty - passive_penalty - filler_penalty, 0, MAX_LANGUAGE)
    reason = (
        f"{lang.spelling_grammar_issue_count} spelling/grammar issue(s), "
        f"{lang.passive_voice_count} passive-voice phrase(s), "
        f"{lang.filler_word_count} filler word(s)."
    )
    return CategoryScore(name="Language Quality", score=score, max_score=MAX_LANGUAGE, reason=reason)


def _sorted_findings(obs: GeneralObservations) -> list[Finding]:
    ordered = sorted(obs.findings, key=lambda f: _SEVERITY_ORDER[f.severity])
    return [
        Finding(
            severity=f.severity,
            location_text=f.location_text,
            problem=f.problem,
            why_it_matters=f.why_it_matters,
            suggestion=f.suggestion,
            affects=f.affects if isinstance(f.affects, AffectedArea) else AffectedArea(f.affects),
        )
        for f in ordered
    ]


def score_general_analysis(obs: GeneralObservations) -> tuple[int, list[CategoryScore], list[Finding]]:
    """Compute the deterministic Resume Quality Score and category breakdown from AI observations.

    Returns (overall_score, category_scores, findings). overall_score is the sum of category
    scores and is guaranteed to be in [0, 100].
    """
    categories = [
        _score_ats_safety(obs),
        _score_experience(obs),
        _score_structure(obs),
        _score_consistency(obs),
        _score_language(obs),
    ]
    overall = sum(category.score for category in categories)
    findings = _sorted_findings(obs)
    return overall, categories, findings
