import { useRef, useState, type DragEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError, confirmResume, pasteResumeText, uploadResumeFile, type ResumeDetail } from '../lib/api'

type Mode = 'choose' | 'paste'
type Stage = 'idle' | 'processing' | 'review' | 'confirming'

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

export default function UploadResumePage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [mode, setMode] = useState<Mode>('choose')
  const [stage, setStage] = useState<Stage>('idle')
  const [isDragging, setIsDragging] = useState(false)
  const [pastedText, setPastedText] = useState('')
  const [resume, setResume] = useState<ResumeDetail | null>(null)
  const [editedText, setEditedText] = useState('')
  const [error, setError] = useState<string | null>(null)

  const accessToken = session?.access_token

  async function handleFile(file: File) {
    if (!accessToken) return
    setError(null)
    setStage('processing')

    try {
      const result = await uploadResumeFile(accessToken, file)
      setResume(result)
      setEditedText(result.extracted_text)
      setStage('review')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong while processing this file.')
      setStage('idle')
    }
  }

  async function handlePasteSubmit() {
    if (!accessToken) return
    setError(null)
    setStage('processing')

    try {
      const result = await pasteResumeText(accessToken, pastedText)
      setResume(result)
      setEditedText(result.extracted_text)
      setStage('review')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong while processing this text.')
      setStage('idle')
    }
  }

  async function handleConfirm() {
    if (!accessToken || !resume) return
    setError(null)
    setStage('confirming')

    try {
      await confirmResume(accessToken, resume.id, editedText)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not confirm this resume.')
      setStage('review')
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files[0]
    if (file) void handleFile(file)
  }

  function resetToStart() {
    setResume(null)
    setEditedText('')
    setError(null)
    setStage('idle')
    setPastedText('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const isConfirming: boolean = stage === 'confirming'

  if ((stage === 'review' || stage === 'confirming') && resume) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <h1 className="text-2xl font-semibold text-slate-900">Review extracted text</h1>
        <p className="mt-1 text-sm text-slate-600">
          Check that this looks right before confirming — you can fix any extraction issues below.
        </p>

        {resume.warnings.length > 0 && (
          <div className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">
            <ul className="list-disc space-y-1 pl-4">
              {resume.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        <textarea
          value={editedText}
          onChange={(event) => setEditedText(event.target.value)}
          rows={16}
          className="mt-4 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />

        {error && (
          <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="mt-4 flex gap-3">
          <button
            onClick={() => void handleConfirm()}
            disabled={isConfirming || editedText.trim().length === 0}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {isConfirming ? 'Confirming…' : 'Confirm and save'}
          </button>
          <button
            onClick={resetToStart}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Start over
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-semibold text-slate-900">Upload your resume</h1>
      <p className="mt-1 text-sm text-slate-600">PDF, DOCX, or TXT — up to 5 MB.</p>
      <p className="mt-2 text-xs text-slate-400">
        We store the extracted text (not the file) so you can analyze and improve it, and it stays
        private to your account. You can delete it any time. See{' '}
        <Link to="/privacy" className="underline underline-offset-2 hover:text-slate-600">
          Privacy &amp; your data
        </Link>
        .
      </p>

      <div className="mt-6 flex gap-2 text-sm">
        <button
          onClick={() => setMode('choose')}
          className={`rounded-md px-3 py-1.5 font-medium ${
            mode === 'choose' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Upload a file
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`rounded-md px-3 py-1.5 font-medium ${
            mode === 'paste' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Paste text
        </button>
      </div>

      {mode === 'choose' ? (
        <div
          onDragOver={(event) => {
            event.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`mt-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-16 text-center ${
            isDragging ? 'border-slate-500 bg-slate-100' : 'border-slate-300 bg-white'
          }`}
        >
          {stage === 'processing' ? (
            <p className="text-sm text-slate-600">Extracting text…</p>
          ) : (
            <>
              <p className="text-sm text-slate-600">Drag and drop your resume here, or</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="mt-3 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Choose a file
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS.join(',')}
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  if (file) void handleFile(file)
                }}
              />
            </>
          )}
        </div>
      ) : (
        <div className="mt-4">
          <textarea
            value={pastedText}
            onChange={(event) => setPastedText(event.target.value)}
            rows={12}
            placeholder="Paste your resume text here…"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
          <button
            onClick={() => void handlePasteSubmit()}
            disabled={stage === 'processing' || pastedText.trim().length === 0}
            className="mt-3 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {stage === 'processing' ? 'Processing…' : 'Continue'}
          </button>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  )
}
