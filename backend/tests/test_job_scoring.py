"""Deterministic job-specific (ATS Alignment) scoring tests."""

from app.schemas.analysis import (
    AtsRisk,
    BulletObservation,
    ContactObservation,
    JobObservations,
    KeywordImportance,
    KeywordObservation,
    LanguageObservation,
    MatchStatus,
    MatchType,
    RequirementCategory,
    RequirementKind,
    RequirementObservation,
    SectionPresence,
    SectionsObservation,
    Severity,
    SummaryObservation,
    SummaryQuality,
)
from app.services.scoring import score_job_analysis


def _all_sections_present() -> SectionsObservation:
    return SectionsObservation(
        contact=ContactObservation(present=True, has_email=True, has_phone=True),
        summary=SummaryObservation(present=True, quality=SummaryQuality.strong),
        experience=SectionPresence(present=True),
        education=SectionPresence(present=True),
        skills=SectionPresence(present=True),
    )


def _perfect_job(**overrides) -> JobObservations:
    data = dict(
        requirements=[
            RequirementObservation(
                text="5 years Python", kind=RequirementKind.required,
                category=RequirementCategory.skill, evidence_text="6 years Python", evidence_strength=3,
            ),
            RequirementObservation(
                text="AWS", kind=RequirementKind.preferred,
                category=RequirementCategory.tool, evidence_text="Used AWS extensively", evidence_strength=3,
            ),
        ],
        keywords=[
            KeywordObservation(term="Python", importance=KeywordImportance.high, present_in_resume=True, match_type=MatchType.exact),
            KeywordObservation(term="AWS", importance=KeywordImportance.medium, present_in_resume=True, match_type=MatchType.exact),
        ],
        sections=_all_sections_present(),
        bullets=[BulletObservation(text="Cut costs 30%.", section="experience", issues=[])],
        ats_risks=[],
        language=LanguageObservation(spelling_grammar_issue_count=0, passive_voice_count=0, filler_word_count=0),
        findings=[],
    )
    data.update(overrides)
    return JobObservations(**data)


def _category(categories, name):
    return next(c for c in categories if c.name == name)


def test_perfect_job_scores_100():
    overall, categories, *_ = score_job_analysis(_perfect_job())
    assert overall == 100
    assert all(c.score == c.max_score for c in categories)


def test_worst_job_scores_0():
    obs = JobObservations(
        requirements=[
            RequirementObservation(
                text="Python", kind=RequirementKind.required,
                category=RequirementCategory.skill, evidence_text=None, evidence_strength=0,
            )
        ],
        keywords=[
            KeywordObservation(term="Python", importance=KeywordImportance.high, present_in_resume=False, match_type=MatchType.none)
        ],
        sections=SectionsObservation(
            contact=ContactObservation(present=False, has_email=False, has_phone=False),
            summary=SummaryObservation(present=False, quality=SummaryQuality.missing),
            experience=SectionPresence(present=False),
            education=SectionPresence(present=False),
            skills=SectionPresence(present=False),
        ),
        bullets=[],
        ats_risks=[AtsRisk(type="tables", severity=Severity.high, description="x") for _ in range(4)],
        language=LanguageObservation(spelling_grammar_issue_count=10, passive_voice_count=10, filler_word_count=10),
        findings=[],
    )
    overall, categories, *_ = score_job_analysis(obs)
    assert overall == 0
    assert all(c.score == 0 for c in categories)


def test_job_scoring_is_deterministic():
    obs = _perfect_job(
        requirements=[
            RequirementObservation(
                text="Kubernetes", kind=RequirementKind.required,
                category=RequirementCategory.tool, evidence_text=None, evidence_strength=1,
            )
        ]
    )
    first = score_job_analysis(obs)
    second = score_job_analysis(obs)
    assert first[0] == second[0]
    assert [c.model_dump() for c in first[1]] == [c.model_dump() for c in second[1]]


def test_job_overall_within_bounds():
    obs = _perfect_job(
        ats_risks=[AtsRisk(type="x", severity=Severity.high, description="y") for _ in range(50)],
        language=LanguageObservation(spelling_grammar_issue_count=999, passive_voice_count=999, filler_word_count=999),
    )
    overall, *_ = score_job_analysis(obs)
    assert 0 <= overall <= 100


def test_keyword_coverage_weights_by_importance():
    # high (weight 3) present, low (weight 1) absent -> 3/4 of 25 = 18.75 -> 19
    obs = _perfect_job(
        keywords=[
            KeywordObservation(term="Python", importance=KeywordImportance.high, present_in_resume=True, match_type=MatchType.exact),
            KeywordObservation(term="Perl", importance=KeywordImportance.low, present_in_resume=False, match_type=MatchType.none),
        ]
    )
    _, categories, *_ = score_job_analysis(obs)
    assert _category(categories, "Keyword Coverage").score == 19


def test_requirement_evidence_weights_required_higher():
    # required(w2) strength 0, preferred(w1) strength 3
    # numer = 2*0 + 1*1 = 1 ; denom = 3 ; 25 * 1/3 = 8.33 -> 8
    obs = _perfect_job(
        requirements=[
            RequirementObservation(text="A", kind=RequirementKind.required, category=RequirementCategory.skill, evidence_text=None, evidence_strength=0),
            RequirementObservation(text="B", kind=RequirementKind.preferred, category=RequirementCategory.skill, evidence_text="yes", evidence_strength=3),
        ]
    )
    _, categories, *_ = score_job_analysis(obs)
    assert _category(categories, "Requirement-Evidence Match").score == 8


def test_structure_scaled_to_10():
    _, categories, *_ = score_job_analysis(_perfect_job())
    structure = _category(categories, "Structure")
    assert structure.max_score == 10
    assert structure.score == 10


def test_empty_keywords_and_requirements_do_not_crash_and_score_full():
    obs = _perfect_job(keywords=[], requirements=[])
    _, categories, *_ = score_job_analysis(obs)
    assert _category(categories, "Keyword Coverage").score == 25
    assert _category(categories, "Requirement-Evidence Match").score == 25


def test_requirement_status_and_job_fit_grouping():
    obs = _perfect_job(
        requirements=[
            RequirementObservation(text="Strong req", kind=RequirementKind.required, category=RequirementCategory.skill, evidence_text="e", evidence_strength=3),
            RequirementObservation(text="Partial req", kind=RequirementKind.required, category=RequirementCategory.skill, evidence_text="e", evidence_strength=2),
            RequirementObservation(text="Missing req", kind=RequirementKind.required, category=RequirementCategory.skill, evidence_text=None, evidence_strength=0),
        ]
    )
    _, _, _, requirements, _, job_fit, _ = score_job_analysis(obs)
    statuses = {r.text: r.match_status for r in requirements}
    assert statuses["Strong req"] == MatchStatus.matched
    assert statuses["Partial req"] == MatchStatus.partial
    assert statuses["Missing req"] == MatchStatus.missing
    assert job_fit.strong == ["Strong req"]
    assert job_fit.partial == ["Partial req"]
    assert job_fit.missing == ["Missing req"]


def test_missing_keywords_lists_important_absent_terms_only():
    obs = _perfect_job(
        keywords=[
            KeywordObservation(term="HighAbsent", importance=KeywordImportance.high, present_in_resume=False, match_type=MatchType.none),
            KeywordObservation(term="MedAbsent", importance=KeywordImportance.medium, present_in_resume=False, match_type=MatchType.none),
            KeywordObservation(term="LowAbsent", importance=KeywordImportance.low, present_in_resume=False, match_type=MatchType.none),
            KeywordObservation(term="HighPresent", importance=KeywordImportance.high, present_in_resume=True, match_type=MatchType.exact),
        ]
    )
    *_, missing = score_job_analysis(obs)
    assert "HighAbsent" in missing
    assert "MedAbsent" in missing
    assert "LowAbsent" not in missing
    assert "HighPresent" not in missing
