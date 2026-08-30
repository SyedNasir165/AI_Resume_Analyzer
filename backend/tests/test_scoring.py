"""Deterministic scoring tests.

These are the most important tests in the project: they pin down that the Resume Quality Score is
a pure, reproducible function of the AI's observations, with no randomness.
"""

from app.schemas.analysis import (
    AtsRisk,
    BulletIssue,
    BulletObservation,
    ContactObservation,
    DateConsistencyObservation,
    GeneralObservations,
    LanguageObservation,
    SectionPresence,
    SectionsObservation,
    Severity,
    SummaryObservation,
    SummaryQuality,
)
from app.services.scoring import score_general_analysis


def _perfect_observations(**overrides) -> GeneralObservations:
    """A resume that should score a perfect 100, with hooks to degrade one dimension at a time."""
    data = dict(
        sections=SectionsObservation(
            contact=ContactObservation(present=True, has_email=True, has_phone=True),
            summary=SummaryObservation(present=True, quality=SummaryQuality.strong),
            experience=SectionPresence(present=True),
            education=SectionPresence(present=True),
            skills=SectionPresence(present=True),
        ),
        bullets=[
            BulletObservation(text="Led migration that cut costs 30%.", section="experience", issues=[]),
            BulletObservation(text="Shipped API used by 10k users.", section="experience", issues=[]),
        ],
        date_consistency=DateConsistencyObservation(consistent_format=True, has_overlaps=False),
        ats_risks=[],
        language=LanguageObservation(
            spelling_grammar_issue_count=0, passive_voice_count=0, filler_word_count=0
        ),
        findings=[],
    )
    data.update(overrides)
    return GeneralObservations(**data)


def _category(categories, name):
    return next(c for c in categories if c.name == name)


def test_perfect_resume_scores_100():
    overall, categories, _ = score_general_analysis(_perfect_observations())
    assert overall == 100
    assert all(c.score == c.max_score for c in categories)


def test_worst_resume_scores_0():
    obs = GeneralObservations(
        sections=SectionsObservation(
            contact=ContactObservation(present=False, has_email=False, has_phone=False),
            summary=SummaryObservation(present=False, quality=SummaryQuality.missing),
            experience=SectionPresence(present=False),
            education=SectionPresence(present=False),
            skills=SectionPresence(present=False),
        ),
        bullets=[],
        date_consistency=DateConsistencyObservation(consistent_format=False, has_overlaps=True),
        ats_risks=[AtsRisk(type="tables", severity=Severity.high, description="x") for _ in range(5)],
        language=LanguageObservation(
            spelling_grammar_issue_count=20, passive_voice_count=20, filler_word_count=20
        ),
        findings=[],
    )
    overall, categories, _ = score_general_analysis(obs)
    assert overall == 0
    assert all(c.score == 0 for c in categories)


def test_scoring_is_deterministic():
    obs = _perfect_observations(
        ats_risks=[AtsRisk(type="columns", severity=Severity.medium, description="x")]
    )
    first = score_general_analysis(obs)
    second = score_general_analysis(obs)
    assert first[0] == second[0]
    assert [c.model_dump() for c in first[1]] == [c.model_dump() for c in second[1]]


def test_overall_is_always_within_bounds():
    obs = _perfect_observations(
        ats_risks=[AtsRisk(type="x", severity=Severity.high, description="y") for _ in range(100)],
        language=LanguageObservation(
            spelling_grammar_issue_count=999, passive_voice_count=999, filler_word_count=999
        ),
    )
    overall, _, _ = score_general_analysis(obs)
    assert 0 <= overall <= 100


def test_ats_penalties_by_severity():
    obs = _perfect_observations(
        ats_risks=[
            AtsRisk(type="a", severity=Severity.high, description="x"),
            AtsRisk(type="b", severity=Severity.medium, description="x"),
            AtsRisk(type="c", severity=Severity.low, description="x"),
        ]
    )
    _, categories, _ = score_general_analysis(obs)
    # 25 - (8 + 4 + 1) = 12
    assert _category(categories, "ATS Parsing Safety").score == 12


def test_experience_strength_is_ratio_of_strong_bullets():
    obs = _perfect_observations(
        bullets=[
            BulletObservation(text="Strong one.", section="experience", issues=[]),
            BulletObservation(text="Weak one.", section="experience", issues=[BulletIssue.no_metric]),
            BulletObservation(text="Strong two.", section="experience", issues=[]),
            BulletObservation(text="Weak two.", section="experience", issues=[BulletIssue.weak_verb]),
        ]
    )
    _, categories, _ = score_general_analysis(obs)
    # 2 of 4 strong -> round(25 * 0.5) = 12 (banker's rounding: round(12.5) == 12)
    assert _category(categories, "Experience & Achievement Strength").score == 12


def test_experience_strength_zero_when_no_bullets():
    obs = _perfect_observations(bullets=[])
    _, categories, _ = score_general_analysis(obs)
    assert _category(categories, "Experience & Achievement Strength").score == 0


def test_non_weakening_issues_do_not_reduce_experience():
    obs = _perfect_observations(
        bullets=[
            BulletObservation(text="A.", section="experience", issues=[BulletIssue.too_long]),
            BulletObservation(text="B.", section="experience", issues=[BulletIssue.repetitive]),
        ]
    )
    _, categories, _ = score_general_analysis(obs)
    # too_long / repetitive aren't "weakening" for strength -> both count as strong -> full 25
    assert _category(categories, "Experience & Achievement Strength").score == 25


def test_structure_partial_credit():
    obs = _perfect_observations(
        sections=SectionsObservation(
            contact=ContactObservation(present=True, has_email=True, has_phone=False),
            summary=SummaryObservation(present=False, quality=SummaryQuality.missing),
            experience=SectionPresence(present=True),
            education=SectionPresence(present=True),
            skills=SectionPresence(present=True),
        )
    )
    _, categories, _ = score_general_analysis(obs)
    # email 4 + experience 5 + education 3 + skills 3 = 15 (no phone -2, no summary -3)
    assert _category(categories, "Structure & Completeness").score == 15


def test_language_penalties_are_capped():
    obs = _perfect_observations(
        language=LanguageObservation(
            spelling_grammar_issue_count=100, passive_voice_count=0, filler_word_count=0
        )
    )
    _, categories, _ = score_general_analysis(obs)
    # spelling penalty capped at 8 -> 15 - 8 = 7
    assert _category(categories, "Language Quality").score == 7


def test_findings_sorted_by_severity():
    from app.schemas.analysis import AffectedArea, AiFinding

    obs = _perfect_observations(
        findings=[
            AiFinding(
                severity=Severity.low,
                location_text="a",
                problem="p",
                why_it_matters="w",
                suggestion="s",
                affects=AffectedArea.recruiter,
            ),
            AiFinding(
                severity=Severity.high,
                location_text="b",
                problem="p",
                why_it_matters="w",
                suggestion="s",
                affects=AffectedArea.ats,
            ),
            AiFinding(
                severity=Severity.medium,
                location_text="c",
                problem="p",
                why_it_matters="w",
                suggestion="s",
                affects=AffectedArea.both,
            ),
        ]
    )
    _, _, findings = score_general_analysis(obs)
    assert [f.severity for f in findings] == [Severity.high, Severity.medium, Severity.low]
