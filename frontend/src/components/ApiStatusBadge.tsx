import { useEffect, useState } from 'react'
import { fetchHealth } from '../lib/api'

type Status = 'checking' | 'online' | 'offline'

const STATUS_CONFIG: Record<Status, { label: string; dot: string; text: string }> = {
  checking: { label: 'Checking backend…', dot: 'bg-slate-400 animate-pulse', text: 'text-slate-500' },
  online: { label: 'Backend connected', dot: 'bg-emerald-500', text: 'text-emerald-700' },
  offline: { label: 'Backend not reachable', dot: 'bg-red-500', text: 'text-red-700' },
}

export default function ApiStatusBadge() {
  const [status, setStatus] = useState<Status>('checking')

  useEffect(() => {
    let cancelled = false

    fetchHealth()
      .then(() => {
        if (!cancelled) setStatus('online')
      })
      .catch(() => {
        if (!cancelled) setStatus('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  const { label, dot, text } = STATUS_CONFIG[status]

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm ${text}`}>
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </div>
  )
}
