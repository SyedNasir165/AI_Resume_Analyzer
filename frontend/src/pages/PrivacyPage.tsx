import { Link } from 'react-router-dom'

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <Link to="/" className="text-sm font-medium text-slate-500 hover:text-slate-900">
        ← Back to home
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Privacy &amp; your data</h1>

      <div className="mt-6 space-y-5 text-sm text-slate-600">
        <section>
          <h2 className="font-semibold text-slate-900">What we store</h2>
          <p className="mt-1">
            When you upload or paste a resume, we store the <em>extracted text</em> so you can review,
            analyze, and improve it — we do not keep the original uploaded file. We also store the
            analyses you run and any tailored versions you save. Your data is private to your account;
            no one else can access it.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-slate-900">How your resume is analyzed</h2>
          <p className="mt-1">
            To analyze a resume, its text (and, for job-specific analysis, the job description you
            provide) is sent to Google&apos;s Gemini API. Scores are computed by our own code from the
            model&apos;s structured output — the AI never sets your score, and it is instructed never to
            invent facts. Treat all AI-generated suggestions as drafts to verify before you use them.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-slate-900">Your controls</h2>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            <li>Delete any resume, version, or analysis at any time.</li>
            <li>
              Delete your entire account from the dashboard — this permanently removes all of your
              data.
            </li>
            <li>Export your approved resume as plain text or DOCX whenever you like.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-slate-900">No guarantees</h2>
          <p className="mt-1">
            Scores are heuristic estimates based on the resume and job description you provide. They do
            not guarantee ATS acceptance, interviews, or employment.
          </p>
        </section>
      </div>
    </div>
  )
}
