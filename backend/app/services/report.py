"""Build a human-readable analysis report from a stored Analysis.

The report is generated purely from the deterministic, already-stored analysis data (score,
category breakdown, findings, and job-fit details) — no AI call — so it exactly reflects what the
user saw on screen.
"""

from app.models.analysis import Analysis, AnalysisType

HEURISTIC_NOTE = (
    "This score is a heuristic estimate based on the resume and job description provided. "
    "It does not guarantee ATS acceptance, interviews, or employment. Verify all AI-generated "
    "suggestions before using them."
)


def _is_job(analysis: Analysis) -> bool:
    value = analysis.analysis_type.value if isinstance(analysis.analysis_type, AnalysisType) else analysis.analysis_type
    return value == "job"


def build_report_text(analysis: Analysis) -> str:
    is_job = _is_job(analysis)
    lines: list[str] = []

    lines.append("ATS Alignment Report" if is_job else "Resume Quality Report")
    lines.append("=" * 40)
    if is_job and analysis.target_role:
        lines.append(f"Target role: {analysis.target_role}")
    lines.append(f"Overall score: {analysis.overall_score} / 100")
    lines.append("")

    lines.append("Category breakdown")
    lines.append("-" * 20)
    for category in analysis.categories:
        lines.append(f"- {category['name']}: {category['score']}/{category['max_score']}")
        lines.append(f"    {category['reason']}")
    lines.append("")

    details = analysis.job_details or {}
    if is_job and details.get("job_fit"):
        fit = details["job_fit"]
        lines.append("Job fit summary")
        lines.append("-" * 20)
        lines.append(f"Strong matches: {', '.join(fit.get('strong', [])) or 'none'}")
        lines.append(f"Partial matches: {', '.join(fit.get('partial', [])) or 'none'}")
        lines.append(f"Missing: {', '.join(fit.get('missing', [])) or 'none'}")
        missing_keywords = details.get("missing_keywords", [])
        if missing_keywords:
            lines.append(f"Important missing keywords: {', '.join(missing_keywords)}")
        lines.append("")

    lines.append(f"Findings ({len(analysis.findings)})")
    lines.append("-" * 20)
    if not analysis.findings:
        lines.append("No specific issues were flagged.")
    for finding in analysis.findings:
        lines.append(f"[{finding['severity'].upper()}] {finding['location_text']}")
        lines.append(f"    Problem: {finding['problem']}")
        lines.append(f"    Why it matters: {finding['why_it_matters']}")
        lines.append(f"    Suggestion: {finding['suggestion']}")
        lines.append("")

    lines.append(HEURISTIC_NOTE)
    return "\n".join(lines)
