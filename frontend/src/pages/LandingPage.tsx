import { Link } from 'react-router-dom'
import ApiStatusBadge from '../components/ApiStatusBadge'

const FEATURES = [
  {
    title: 'Evidence-based scoring',
    body: 'Every score category is explainable, reproducible, and backed by what is actually in your resume — the AI never sets the number.',
    icon: (
      <path d="M4 13a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v6H4v-6ZM10 8a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v11h-4V8ZM16 4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v15h-4V4Z" />
    ),
  },
  {
    title: 'Job-specific analysis',
    body: 'Match your resume against the real job description — required vs. preferred, matched, partial, and missing — with an ATS Alignment Score.',
    icon: (
      <path d="M9.5 3a6.5 6.5 0 1 0 4.02 11.6l4.44 4.43 1.42-1.42-4.43-4.44A6.5 6.5 0 0 0 9.5 3Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" />
    ),
  },
  {
    title: 'You approve every change',
    body: 'The coach rewrites weak bullets using only your real facts, never inventing metrics. You accept, edit, or reject — the original is never touched.',
    icon: (
      <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17Z" />
    ),
  },
]

export default function LandingPage() {
  return (
    <div>
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-brand-50 via-white to-slate-50" />
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="flex flex-col items-start gap-6">
            <ApiStatusBadge />
            <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.1] tracking-tight text-slate-900 sm:text-6xl">
              Understand exactly how strong your resume is.
            </h1>
            <p className="max-w-2xl text-lg leading-relaxed text-slate-600">
              Upload your resume, optionally add a target role and job description, and get a
              transparent, evidence-based analysis: your strengths, your gaps, your ATS alignment,
              and the exact lines that need work — with every suggestion you control.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                to="/register"
                className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
              >
                Get started — it&apos;s free
              </Link>
              <Link
                to="/login"
                className="rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Log in
              </Link>
            </div>
            <p className="text-xs text-slate-400">
              Scores are a heuristic estimate — not a guarantee of ATS acceptance, interviews, or employment.
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
        <div className="grid gap-5 sm:grid-cols-3">
          {FEATURES.map((item) => (
            <div
              key={item.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  {item.icon}
                </svg>
              </span>
              <h3 className="mt-4 font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
