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
