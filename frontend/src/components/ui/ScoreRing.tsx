interface ScoreRingProps {
  score: number
  max?: number
  size?: number
  label?: string
}

function toneFor(pct: number): string {
  if (pct >= 80) return '#059669' // emerald-600
  if (pct >= 60) return '#d97706' // amber-600
  return '#dc2626' // red-600
}

export function ScoreRing({ score, max = 100, size = 132, label }: ScoreRingProps) {
  const pct = Math.max(0, Math.min(100, (score / max) * 100))
  const stroke = 10
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const dash = (pct / 100) * circumference
  const color = toneFor(pct)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          style={{ transition: 'stroke-dasharray 700ms ease' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold text-slate-900">{score}</span>
        <span className="text-xs text-slate-400">/ {max}</span>
        {label && <span className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-400">{label}</span>}
      </div>
    </div>
  )
}
