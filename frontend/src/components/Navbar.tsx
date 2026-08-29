import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="text-lg font-semibold tracking-tight text-slate-900">
          AI Resume Analyzer
        </Link>
        <nav className="flex items-center gap-3">
          <Link to="/login" className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900">
            Log in
          </Link>
          <Link
            to="/register"
            className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Sign up
          </Link>
        </nav>
      </div>
    </header>
  )
}
