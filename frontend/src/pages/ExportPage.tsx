import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  ApiError,
  exportResume,
  validateResume,
  type ValidationCheck,
  type ValidationReport,
} from '../lib/api'

type LoadStatus = 'loading' | 'ok' | 'error'

function CheckRow({ check }: { check: ValidationCheck }) {
  const isWarning = check.status === 'warning'
  return (
    <div className="border-b border-slate-100 px-4 py-3 last:border-b-0">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${isWarning ? 'bg-amber-500' : 'bg-emerald-500'}`} />
        <span className="text-sm font-medium text-slate-900">{check.name}</span>
      </div>
      <p className="mt-1 pl-4 text-xs text-slate-600">{check.detail}</p>
      {check.items.length > 0 && (
        <ul className="mt-1 flex flex-wrap gap-1.5 pl-4">
          {check.items.map((item) => (
            <li key={item} className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] text-amber-800">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function ExportPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const { session } = useAuth()

  const [status, setStatus] = useState<LoadStatus>('loading')
  const [report, setReport] = useState<ValidationReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<'txt' | 'docx' | 'pdf' | null>(null)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  useEffect(() => {
    if (!session || !resumeId) return
    let cancelled = false
    setStatus('loading')

    validateResume(session.access_token, resumeId)
      .then((data) => {
        if (!cancelled) {
          setReport(data)
          setStatus('ok')
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Could not run validation.')
          setStatus('error')
        }
      })

    return () => {
      cancelled = true
    }
  }, [session, resumeId])

  async function handleDownload(format: 'txt' | 'docx' | 'pdf') {
    if (!session || !resumeId) return
    setDownloadError(null)
    setDownloading(format)
    try {
      await exportResume(session.access_token, resumeId, format)
    } catch (err) {
      setDownloadError(err instanceof ApiError ? err.message : 'Could not export the resume.')
    } finally {
      setDownloading(null)
    }
  }

  const warnings = report?.checks.filter((c) => c.status === 'warning') ?? []

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <Link to="/dashboard" className="text-sm font-medium text-slate-500 hover:text-slate-900">
        ← Back to dashboard
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Validate &amp; export</h1>
      <p className="mt-1 text-sm text-slate-600">
        A quick check before you export — exports contain only your approved resume text, exactly as
        it is now.
      </p>

      {status === 'loading' && <p className="mt-6 text-sm text-slate-500">Running validation…</p>}
      {status === 'error' && <p className="mt-6 text-sm text-red-700">{error}</p>}

      {status === 'ok' && report && (
        <>
          <div className="mt-6 rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-4 py-3">
              <p className="text-sm font-medium text-slate-900">
                {report.ok ? 'All checks passed.' : `${warnings.length} thing${warnings.length > 1 ? 's' : ''} to review`}
              </p>
              {!report.ok && (
                <p className="mt-1 text-xs text-slate-500">
                  These aren&apos;t blockers — review each one and confirm it&apos;s correct before you
                  share the resume.
                </p>
              )}
            </div>
            {report.checks.map((check) => (
              <CheckRow key={check.name} check={check} />
            ))}
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => void handleDownload('txt')}
              disabled={downloading !== null}
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {downloading === 'txt' ? 'Preparing…' : 'Download .txt'}
            </button>
            <button
              onClick={() => void handleDownload('docx')}
              disabled={downloading !== null}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60"
            >
              {downloading === 'docx' ? 'Preparing…' : 'Download .docx'}
            </button>
            <button
              onClick={() => void handleDownload('pdf')}
              disabled={downloading !== null}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60"
            >
              {downloading === 'pdf' ? 'Preparing…' : 'Download .pdf'}
            </button>
          </div>
          {downloadError && <p className="mt-3 text-sm text-red-700">{downloadError}</p>}
          <p className="mt-4 text-xs text-slate-400">
            Both formats are plain, ATS-friendly, and keep the text fully selectable and extractable.
          </p>
        </>
      )}
    </div>
  )
}
