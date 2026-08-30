"""Deterministic scoring for resume analysis.

This module is the trust anchor of the product: it turns Gemini's *observations* into a numeric
score using fixed, explainable rules in application code. The LLM never produces the score. The
same observations always yield the same result — no randomness, no time dependence, no external
state.

Two rubrics live here, both totalling 100:

- **General Resume Quality Score** (`score_general_analysis`): the subset of quality dimensions
  assessable without a job description.
- **Job-specific ATS Alignment Score** (`score_job_analysis`): Keyword Coverage 25 /
  Requirement-Evidence Match 25 / ATS Parsing Safety 20 / Experience Strength 15 / Structure 10 /
  Language Quality 5, per the product spec.
"""

from app.schemas.analysis import (
    AffectedArea,
    AiFinding,
    AtsRisk,
    BulletIssue,
    BulletObservation,
    CategoryScore,
    Finding,
    GeneralObservations,
    JobFitSummary,
    JobObservations,
    KeywordImportance,
    KeywordResult,
    LanguageObservation,
    MatchStatus,
    MatchType,
    RequirementKind,
    RequirementResult,
    SectionsObservation,
    Severity,
)

# Bullet issues that make a bullet "weak" for experience-strength purposes.
WEAKENING_ISSUES = {BulletIssue.weak_verb, BulletIssue.no_metric, BulletIssue.passive_voice}

_SEVERITY_ORDER = {Severity.high: 0, Severity.medium: 1, Severity.low: 2}


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Shared observation helpers (both rubrics build on these).
# ---------------------------------------------------------------------------

def _severity_counts(ats_risks: list[AtsRisk]) -> tuple[int, int, int]:
    high = sum(1 for r in ats_risks if r.severity == Severity.high)
    med = sum(1 for r in ats_risks if r.severity == Severity.medium)
    low = sum(1 for r in ats_risks if r.severity == Severity.low)
    return high, med, low


def _ats_reason(ats_risks: list[AtsRisk]) -> str:
    if not ats_risks:
        return "No ATS parsing risks were detected."
    high, med, low = _severity_counts(ats_risks)
    return f"Detected {high} high, {med} medium, and {low} low-severity ATS parsing risk(s)."


def _strong_and_total(bullets: list[BulletObservation]) -> tuple[int, int]:
    total = len(bullets)
    strong = sum(1 for bullet in bullets if not (set(bullet.issues) & WEAKENING_ISSUES))
    return strong, total


def _structure_points(sections: SectionsObservation) -> tuple[int, list[str]]:
    """Return structure points on a fixed 0-20 scale plus the list of missing items.

    Job scoring scales this down to its 10-point category; general uses it as-is (20).
    """
    points = 0
    missing: list[str] = []
    checks = [
        (sections.contact.has_email, 4, "email address"),
        (sections.contact.has_phone, 2, "phone number"),
        (sections.summary.present, 3, "summary"),
        (sections.experience.present, 5, "experience section"),
        (sections.education.present, 3, "education section"),
        (sections.skills.present, 3, "skills section"),
    ]
    for present, weight, label in checks:
        if present:
            points += weight
        else:
            missing.append(label)
    return points, missing


def _structure_reason(missing: list[str]) -> str:
    return "All key sections and contact details are present." if not missing else f"Missing: {', '.join(missing)}."


def _language_reason(lang: LanguageObservation) -> str:
    return (
        f"{lang.spelling_grammar_issue_count} spelling/grammar issue(s), "
        f"{lang.passive_voice_count} passive-voice phrase(s), "
        f"{lang.filler_word_count} filler word(s)."
    )


def _sorted_findings(findings: list[AiFinding]) -> list[Finding]:
    ordered = sorted(findings, key=lambda f: _SEVERITY_ORDER[f.severity])
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


# ---------------------------------------------------------------------------
# General Resume Quality Score.
# ---------------------------------------------------------------------------

GEN_MAX_ATS = 25
GEN_MAX_EXPERIENCE = 25
GEN_MAX_STRUCTURE = 20
GEN_MAX_CONSISTENCY = 15
GEN_MAX_LANGUAGE = 15

GEN_ATS_PENALTY = {Severity.high: 8, Severity.medium: 4, Severity.low: 1}


def _gen_ats(obs: GeneralObservations) -> CategoryScore:
    penalty = sum(GEN_ATS_PENALTY[r.severity] for r in obs.ats_risks)
    score = _clamp(GEN_MAX_ATS - penalty, 0, GEN_MAX_ATS)
    return CategoryScore(name="ATS Parsing Safety", score=score, max_score=GEN_MAX_ATS, reason=_ats_reason(obs.ats_risks))


def _gen_experience(obs: GeneralObservations) -> CategoryScore:
    strong, total = _strong_and_total(obs.bullets)
    if total == 0:
        return CategoryScore(
            name="Experience & Achievement Strength",
            score=0,
            max_score=GEN_MAX_EXPERIENCE,
            reason="No experience bullet points were found to assess.",
        )
    score = round(GEN_MAX_EXPERIENCE * strong / total)
    return CategoryScore(
        name="Experience & Achievement Strength",
        score=score,
        max_score=GEN_MAX_EXPERIENCE,
        reason=f"{strong} of {total} bullet point(s) show strong, specific achievements.",
    )


def _gen_structure(obs: GeneralObservations) -> CategoryScore:
    points, missing = _structure_points(obs.sections)
    return CategoryScore(
        name="Structure & Completeness",
        score=_clamp(points, 0, GEN_MAX_STRUCTURE),
        max_score=GEN_MAX_STRUCTURE,
        reason=_structure_reason(missing),
    )


def _gen_consistency(obs: GeneralObservations) -> CategoryScore:
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
    return CategoryScore(name="Consistency", score=score, max_score=GEN_MAX_CONSISTENCY, reason=reason)


def _gen_language(obs: GeneralObservations) -> CategoryScore:
    lang = obs.language
    score = _clamp(
        GEN_MAX_LANGUAGE
        - min(lang.spelling_grammar_issue_count, 8)
        - min(lang.passive_voice_count // 2, 4)
        - min(lang.filler_word_count // 2, 3),
        0,
        GEN_MAX_LANGUAGE,
    )
    return CategoryScore(name="Language Quality", score=score, max_score=GEN_MAX_LANGUAGE, reason=_language_reason(lang))


def score_general_analysis(obs: GeneralObservations) -> tuple[int, list[CategoryScore], list[Finding]]:
    """Compute the deterministic Resume Quality Score and category breakdown from AI observations.

    Returns (overall_score, category_scores, findings). overall_score is the sum of category scores
    and is guaranteed to be in [0, 100].
    """
    categories = [_gen_ats(obs), _gen_experience(obs), _gen_structure(obs), _gen_consistency(obs), _gen_language(obs)]
    overall = sum(c.score for c in categories)
    return overall, categories, _sorted_findings(obs.findings)


# ---------------------------------------------------------------------------
# Job-specific ATS Alignment Score.
# ---------------------------------------------------------------------------

JOB_MAX_KEYWORD = 25
JOB_MAX_REQUIREMENT = 25
JOB_MAX_ATS = 20
JOB_MAX_EXPERIENCE = 15
JOB_MAX_STRUCTURE = 10
JOB_MAX_LANGUAGE = 5

JOB_ATS_PENALTY = {Severity.high: 7, Severity.medium: 4, Severity.low: 1}
KEYWORD_WEIGHT = {KeywordImportance.high: 3, KeywordImportance.medium: 2, KeywordImportance.low: 1}
REQUIREMENT_WEIGHT = {RequirementKind.required: 2, RequirementKind.preferred: 1}


def _status_from_strength(strength: int) -> MatchStatus:
    if strength <= 0:
        return MatchStatus.missing
    if strength >= 3:
        return MatchStatus.matched
    return MatchStatus.partial


def _job_keyword_coverage(obs: JobObservations) -> CategoryScore:
    total_weight = sum(KEYWORD_WEIGHT[k.importance] for k in obs.keywords)
    if total_weight == 0:
        return CategoryScore(
            name="Keyword Coverage",
            score=JOB_MAX_KEYWORD,
            max_score=JOB_MAX_KEYWORD,
            reason="No specific keywords were extracted from the job description.",
        )
    present_weight = sum(KEYWORD_WEIGHT[k.importance] for k in obs.keywords if k.present_in_resume)
    score = round(JOB_MAX_KEYWORD * present_weight / total_weight)
    present = sum(1 for k in obs.keywords if k.present_in_resume)
    return CategoryScore(
        name="Keyword Coverage",
        score=score,
        max_score=JOB_MAX_KEYWORD,
        reason=f"{present} of {len(obs.keywords)} job keyword(s) are present in the resume (weighted by importance).",
    )


def _job_requirement_evidence(obs: JobObservations) -> CategoryScore:
    denom = sum(REQUIREMENT_WEIGHT[r.kind] for r in obs.requirements)
    if denom == 0:
        return CategoryScore(
            name="Requirement-Evidence Match",
            score=JOB_MAX_REQUIREMENT,
            max_score=JOB_MAX_REQUIREMENT,
            reason="No specific requirements were extracted from the job description.",
        )
    numer = sum(REQUIREMENT_WEIGHT[r.kind] * (r.evidence_strength / 3) for r in obs.requirements)
    score = round(JOB_MAX_REQUIREMENT * numer / denom)
    matched = sum(1 for r in obs.requirements if r.evidence_strength >= 3)
    return CategoryScore(
        name="Requirement-Evidence Match",
        score=score,
        max_score=JOB_MAX_REQUIREMENT,
        reason=f"{matched} of {len(obs.requirements)} requirement(s) are strongly evidenced (weighted by required vs. preferred).",
    )


def _job_ats(obs: JobObservations) -> CategoryScore:
    penalty = sum(JOB_ATS_PENALTY[r.severity] for r in obs.ats_risks)
    score = _clamp(JOB_MAX_ATS - penalty, 0, JOB_MAX_ATS)
    return CategoryScore(name="ATS Parsing Safety", score=score, max_score=JOB_MAX_ATS, reason=_ats_reason(obs.ats_risks))


def _job_experience(obs: JobObservations) -> CategoryScore:
    strong, total = _strong_and_total(obs.bullets)
    if total == 0:
        return CategoryScore(
            name="Experience Strength",
            score=0,
            max_score=JOB_MAX_EXPERIENCE,
            reason="No experience bullet points were found to assess.",
        )
    score = round(JOB_MAX_EXPERIENCE * strong / total)
    return CategoryScore(
        name="Experience Strength",
        score=score,
        max_score=JOB_MAX_EXPERIENCE,
        reason=f"{strong} of {total} bullet point(s) show strong, specific achievements.",
    )


def _job_structure(obs: JobObservations) -> CategoryScore:
    points, missing = _structure_points(obs.sections)  # 0-20 scale
    score = round(points / 2)  # scale to 10
    return CategoryScore(
        name="Structure", score=_clamp(score, 0, JOB_MAX_STRUCTURE), max_score=JOB_MAX_STRUCTURE, reason=_structure_reason(missing)
    )


def _job_language(obs: JobObservations) -> CategoryScore:
    lang = obs.language
    score = _clamp(
        JOB_MAX_LANGUAGE
        - min(lang.spelling_grammar_issue_count, 3)
        - min(lang.passive_voice_count // 3, 1)
        - min(lang.filler_word_count // 3, 1),
        0,
        JOB_MAX_LANGUAGE,
    )
    return CategoryScore(name="Language Quality", score=score, max_score=JOB_MAX_LANGUAGE, reason=_language_reason(lang))


def _requirement_results(obs: JobObservations) -> list[RequirementResult]:
    # Required first, then by descending evidence strength, so the most important gaps surface.
    ordered = sorted(
        obs.requirements,
        key=lambda r: (0 if r.kind == RequirementKind.required else 1, r.evidence_strength),
    )
    return [
        RequirementResult(
            text=r.text,
            kind=r.kind,
            category=r.category,
            match_status=_status_from_strength(r.evidence_strength),
            evidence_text=r.evidence_text,
            evidence_strength=r.evidence_strength,
        )
        for r in ordered
    ]


def _keyword_results(obs: JobObservations) -> list[KeywordResult]:
    importance_order = {KeywordImportance.high: 0, KeywordImportance.medium: 1, KeywordImportance.low: 2}
    ordered = sorted(obs.keywords, key=lambda k: (importance_order[k.importance], not k.present_in_resume))
    return [
        KeywordResult(term=k.term, importance=k.importance, present=k.present_in_resume, match_type=k.match_type)
        for k in ordered
    ]


def _job_fit(requirements: list[RequirementResult]) -> JobFitSummary:
    strong = [r.text for r in requirements if r.match_status == MatchStatus.matched]
    partial = [r.text for r in requirements if r.match_status == MatchStatus.partial]
    missing = [r.text for r in requirements if r.match_status == MatchStatus.missing]
    return JobFitSummary(strong=strong, partial=partial, missing=missing)


def _missing_keywords(keywords: list[KeywordResult]) -> list[str]:
    # Important (high/medium) keywords the resume does not currently support.
    return [
        k.term
        for k in keywords
        if not k.present and k.importance in (KeywordImportance.high, KeywordImportance.medium)
    ]


def score_job_analysis(
    obs: JobObservations,
) -> tuple[int, list[CategoryScore], list[Finding], list[RequirementResult], list[KeywordResult], JobFitSummary, list[str]]:
    """Compute the deterministic ATS Alignment Score plus the job-fit detail from AI observations.

    Returns (overall, categories, findings, requirements, keywords, job_fit, missing_keywords).
    overall is the sum of category scores, guaranteed within [0, 100].
    """
    categories = [
        _job_keyword_coverage(obs),
        _job_requirement_evidence(obs),
        _job_ats(obs),
        _job_experience(obs),
        _job_structure(obs),
        _job_language(obs),
    ]
    overall = sum(c.score for c in categories)
    requirements = _requirement_results(obs)
    keywords = _keyword_results(obs)
    job_fit = _job_fit(requirements)
    missing = _missing_keywords(keywords)
    return overall, categories, _sorted_findings(obs.findings), requirements, keywords, job_fit, missing
