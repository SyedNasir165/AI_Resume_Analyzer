import { useEffect, useState } from 'react'
import { fetchHealth } from '../lib/api'

type Status = 'checking' | 'online' | 'offline'

const STATUS_CONFIG: Record<Status, { label: string; dot: string; text: string }> = {
  checking: { label: 'Connecting…', dot: 'bg-slate-400 animate-pulse', text: 'text-slate-500' },
  online: { label: 'Live analysis ready', dot: 'bg-emerald-500', text: 'text-emerald-700' },
  offline: { label: 'Service offline', dot: 'bg-red-500', text: 'text-red-700' },
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
    <div
      className={`inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1 text-xs font-medium shadow-sm backdrop-blur ${text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </div>
  )
}
