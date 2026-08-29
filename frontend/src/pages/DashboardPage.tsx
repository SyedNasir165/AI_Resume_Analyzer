import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { fetchMe } from '../lib/api'

type BackendStatus = 'loading' | 'ok' | 'error'

export default function DashboardPage() {
  const { session, signOut } = useAuth()
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('loading')
  const [backendEmail, setBackendEmail] = useState<string | null>(null)

  useEffect(() => {
    if (!session) return

    let cancelled = false
    setBackendStatus('loading')

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

      <div className="mt-8 rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
        Resume upload and analysis aren&apos;t implemented yet — that&apos;s a later phase.
      </div>
    </div>
  )
}
