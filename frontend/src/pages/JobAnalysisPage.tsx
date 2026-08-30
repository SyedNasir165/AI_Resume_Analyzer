import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { analyzeResumeForJob, ApiError } from '../lib/api'

const COMMON_ROLES = [
  'Software Engineer',
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Developer',
  'Data Analyst',
  'Data Scientist',
  'Machine Learning Engineer',
  'AI Engineer',
  'DevOps Engineer',
  'Cloud Engineer',
  'Cybersecurity Analyst',
  'Product Manager',
  'UI/UX Designer',
]

export default function JobAnalysisPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const { session } = useAuth()
  const navigate = useNavigate()

  const [targetRole, setTargetRole] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!session || !resumeId) return
    setError(null)

    if (jobDescription.trim().length < 20) {
      setError('Please paste the full job description (at least a couple of sentences).')
      return
    }

    setSubmitting(true)
    try {
      const result = await analyzeResumeForJob(
        session.access_token,
        resumeId,
        jobDescription,
        targetRole.trim() || undefined,
      )
      navigate(`/analyses/${result.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not analyze against this job. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <Link to="/dashboard" className="text-sm font-medium text-slate-500 hover:text-slate-900">
        ← Back to dashboard
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Job-specific analysis</h1>
      <p className="mt-1 text-sm text-slate-600">
        Paste the actual job description you&apos;re targeting. The analysis matches your resume
        against these exact requirements — it never assumes requirements that aren&apos;t stated.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div>
          <label htmlFor="role" className="block text-sm font-medium text-slate-700">
            Target role <span className="font-normal text-slate-400">(optional context)</span>
          </label>
          <input
            id="role"
            list="common-roles"
            value={targetRole}
            onChange={(event) => setTargetRole(event.target.value)}
            placeholder="Search or type a role…"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
          <datalist id="common-roles">
            {COMMON_ROLES.map((role) => (
              <option key={role} value={role} />
            ))}
          </datalist>
        </div>

        <div>
          <label htmlFor="jd" className="block text-sm font-medium text-slate-700">
            Job description
          </label>
          <textarea
            id="jd"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            rows={14}
            placeholder="Paste the full job description here…"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="self-start rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {submitting ? 'Analyzing…' : 'Run job-specific analysis'}
        </button>
      </form>
    </div>
  )
}
