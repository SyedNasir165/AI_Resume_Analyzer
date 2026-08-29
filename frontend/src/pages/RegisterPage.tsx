import { Link } from 'react-router-dom'

export default function RegisterPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-4 py-24 text-center sm:px-6">
      <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
      <p className="text-slate-600">
        Registration is not implemented yet — it&apos;s planned for a later phase. This page is a
        placeholder confirming the routing works.
      </p>
      <Link to="/" className="text-sm font-medium text-slate-900 underline underline-offset-4">
        Back to home
      </Link>
    </div>
  )
}
