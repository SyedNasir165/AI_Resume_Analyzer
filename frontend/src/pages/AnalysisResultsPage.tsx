import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import CoachPanel from '../components/CoachPanel'
import { ScoreRing } from '../components/ui/ScoreRing'
import { StatusBadge, type Tone } from '../components/ui/StatusBadge'
import {
  ApiError,
  createResumeVersion,
  deleteAnalysis,
  downloadAnalysisReport,
  getAnalysis,
  getResume,
  type AnalysisResult,
  type CategoryScore,
  type Finding,
  type RequirementResult,
  type Severity,
} from '../lib/api'

type LoadStatus = 'loading' | 'ok' | 'error'

const SEVERITY_STYLES: Record<Severity, { label: string; badge: string }> = {
  high: { label: 'High', badge: 'bg-red-100 text-red-800' },
  medium: { label: 'Medium', badge: 'bg-amber-100 text-amber-800' },
  low: { label: 'Low', badge: 'bg-slate-100 text-slate-700' },
}

const STATUS_STYLES: Record<string, { label: string; badge: string }> = {
  matched: { label: 'Matched', badge: 'bg-emerald-100 text-emerald-800' },
  partial: { label: 'Partial', badge: 'bg-amber-100 text-amber-800' },
  missing: { label: 'Missing', badge: 'bg-red-100 text-red-800' },
}

const AFFECTS_LABEL: Record<string, string> = {
  ats: 'Affects ATS parsing',
  recruiter: 'Affects recruiter readability',
  both: 'Affects ATS & recruiters',
}

function healthFor(category: CategoryScore): { tone: Tone; label: string; dot: string } {
  const pct = (category.score / category.max_score) * 100
  if (pct >= 80) return { tone: 'strong', label: 'Strong', dot: 'bg-emerald-500' }
  if (pct >= 50) return { tone: 'warning', label: 'Needs improvement', dot: 'bg-amber-500' }
  return { tone: 'weak', label: 'Weak', dot: 'bg-red-500' }
}

function HealthCheck({ categories }: { categories: CategoryScore[] }) {
  return (
    <>
      <h2 className="mt-8 text-lg font-semibold text-slate-900">Resume health check</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {categories.map((category) => {
          const health = healthFor(category)
          return (
            <div
              key={category.name}
              className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-center gap-2.5">
                <span className={`h-2.5 w-2.5 rounded-full ${health.dot}`} />
                <span className="text-sm font-medium text-slate-900">{category.name}</span>
              </div>
              <StatusBadge tone={health.tone}>{health.label}</StatusBadge>
            </div>
          )
        })}
      </div>
    </>
  )
}

function LockedFacts() {
  return (
    <div className="mt-6 flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-slate-500 shadow-sm">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      </span>
      <div>
        <p className="text-sm font-semibold text-slate-900">Your facts are locked</p>
        <p className="mt-0.5 text-xs leading-relaxed text-slate-600">
          Your employers, job titles, dates, and education are never changed. The coach only rewrites
          the wording of bullet points, using facts already in your resume plus answers you provide —
          it never invents metrics or achievements.
        </p>
      </div>
    </div>
  )
}

interface FindingCardProps {
  finding: Finding
  resumeText: string | null
  acceptedText: string | null
  onAccept: (originalText: string, improvedText: string) => void
  onUndo: (originalText: string) => void
}

function FindingCard({ finding, resumeText, acceptedText, onAccept, onUndo }: FindingCardProps) {
  const severity = SEVERITY_STYLES[finding.severity]
  // The coach can only apply an edit if the finding's exact text is present in the resume.
  const coachable = Boolean(finding.location_text && resumeText && resumeText.includes(finding.location_text))
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${severity.badge}`}>
          {severity.label}
        </span>
        <span className="text-xs text-slate-500">{AFFECTS_LABEL[finding.affects] ?? ''}</span>
      </div>
      {finding.location_text && (
        <blockquote className="mt-3 border-l-2 border-slate-300 pl-3 text-sm italic text-slate-600">
          “{finding.location_text}”
        </blockquote>
      )}
      <p className="mt-3 text-sm font-medium text-slate-900">{finding.problem}</p>
      <p className="mt-1 text-sm text-slate-600">{finding.why_it_matters}</p>
      <p className="mt-2 text-sm text-slate-800">
        <span className="font-medium">Suggestion: </span>
        {finding.suggestion}
      </p>
      {coachable && (
        <CoachPanel
          bulletText={finding.location_text}
          accepted={acceptedText !== null}
          acceptedText={acceptedText}
          onAccept={onAccept}
          onUndo={onUndo}
        />
      )}
    </div>
  )
}

function RequirementRow({ requirement }: { requirement: RequirementResult }) {
  const style = STATUS_STYLES[requirement.match_status] ?? STATUS_STYLES.missing
  return (
    <div className="border-b border-slate-100 px-4 py-3 last:border-b-0">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-900">{requirement.text}</p>
          <p className="text-xs text-slate-500">
            {requirement.kind === 'required' ? 'Required' : 'Preferred'} · {requirement.category.replace('_', ' ')}
          </p>
        </div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${style.badge}`}>
          {style.label}
        </span>
      </div>
      {requirement.evidence_text && (
        <p className="mt-2 text-xs text-slate-600">
          <span className="font-medium">Evidence: </span>“{requirement.evidence_text}”
        </p>
      )}
      {!requirement.evidence_text && requirement.match_status === 'missing' && (
        <p className="mt-2 text-xs text-slate-500">
          No supporting evidence found. Only add this if you genuinely have the experience.
        </p>
      )}
    </div>
  )
}

function JobFitSection({ analysis }: { analysis: AnalysisResult }) {
  if (!analysis.job_fit) return null
  const fit = analysis.job_fit

  const groups: { label: string; items: string[]; dot: string }[] = [
    { label: 'Strong matches', items: fit.strong, dot: 'bg-emerald-500' },
    { label: 'Partial matches', items: fit.partial, dot: 'bg-amber-500' },
    { label: 'Missing', items: fit.missing, dot: 'bg-red-500' },
  ]

  return (
    <>
      <h2 className="mt-8 text-lg font-semibold text-slate-900">Job fit summary</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {groups.map((group) => (
          <div key={group.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${group.dot}`} />
              <span className="text-sm font-medium text-slate-900">{group.label}</span>
              <span className="text-xs text-slate-400">({group.items.length})</span>
            </div>
            <ul className="mt-2 space-y-1 text-xs text-slate-600">
              {group.items.length === 0 ? (
                <li className="text-slate-400">None</li>
              ) : (
                group.items.map((item) => <li key={item}>• {item}</li>)
              )}
            </ul>
          </div>
        ))}
      </div>

      {analysis.missing_keywords.length > 0 && (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-900">Important missing keywords</p>
          <p className="mt-1 text-xs text-slate-500">
            Present in the job description but not found in your resume. Only add a keyword if your
            experience genuinely supports it.
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {analysis.missing_keywords.map((kw) => (
              <span key={kw} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {analysis.requirements.length > 0 && (
        <>
          <h2 className="mt-8 text-lg font-semibold text-slate-900">Requirement-to-evidence match</h2>
          <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            {analysis.requirements.map((requirement, index) => (
              <RequirementRow key={index} requirement={requirement} />
            ))}
          </div>
        </>
      )}
    </>
  )
}

export default function AnalysisResultsPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const { session } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus] = useState<LoadStatus>('loading')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [resumeText, setResumeText] = useState<string | null>(null)
  const [acceptedEdits, setAcceptedEdits] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    if (!session || !analysisId) return
    let cancelled = false
    setStatus('loading')
    // Reset per-analysis working state when navigating between analyses (the component stays
    // mounted across route param changes, so stale accepted edits / saving state must be cleared).
    setResumeText(null)
    setAcceptedEdits({})
    setSaving(false)
    setSaveError(null)

    getAnalysis(session.access_token, analysisId)
      .then((data) => {
        if (cancelled) return
        setAnalysis(data)
        setStatus('ok')
        // Load the resume text so accepted rewrites can be substituted into a new version.
        return getResume(session.access_token, data.resume_id).then((resume) => {
          if (!cancelled) setResumeText(resume.extracted_text)
        })
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Could not load this analysis.')
          setStatus('error')
        }
      })

    return () => {
      cancelled = true
    }
  }, [session, analysisId])

  function acceptEdit(originalText: string, improvedText: string) {
    setAcceptedEdits((prev) => ({ ...prev, [originalText]: improvedText }))
  }

  function undoEdit(originalText: string) {
    setAcceptedEdits((prev) => {
      const next = { ...prev }
      delete next[originalText]
      return next
    })
  }

  const [deletingAnalysis, setDeletingAnalysis] = useState(false)
  const [downloadingReport, setDownloadingReport] = useState<'txt' | 'pdf' | null>(null)

  async function handleDownloadReport(format: 'txt' | 'pdf') {
    if (!session || !analysis) return
    setDownloadingReport(format)
    try {
      await downloadAnalysisReport(session.access_token, analysis.id, format)
    } catch {
      // best-effort download; ignore
    } finally {
      setDownloadingReport(null)
    }
  }

  async function handleDeleteAnalysis() {
    if (!session || !analysis) return
    setDeletingAnalysis(true)
    try {
      await deleteAnalysis(session.access_token, analysis.id)
      navigate('/dashboard')
    } catch {
      setDeletingAnalysis(false)
    }
  }

  async function saveTailoredVersion() {
    if (!session || !analysis || !resumeText) return
    setSaveError(null)
    setSaving(true)
    try {
      let newText = resumeText
      for (const [original, improved] of Object.entries(acceptedEdits)) {
        newText = newText.replace(original, improved)
      }
      const label = analysis.analysis_type === 'job' && analysis.target_role ? `Tailored for ${analysis.target_role}` : undefined
      const version = await createResumeVersion(session.access_token, analysis.resume_id, newText, label)
      // Re-analyze the new version so the user immediately sees the before/after.
      const endpoint =
        analysis.analysis_type === 'job'
          ? null // job re-analysis needs the JD again; send them to run it, keep it simple
          : `/api/resumes/${version.id}/analyze`
      if (endpoint) {
        const resp = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}${endpoint}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${session.access_token}` },
        })
        if (resp.ok) {
          const newAnalysis = (await resp.json()) as AnalysisResult
          navigate(`/analyses/${newAnalysis.id}`)
          return
        }
      }
      navigate('/dashboard')
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : 'Could not save the tailored version.')
      setSaving(false)
    }
  }

  if (status === 'loading') {
    return <div className="mx-auto max-w-3xl px-4 py-24 text-center text-slate-500 sm:px-6">Loading analysis…</div>
  }

  if (status === 'error' || !analysis) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center sm:px-6">
        <p className="text-red-700">{error ?? 'Analysis not found.'}</p>
        <Link to="/dashboard" className="mt-4 inline-block text-sm font-medium text-slate-900 underline underline-offset-4">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const isJob = analysis.analysis_type === 'job'

  const delta = analysis.previous_score !== null ? analysis.overall_score - analysis.previous_score : null

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="flex items-center justify-between">
        <Link to="/dashboard" className="text-sm font-medium text-slate-500 hover:text-slate-900">
          ← Back to dashboard
        </Link>
        <button
          onClick={() => void handleDeleteAnalysis()}
          disabled={deletingAnalysis}
          className="text-xs font-medium text-slate-400 hover:text-red-600 disabled:opacity-60"
        >
          {deletingAnalysis ? 'Deleting…' : 'Delete this analysis'}
        </button>
      </div>

      <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={analysis.overall_score} />
          <div className="flex-1 text-center sm:text-left">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">
              {isJob ? 'ATS Alignment Score' : 'Resume Quality Score'}
            </p>
            {isJob && analysis.target_role && (
              <p className="mt-0.5 text-lg font-bold text-slate-900">{analysis.target_role}</p>
            )}
            {delta !== null && (
              <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-sm">
                <span className="text-slate-500">Before {analysis.previous_score}</span>
                <span className="text-slate-400">→</span>
                <span className="font-semibold text-slate-900">After {analysis.overall_score}</span>
                <span className={`font-bold ${delta >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {delta >= 0 ? '+' : ''}
                  {delta}
                </span>
              </div>
            )}
            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs sm:justify-start">
              <span className="text-slate-400">Download report:</span>
              <button
                onClick={() => void handleDownloadReport('pdf')}
                disabled={downloadingReport !== null}
                className="rounded-md border border-slate-300 px-2.5 py-1 font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-60"
              >
                {downloadingReport === 'pdf' ? 'Preparing…' : 'PDF'}
              </button>
              <button
                onClick={() => void handleDownloadReport('txt')}
                disabled={downloadingReport !== null}
                className="rounded-md border border-slate-300 px-2.5 py-1 font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-60"
              >
                {downloadingReport === 'txt' ? 'Preparing…' : 'Text'}
              </button>
            </div>
          </div>
        </div>
        <p className="mt-5 border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-500">
          {isJob
            ? 'This is a heuristic estimate of alignment with the provided job description per this analyzer’s model. A high score means strong alignment — not a guarantee of ATS acceptance, interviews, or employment. Always review AI-generated suggestions before using them.'
            : 'This is a heuristic estimate of resume quality based on this analyzer’s model. It is not a guarantee of ATS acceptance, interviews, or employment. Always review AI-generated suggestions before using them.'}
        </p>
      </div>

      {!isJob && <HealthCheck categories={analysis.categories} />}

      {isJob && <JobFitSection analysis={analysis} />}

      <h2 className="mt-8 text-lg font-semibold text-slate-900">Category breakdown</h2>
      <div className="mt-3 space-y-3">
        {analysis.categories.map((category) => {
          const pct = Math.round((category.score / category.max_score) * 100)
          const barColor = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'
          return (
            <div key={category.name} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-900">{category.name}</span>
                <span className="font-semibold text-slate-600">
                  {category.score} / {category.max_score}
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
              </div>
              <p className="mt-2 text-xs text-slate-500">{category.reason}</p>
            </div>
          )
        })}
      </div>

      <LockedFacts />

      <h2 className="mt-8 text-lg font-semibold text-slate-900">
        Findings {analysis.findings.length > 0 && `(${analysis.findings.length})`}
      </h2>
      <div className="mt-3 space-y-3">
        {analysis.findings.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
            No specific issues were flagged.
          </div>
        ) : (
          analysis.findings.map((finding, index) => (
            <FindingCard
              key={index}
              finding={finding}
              resumeText={resumeText}
              acceptedText={acceptedEdits[finding.location_text] ?? null}
              onAccept={acceptEdit}
              onUndo={undoEdit}
            />
          ))
        )}
      </div>

      {Object.keys(acceptedEdits).length > 0 && (
        <div className="sticky bottom-4 mt-6 flex flex-col gap-2 rounded-lg border border-slate-300 bg-white p-4 shadow-lg">
          <p className="text-sm font-medium text-slate-900">
            {Object.keys(acceptedEdits).length} improvement
            {Object.keys(acceptedEdits).length > 1 ? 's' : ''} ready to apply
          </p>
          <p className="text-xs text-slate-500">
            Saving creates a new tailored version — your original resume stays unchanged.
          </p>
          {saveError && <p className="text-xs text-red-700">{saveError}</p>}
          <button
            onClick={() => void saveTailoredVersion()}
            disabled={saving}
            className="self-start rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saving ? 'Saving…' : 'Save as new version'}
          </button>
        </div>
      )}
    </div>
  )
}
