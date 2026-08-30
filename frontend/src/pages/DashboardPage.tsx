import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  analyzeResume,
  ApiError,
  deleteAccount,
  deleteResume,
  fetchMe,
  listResumes,
  type ResumeSummary,
} from '../lib/api'

type BackendStatus = 'loading' | 'ok' | 'error'
type ResumesStatus = 'loading' | 'ok' | 'error'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

// Order so each original resume is immediately followed by its tailored versions.
function orderWithVersions(resumes: ResumeSummary[]): ResumeSummary[] {
  const originals = resumes.filter((r) => !r.parent_resume_id)
  const versionsByParent = new Map<string, ResumeSummary[]>()
  for (const r of resumes) {
    if (r.parent_resume_id) {
      const list = versionsByParent.get(r.parent_resume_id) ?? []
      list.push(r)
      versionsByParent.set(r.parent_resume_id, list)
    }
  }
  const ordered: ResumeSummary[] = []
  for (const original of originals) {
    ordered.push(original)
    ordered.push(...(versionsByParent.get(original.id) ?? []))
  }
  return ordered
}

export default function DashboardPage() {
  const { session, signOut } = useAuth()
  const navigate = useNavigate()
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('loading')
  const [backendEmail, setBackendEmail] = useState<string | null>(null)

  const [resumesStatus, setResumesStatus] = useState<ResumesStatus>('loading')
  const [resumes, setResumes] = useState<ResumeSummary[]>([])
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [analyzingId, setAnalyzingId] = useState<string | null>(null)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)
  const [confirmingAccountDelete, setConfirmingAccountDelete] = useState(false)
  const [deletingAccount, setDeletingAccount] = useState(false)
  const [accountError, setAccountError] = useState<string | null>(null)

  const loadResumes = useCallback(async () => {
    if (!session) return
    setResumesStatus('loading')
    try {
      const data = await listResumes(session.access_token)
      setResumes(data)
      setResumesStatus('ok')
    } catch {
      setResumesStatus('error')
    }
  }, [session])

  useEffect(() => {
    if (!session) return

    let cancelled = false

    fetchMe(session.access_token)
      .then((data) => {
        if (!cancelled) {
          setBackendEmail(data.email)
          setBackendStatus('ok')
        }
      })
      .catch(() => {
        if (!cancelled) setBackendStatus('error')
      })

    return () => {
      cancelled = true
    }
  }, [session])

  useEffect(() => {
    void loadResumes()
  }, [loadResumes])

  async function handleDelete(resumeId: string) {
    if (!session) return
    setDeletingId(resumeId)
    try {
      await deleteResume(session.access_token, resumeId)
      setResumes((current) => current.filter((resume) => resume.id !== resumeId))
    } finally {
      setDeletingId(null)
      setPendingDeleteId(null)
    }
  }

  async function handleDeleteAccount() {
    if (!session) return
    setAccountError(null)
    setDeletingAccount(true)
    try {
      await deleteAccount(session.access_token)
      await signOut()
      navigate('/')
    } catch (err) {
      setAccountError(
        err instanceof ApiError ? err.message : 'Could not delete your account. Please try again.',
      )
      setDeletingAccount(false)
    }
  }

  async function handleAnalyze(resumeId: string) {
    if (!session) return
    setAnalyzeError(null)
    setAnalyzingId(resumeId)
    try {
      const result = await analyzeResume(session.access_token, resumeId)
      navigate(`/analyses/${result.id}`)
    } catch (err) {
      setAnalyzeError(
        err instanceof ApiError ? err.message : 'Could not analyze this resume. Please try again.',
      )
      setAnalyzingId(null)
    }
  }

  const totalResumes = resumes.filter((r) => !r.parent_resume_id).length
  const totalVersions = resumes.filter((r) => r.parent_resume_id).length

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Your dashboard</h1>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                backendStatus === 'ok' ? 'bg-emerald-500' : backendStatus === 'error' ? 'bg-red-500' : 'bg-slate-300'
              }`}
            />
            {session?.user.email ?? backendEmail}
          </p>
        </div>
        <Link
          to="/resumes/new"
          className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
        >
          + Upload resume
        </Link>
      </div>

      {resumesStatus === 'ok' && resumes.length > 0 && (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:max-w-md">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-2xl font-bold text-slate-900">{totalResumes}</p>
            <p className="text-xs font-medium text-slate-500">Resume{totalResumes === 1 ? '' : 's'}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-2xl font-bold text-slate-900">{totalVersions}</p>
            <p className="text-xs font-medium text-slate-500">Tailored version{totalVersions === 1 ? '' : 's'}</p>
          </div>
        </div>
      )}

      <h2 className="mt-10 text-sm font-semibold uppercase tracking-wide text-slate-400">Your resumes</h2>

      <div className="mt-3">
        {resumesStatus === 'loading' && <p className="text-sm text-slate-500">Loading your resumes…</p>}
        {resumesStatus === 'error' && (
          <p className="text-sm text-red-700">Could not load your resumes. Try refreshing the page.</p>
        )}
        {resumesStatus === 'ok' && resumes.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <p className="mt-3 text-sm font-medium text-slate-900">No resumes yet</p>
            <p className="mt-1 text-sm text-slate-500">Upload a resume to run your first analysis.</p>
            <Link
              to="/resumes/new"
              className="mt-4 inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
            >
              Upload resume
            </Link>
          </div>
        )}
        {resumesStatus === 'ok' && resumes.length > 0 && (
          <ul className="space-y-2.5">
            {orderWithVersions(resumes).map((resume) => {
              const isVersion = Boolean(resume.parent_resume_id)
              return (
                <li
                  key={resume.id}
                  className={`rounded-2xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
                    isVersion ? 'ml-6 border-slate-200/80 border-l-2 border-l-brand-200' : 'border-slate-200'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="flex items-center gap-2 truncate text-sm font-semibold text-slate-900">
                        {resume.version_label ?? resume.original_filename ?? 'Pasted text'}
                        {isVersion && (
                          <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">
                            Tailored
                          </span>
                        )}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {formatDate(resume.created_at)} · {resume.file_type.toUpperCase()}
                        {!isVersion && resume.status !== 'confirmed' && ' · Pending confirmation'}
                        {resume.warnings.length > 0 && ' · has warnings'}
                      </p>
                    </div>

                    {pendingDeleteId === resume.id ? (
                      <div className="flex shrink-0 items-center gap-2">
                        <span className="text-xs text-slate-600">Delete this resume?</span>
                        <button
                          onClick={() => void handleDelete(resume.id)}
                          disabled={deletingId === resume.id}
                          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                        >
                          {deletingId === resume.id ? 'Deleting…' : 'Yes, delete'}
                        </button>
                        <button
                          onClick={() => setPendingDeleteId(null)}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="flex shrink-0 flex-wrap items-center gap-2">
                        <button
                          onClick={() => void handleAnalyze(resume.id)}
                          disabled={analyzingId === resume.id}
                          className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                        >
                          {analyzingId === resume.id ? 'Analyzing…' : 'Analyze'}
                        </button>
                        <Link
                          to={`/resumes/${resume.id}/analyze-job`}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Job match
                        </Link>
                        <Link
                          to={`/resumes/${resume.id}/export`}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Export
                        </Link>
                        <button
                          onClick={() => setPendingDeleteId(resume.id)}
                          disabled={analyzingId === resume.id}
                          className="rounded-lg px-2 py-1.5 text-xs font-medium text-slate-400 hover:bg-slate-100 hover:text-red-600 disabled:opacity-60"
                          aria-label="Delete resume"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        )}
        {analyzeError && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {analyzeError}
          </p>
        )}
      </div>

      <div className="mt-12 rounded-2xl border border-red-200 bg-red-50/40 p-6">
        <h2 className="text-sm font-semibold text-red-800">Danger zone</h2>
        <p className="mt-1 text-xs text-slate-600">
          Permanently deletes your account and all of your data — resumes, versions, and analyses.
          This cannot be undone.
        </p>
        {accountError && <p className="mt-2 text-xs text-red-700">{accountError}</p>}
        {confirmingAccountDelete ? (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-700">Are you sure? This is permanent.</span>
            <button
              onClick={() => void handleDeleteAccount()}
              disabled={deletingAccount}
              className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-60"
            >
              {deletingAccount ? 'Deleting…' : 'Yes, delete everything'}
            </button>
            <button
              onClick={() => setConfirmingAccountDelete(false)}
              disabled={deletingAccount}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmingAccountDelete(true)}
            className="mt-3 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
          >
            Delete my account
          </button>
        )}
      </div>

      <p className="mt-6 text-center text-xs text-slate-400">
        <Link to="/privacy" className="underline underline-offset-2 hover:text-slate-600">
          Privacy &amp; your data
        </Link>
      </p>
    </div>
  )
}
