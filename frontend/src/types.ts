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
  required_technologies: string[]
  desired_technologies: string[]
  seniority: string | null
  work_mode: string | null
  location: string | null
  timezone: string | null
  salary_min: number | null
  salary_max: number | null
  languages: string[]
  created_at: string
  status: JobStatus
  score: number | null
  recommendation: Recommendation | null
  applied_at: string | null
}

export interface Profile {
  id: number
  name: string
  skills: string[]
  target_titles: string[]
  desired_seniority: string | null
  work_modes: string[]
  locations: string[]
  timezones: string[]
  salary_min: number | null
  salary_max: number | null
  languages: string[]
  required_technologies: string[]
  desired_technologies: string[]
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

export interface ResumeDraft {
  skills: string[]
  target_titles: string[]
  languages: string[]
  experiences: string[]
  education: string[]
}

export interface ResumeExtraction {
  id: number
  source_content: string
  draft: ResumeDraft
  confirmed_profile_id: number | null
  confirmed_at: string | null
  created_at: string
}
