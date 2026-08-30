import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, getCoachQuestions, rewriteBullet, type BulletRewrite, type FactSource } from '../lib/api'

type Stage = 'idle' | 'questions' | 'rewritten'

const SOURCE_STYLES: Record<FactSource, { label: string; badge: string }> = {
  resume: { label: 'From your resume', badge: 'bg-emerald-100 text-emerald-800' },
  user_answer: { label: 'From your answer', badge: 'bg-sky-100 text-sky-800' },
  unverified: { label: 'Needs confirmation', badge: 'bg-amber-100 text-amber-800' },
}

interface CoachPanelProps {
  bulletText: string
  accepted: boolean
  acceptedText: string | null
  onAccept: (originalText: string, improvedText: string) => void
  onUndo: (originalText: string) => void
}

export default function CoachPanel({ bulletText, accepted, acceptedText, onAccept, onUndo }: CoachPanelProps) {
  const { session } = useAuth()
  const [open, setOpen] = useState(false)
  const [stage, setStage] = useState<Stage>('idle')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [questions, setQuestions] = useState<string[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [rewrite, setRewrite] = useState<BulletRewrite | null>(null)
  const [editedBullet, setEditedBullet] = useState('')

  const token = session?.access_token

  async function loadQuestions() {
    if (!token) return
    setError(null)
    setLoading(true)
    try {
      const qs = await getCoachQuestions(token, bulletText)
      setQuestions(qs)
      setStage('questions')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not start the coach.')
    } finally {
      setLoading(false)
    }
  }

  async function generate() {
    if (!token) return
    setError(null)
    setLoading(true)
    try {
      const answerList = questions
        .map((q) => ({ question: q, answer: (answers[q] ?? '').trim() }))
        .filter((a) => a.answer.length > 0)
      const result = await rewriteBullet(token, bulletText, answerList)
      setRewrite(result)
      setEditedBullet(result.improved_bullet)
      setStage('rewritten')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not generate an improved bullet.')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setStage('idle')
    setQuestions([])
    setAnswers({})
    setRewrite(null)
    setEditedBullet('')
    setError(null)
  }

  if (accepted) {
    return (
      <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3">
        <p className="text-xs font-medium text-emerald-800">✓ Improved version will be applied when you save:</p>
        <p className="mt-1 text-sm text-slate-800">{acceptedText}</p>
        <button
          onClick={() => {
            onUndo(bulletText)
            reset()
          }}
          className="mt-2 text-xs font-medium text-slate-500 underline underline-offset-2 hover:text-slate-900"
        >
          Undo
        </button>
      </div>
    )
  }

  return (
    <div className="mt-3">
      {!open ? (
        <button
          onClick={() => {
            setOpen(true)
            void loadQuestions()
          }}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
        >
          Improve this with the coach
        </button>
      ) : (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
          {loading && stage === 'idle' && <p className="text-xs text-slate-500">Thinking of questions…</p>}

          {stage === 'questions' && (
            <>
              <p className="text-xs font-medium text-slate-700">
                Answer what you can — leave the rest blank. The coach only uses real facts you provide; it
                never invents numbers.
              </p>
              <div className="mt-2 space-y-2">
                {questions.map((q) => (
                  <div key={q}>
                    <label className="block text-xs text-slate-600">{q}</label>
                    <input
                      value={answers[q] ?? ''}
                      onChange={(event) => setAnswers((prev) => ({ ...prev, [q]: event.target.value }))}
                      className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => void generate()}
                  disabled={loading}
                  className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-60"
                >
                  {loading ? 'Generating…' : 'Generate improved bullet'}
                </button>
                <button
                  onClick={() => {
                    setOpen(false)
                    reset()
                  }}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                >
                  Cancel
                </button>
              </div>
            </>
          )}

          {stage === 'rewritten' && rewrite && (
            <>
              <p className="text-xs font-medium text-slate-700">Suggested rewrite (edit before accepting if you like):</p>
              <textarea
                value={editedBullet}
                onChange={(event) => setEditedBullet(event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
              />
              {rewrite.facts_used.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {rewrite.facts_used.map((fact, index) => {
                    const style = SOURCE_STYLES[fact.source]
                    return (
                      <span
                        key={index}
                        className={`rounded-full px-2 py-0.5 text-[11px] ${style.badge}`}
                        title={style.label}
                      >
                        {fact.text} · {style.label}
                      </span>
                    )
                  })}
                </div>
              )}
              {rewrite.facts_used.some((f) => f.source === 'unverified') && (
                <p className="mt-2 text-[11px] text-amber-700">
                  Some claims couldn&apos;t be verified from your resume or answers — confirm they&apos;re true
                  (or edit them out) before accepting.
                </p>
              )}
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => {
                    onAccept(bulletText, editedBullet.trim())
                    setOpen(false)
                  }}
                  disabled={editedBullet.trim().length === 0}
                  className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
                >
                  Accept
                </button>
                <button
                  onClick={() => void generate()}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                >
                  Regenerate
                </button>
                <button
                  onClick={() => {
                    setOpen(false)
                    reset()
                  }}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                >
                  Reject
                </button>
              </div>
            </>
          )}

          {error && <p className="mt-2 text-xs text-red-700">{error}</p>}
        </div>
      )}
    </div>
  )
}
