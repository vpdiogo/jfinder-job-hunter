import type { Evaluation, JobQueueItem, JobStatus, Profile, ResumeExtraction } from './types'

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

type RequestOptions = RequestInit & { body?: string }

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail ?? 'Não foi possível concluir a ação.')
  }
  return response.json() as Promise<T>
}

export function getQueue(filters: {
  status?: JobStatus
  recommendation?: string
  minScore?: string
}): Promise<JobQueueItem[]> {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.recommendation) params.set('recommendation', filters.recommendation)
  if (filters.minScore) params.set('min_score', filters.minScore)
  const suffix = params.size ? `?${params}` : ''
  return request<JobQueueItem[]>(`/jobs/queue${suffix}`)
}

export function getProfiles(): Promise<Profile[]> {
  return request<Profile[]>('/profiles')
}

export function getJobEvaluations(jobId: number): Promise<Evaluation[]> {
  return request<Evaluation[]>(`/jobs/${jobId}/evaluations`)
}

export function updateProfile(
  profileId: number,
  data: Omit<Profile, 'id' | 'created_at'>,
): Promise<Profile> {
  return request<Profile>(`/profiles/${profileId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function createProfile(
  data: Omit<Profile, 'id' | 'created_at'>,
): Promise<Profile> {
  return request<Profile>('/profiles', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function evaluateSavedJob(jobId: number, profileId: number): Promise<Evaluation> {
  return request<Evaluation>(`/jobs/${jobId}/evaluate`, {
    method: 'POST',
    body: JSON.stringify({ profile_id: profileId }),
  })
}

export function moveJob(jobId: number, action: 'interest' | 'apply'): Promise<void> {
  return request<void>(`/jobs/${jobId}/${action}`, { method: 'POST' })
}

export function updateJobStatus(jobId: number, status: JobStatus): Promise<void> {
  return request<void>(`/jobs/${jobId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export function extractResume(content: string): Promise<ResumeExtraction> {
  return request<ResumeExtraction>('/profiles/resume-extractions', {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}

export function confirmResumeExtraction(
  extractionId: number,
  data: { profile: Omit<Profile, 'id' | 'created_at'>; experiences: string[]; education: string[] },
): Promise<Profile> {
  return request<Profile>(`/profiles/resume-extractions/${extractionId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
