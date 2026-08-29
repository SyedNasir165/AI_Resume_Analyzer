import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { deleteResume, fetchMe, listResumes, type ResumeSummary } from '../lib/api'

type BackendStatus = 'loading' | 'ok' | 'error'
type ResumesStatus = 'loading' | 'ok' | 'error'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function DashboardPage() {
  const { session, signOut } = useAuth()
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('loading')
  const [backendEmail, setBackendEmail] = useState<string | null>(null)

  const [resumesStatus, setResumesStatus] = useState<ResumesStatus>('loading')
  const [resumes, setResumes] = useState<ResumeSummary[]>([])
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

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

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <button
          onClick={() => void signOut()}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Log out
        </button>
      </div>

      <div className="mt-8 rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-500">Signed in as</p>
        <p className="text-lg font-medium text-slate-900">{session?.user.email}</p>

        <div className="mt-4 border-t border-slate-100 pt-4">
          {backendStatus === 'loading' && <p className="text-sm text-slate-500">Checking backend session…</p>}
          {backendStatus === 'ok' && (
            <p className="text-sm text-emerald-700">
              Backend verified your session for <span className="font-medium">{backendEmail}</span>.
            </p>
          )}
          {backendStatus === 'error' && (
            <p className="text-sm text-red-700">Could not verify your session with the backend.</p>
          )}
        </div>
      </div>

      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Your resumes</h2>
          <Link
            to="/resumes/new"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
          >
            Upload resume
          </Link>
        </div>

        <div className="mt-4">
          {resumesStatus === 'loading' && <p className="text-sm text-slate-500">Loading your resumes…</p>}
          {resumesStatus === 'error' && (
            <p className="text-sm text-red-700">Could not load your resumes. Try refreshing the page.</p>
          )}
          {resumesStatus === 'ok' && resumes.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
              You haven&apos;t uploaded a resume yet.
            </div>
          )}
          {resumesStatus === 'ok' && resumes.length > 0 && (
            <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
              {resumes.map((resume) => (
                <li key={resume.id} className="flex items-center justify-between gap-4 px-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {resume.original_filename ?? 'Pasted text'}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatDate(resume.created_at)} · {resume.file_type.toUpperCase()} ·{' '}
                      {resume.status === 'confirmed' ? 'Confirmed' : 'Pending confirmation'}
                      {resume.warnings.length > 0 && ' · has warnings'}
                    </p>
                  </div>

                  {pendingDeleteId === resume.id ? (
                    <div className="flex shrink-0 items-center gap-2">
                      <span className="text-xs text-slate-600">Delete this resume?</span>
                      <button
                        onClick={() => void handleDelete(resume.id)}
                        disabled={deletingId === resume.id}
                        className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                      >
                        {deletingId === resume.id ? 'Deleting…' : 'Yes, delete'}
                      </button>
                      <button
                        onClick={() => setPendingDeleteId(null)}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setPendingDeleteId(resume.id)}
                      className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                    >
                      Delete
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="mt-8 rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
        Resume analysis isn&apos;t implemented yet — that&apos;s a later phase.
      </div>
    </div>
  )
}
