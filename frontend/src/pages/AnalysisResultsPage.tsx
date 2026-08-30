import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError, getAnalysis, type AnalysisResult, type Finding, type Severity } from '../lib/api'

type LoadStatus = 'loading' | 'ok' | 'error'

const SEVERITY_STYLES: Record<Severity, { label: string; badge: string }> = {
  high: { label: 'High', badge: 'bg-red-100 text-red-800' },
  medium: { label: 'Medium', badge: 'bg-amber-100 text-amber-800' },
  low: { label: 'Low', badge: 'bg-slate-100 text-slate-700' },
}

const AFFECTS_LABEL: Record<string, string> = {
  ats: 'Affects ATS parsing',
  recruiter: 'Affects recruiter readability',
  both: 'Affects ATS & recruiters',
}

function scoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-red-600'
}

function FindingCard({ finding }: { finding: Finding }) {
  const severity = SEVERITY_STYLES[finding.severity]
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
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
    </div>
  )
}

export default function AnalysisResultsPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const { session } = useAuth()
  const [status, setStatus] = useState<LoadStatus>('loading')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!session || !analysisId) return
    let cancelled = false
    setStatus('loading')

    getAnalysis(session.access_token, analysisId)
      .then((data) => {
        if (!cancelled) {
          setAnalysis(data)
          setStatus('ok')
        }
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

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <Link to="/dashboard" className="text-sm font-medium text-slate-500 hover:text-slate-900">
        ← Back to dashboard
      </Link>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-500">Resume Quality Score</p>
        <div className="mt-1 flex items-baseline gap-2">
          <span className={`text-5xl font-bold ${scoreColor(analysis.overall_score)}`}>
            {analysis.overall_score}
          </span>
          <span className="text-xl text-slate-400">/ 100</span>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          This is a heuristic estimate of resume quality based on this analyzer&apos;s model. It is
          not a guarantee of ATS acceptance, interviews, or employment. Always review AI-generated
          suggestions before using them.
        </p>
      </div>

      <h2 className="mt-8 text-lg font-semibold text-slate-900">Category breakdown</h2>
      <div className="mt-3 space-y-3">
        {analysis.categories.map((category) => {
          const pct = Math.round((category.score / category.max_score) * 100)
          return (
            <div key={category.name} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-900">{category.name}</span>
                <span className="text-slate-600">
                  {category.score} / {category.max_score}
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-slate-800" style={{ width: `${pct}%` }} />
              </div>
              <p className="mt-2 text-xs text-slate-500">{category.reason}</p>
            </div>
          )
        })}
      </div>

      <h2 className="mt-8 text-lg font-semibold text-slate-900">
        Findings {analysis.findings.length > 0 && `(${analysis.findings.length})`}
      </h2>
      <div className="mt-3 space-y-3">
        {analysis.findings.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
            No specific issues were flagged.
          </div>
        ) : (
          analysis.findings.map((finding, index) => <FindingCard key={index} finding={finding} />)
        )}
      </div>
    </div>
  )
}
