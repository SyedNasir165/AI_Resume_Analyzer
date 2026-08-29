import { Link } from 'react-router-dom'
import ApiStatusBadge from '../components/ApiStatusBadge'

const FEATURES = [
  {
    title: 'Evidence-based scoring',
    body: 'Every score category is explainable, reproducible, and backed by what is actually in your resume.',
  },
  {
    title: 'Job-specific analysis',
    body: 'Match your resume against the real job description — required, preferred, matched, and missing.',
  },
  {
    title: 'You approve every change',
    body: 'Suggestions never overwrite your resume. You review, edit, and approve before anything changes.',
  },
]

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="flex flex-col items-start gap-6">
        <ApiStatusBadge />
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Understand exactly how strong your resume is.
        </h1>
        <p className="max-w-2xl text-lg text-slate-600">
          Upload your resume, optionally add a target role and job description, and get a
          transparent, evidence-based analysis: your strengths, your gaps, your ATS alignment,
          and the exact lines that need work — with every suggestion you control.
        </p>
        <div className="flex gap-3">
          <Link
            to="/register"
            className="rounded-md bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700"
          >
            Get started
          </Link>
          <Link
            to="/login"
            className="rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Log in
          </Link>
        </div>
      </div>

      <div className="mt-20 grid gap-6 sm:grid-cols-3">
        {FEATURES.map((item) => (
          <div key={item.title} className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{item.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
