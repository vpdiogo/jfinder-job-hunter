export type JobStatus =
  | 'discovered'
  | 'evaluated'
  | 'interested'
  | 'applied'
  | 'recruiter'
  | 'technical'
  | 'final'
  | 'offer'
  | 'rejected'

export type Recommendation = 'apply' | 'review' | 'skip'

export interface JobQueueItem {
  id: number
  title: string
  company: string
  url: string
  description: string
  required_skills: string[]
  created_at: string
  status: JobStatus
  score: number | null
  recommendation: Recommendation | null
  applied_at: string | null
}

export interface Profile {
  id: number
  skills: string[]
  target_titles: string[]
  created_at: string
}

export interface Evaluation {
  id: number
  profile_id: number
  job_url: string
  score: number
  recommendation: Recommendation
  reasons: string[]
  missing_requirements: string[]
  matched_skills: string[]
  evaluated_at: string
}
