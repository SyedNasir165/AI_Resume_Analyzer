export type Tone = 'strong' | 'warning' | 'weak' | 'neutral' | 'brand'

const TONES: Record<Tone, string> = {
  strong: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  weak: 'bg-red-100 text-red-800',
  neutral: 'bg-slate-100 text-slate-700',
  brand: 'bg-brand-100 text-brand-700',
}

export function StatusBadge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${TONES[tone]}`}>
      {children}
    </span>
  )
}
