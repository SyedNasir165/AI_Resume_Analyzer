const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // response body wasn't JSON — fall through to the generic message
  }
  return `Request failed with status ${response.status}`
}

export interface HealthResponse {
  status: string
  service: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`)
  }

  return response.json() as Promise<HealthResponse>
}

export interface MeResponse {
  id: string
  email: string
}

export async function fetchMe(accessToken: string): Promise<MeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Fetching current user failed with status ${response.status}`)
  }

  return response.json() as Promise<MeResponse>
}

export interface ResumeSummary {
  id: string
  original_filename: string | null
  file_type: string
  status: 'pending_confirmation' | 'confirmed'
  char_count: number
  warnings: string[]
  created_at: string
  confirmed_at: string | null
  parent_resume_id: string | null
  version_label: string | null
}

export interface ResumeDetail extends ResumeSummary {
  extracted_text: string
}

function authHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` }
}

export async function uploadResumeFile(accessToken: string, file: File): Promise<ResumeDetail> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/resumes/upload`, {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: formData,
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeDetail>
}

export async function pasteResumeText(accessToken: string, text: string): Promise<ResumeDetail> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/paste`, {
    method: 'POST',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeDetail>
}

export async function listResumes(accessToken: string): Promise<ResumeSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/resumes`, {
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeSummary[]>
}

export async function confirmResume(
  accessToken: string,
  resumeId: string,
  editedText?: string,
): Promise<ResumeDetail> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}/confirm`, {
    method: 'PATCH',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ edited_text: editedText ?? null }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeDetail>
}

export async function deleteResume(accessToken: string, resumeId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}`, {
    method: 'DELETE',
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }
}

export async function getResume(accessToken: string, resumeId: string): Promise<ResumeDetail> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}`, {
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeDetail>
}

export async function createResumeVersion(
  accessToken: string,
  resumeId: string,
  editedText: string,
  versionLabel?: string,
): Promise<ResumeDetail> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}/versions`, {
    method: 'POST',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ edited_text: editedText, version_label: versionLabel || null }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ResumeDetail>
}

export type FactSource = 'resume' | 'user_answer' | 'unverified'

export interface FactUsed {
  text: string
  source: FactSource
}

export interface BulletRewrite {
  improved_bullet: string
  facts_used: FactUsed[]
}

export async function getCoachQuestions(accessToken: string, bulletText: string): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/coach/questions`, {
    method: 'POST',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ bullet_text: bulletText }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  const data = (await response.json()) as { questions: string[] }
  return data.questions
}

export async function rewriteBullet(
  accessToken: string,
  bulletText: string,
  answers: { question: string; answer: string }[],
): Promise<BulletRewrite> {
  const response = await fetch(`${API_BASE_URL}/api/coach/rewrite`, {
    method: 'POST',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ bullet_text: bulletText, answers }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<BulletRewrite>
}

export type ValidationStatus = 'pass' | 'warning'

export interface ValidationCheck {
  name: string
  status: ValidationStatus
  detail: string
  items: string[]
}

export interface ValidationReport {
  ok: boolean
  checks: ValidationCheck[]
}

export async function validateResume(accessToken: string, resumeId: string): Promise<ValidationReport> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}/validate`, {
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<ValidationReport>
}

function filenameFromDisposition(header: string | null, fallback: string): string {
  if (!header) return fallback
  const match = /filename="?([^"]+)"?/.exec(header)
  return match ? match[1] : fallback
}

// Downloads must go through fetch (not a plain link) because the endpoint needs the auth header.
async function downloadFromEndpoint(accessToken: string, path: string, fallbackName: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: authHeaders(accessToken) })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  const blob = await response.blob()
  const filename = filenameFromDisposition(response.headers.get('Content-Disposition'), fallbackName)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function exportResume(
  accessToken: string,
  resumeId: string,
  format: 'txt' | 'docx' | 'pdf',
): Promise<void> {
  await downloadFromEndpoint(accessToken, `/api/resumes/${resumeId}/export?format=${format}`, `resume.${format}`)
}

export async function downloadAnalysisReport(
  accessToken: string,
  analysisId: string,
  format: 'txt' | 'pdf',
): Promise<void> {
  await downloadFromEndpoint(
    accessToken,
    `/api/analyses/${analysisId}/report?format=${format}`,
    `analysis-report.${format}`,
  )
}

export type Severity = 'high' | 'medium' | 'low'
export type AffectedArea = 'ats' | 'recruiter' | 'both'

export interface CategoryScore {
  name: string
  score: number
  max_score: number
  reason: string
}

export interface Finding {
  severity: Severity
  location_text: string
  problem: string
  why_it_matters: string
  suggestion: string
  affects: AffectedArea
}

export type MatchStatus = 'matched' | 'partial' | 'missing'
export type MatchType = 'exact' | 'synonym' | 'none'
export type Importance = 'high' | 'medium' | 'low'

export interface RequirementResult {
  text: string
  kind: 'required' | 'preferred'
  category: string
  match_status: MatchStatus
  evidence_text: string | null
  evidence_strength: number
}

export interface KeywordResult {
  term: string
  importance: Importance
  present: boolean
  match_type: MatchType
}

export interface JobFitSummary {
  strong: string[]
  partial: string[]
  missing: string[]
}

export interface AnalysisResult {
  id: string
  resume_id: string
  analysis_type: string
  overall_score: number
  categories: CategoryScore[]
  findings: Finding[]
  created_at: string
  target_role: string | null
  requirements: RequirementResult[]
  keywords: KeywordResult[]
  job_fit: JobFitSummary | null
  missing_keywords: string[]
  previous_score: number | null
}

export async function analyzeResume(accessToken: string, resumeId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}/analyze`, {
    method: 'POST',
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<AnalysisResult>
}

export async function analyzeResumeForJob(
  accessToken: string,
  resumeId: string,
  jobDescription: string,
  targetRole?: string,
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}/analyze-job`, {
    method: 'POST',
    headers: { ...authHeaders(accessToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_description: jobDescription, target_role: targetRole || null }),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<AnalysisResult>
}

export async function getAnalysis(accessToken: string, analysisId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/analyses/${analysisId}`, {
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }

  return response.json() as Promise<AnalysisResult>
}

export async function deleteAnalysis(accessToken: string, analysisId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/analyses/${analysisId}`, {
    method: 'DELETE',
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }
}

export async function deleteAccount(accessToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/me`, {
    method: 'DELETE',
    headers: authHeaders(accessToken),
  })

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response))
  }
}
