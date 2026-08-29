import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ForgotPasswordPage() {
  const { requestPasswordReset } = useAuth()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)

    const { error: resetError } = await requestPasswordReset(email)

    setSubmitting(false)

    if (resetError) {
      setError(resetError)
      return
    }

    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="mx-auto flex max-w-sm flex-col items-center gap-4 px-4 py-24 text-center sm:px-6">
        <h1 className="text-2xl font-semibold text-slate-900">Check your email</h1>
        <p className="text-slate-600">
          If an account exists for <span className="font-medium">{email}</span>, we sent a link to
          reset your password.
        </p>
        <Link to="/login" className="text-sm font-medium text-slate-900 underline underline-offset-4">
          Back to log in
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-sm flex-col gap-6 px-4 py-24 sm:px-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Reset your password</h1>
        <p className="mt-1 text-sm text-slate-600">Enter your email and we&apos;ll send you a reset link.</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
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
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60"
        >
          {submitting ? 'Sending…' : 'Send reset link'}
        </button>
      </form>

      <p className="text-center text-sm text-slate-600">
        <Link to="/login" className="font-medium text-slate-900 underline underline-offset-4">
          Back to log in
        </Link>
      </p>
    </div>
  )
}
