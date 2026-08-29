export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-slate-500 sm:px-6">
        <p>
          AI Resume Analyzer scores are a heuristic estimate based on the resume and job
          description you provide. They do not guarantee ATS acceptance, interviews, or
          employment.
        </p>
        <p className="mt-2">&copy; {new Date().getFullYear()} AI Resume Analyzer.</p>
      </div>
    </footer>
  )
}
