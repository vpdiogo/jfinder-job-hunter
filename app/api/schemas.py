from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import JobStatus, Recommendation


class JobInput(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    url: str = Field(min_length=1)
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    source: str = Field(default="manual", min_length=1, max_length=50)
    required_technologies: list[str] = Field(default_factory=list)
    desired_technologies: list[str] = Field(default_factory=list)
    seniority: str | None = None
    work_mode: str | None = None
    location: str | None = None
    timezone: str | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    languages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validates_salary_range(self) -> "JobInput":
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max.")
        return self


class JobResponse(JobInput):
    focus_profile_id: int | None = None
    id: int
    created_at: datetime


class JobDescriptionExtractionRequest(BaseModel):
    description: str = Field(min_length=20, max_length=100_000)


class JobDescriptionExtractionResponse(BaseModel):
    responsibilities: list[str] = Field(default_factory=list)
    required_technologies: list[str] = Field(default_factory=list)
    desired_technologies: list[str] = Field(default_factory=list)
    seniority: str | None = None
    work_mode: str | None = None
    languages: list[str] = Field(default_factory=list)


class ManualJobCreateRequest(BaseModel):
    job: JobInput
    profile_id: int = Field(ge=1)


class JobNoteInput(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class JobNoteResponse(JobNoteInput):
    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime


class JobImportRequest(BaseModel):
    jobs: list[JobInput] = Field(min_length=1)


class JobImportResponse(BaseModel):
    imported: list[JobResponse]
    skipped_urls: list[str]


class JobEvaluationRequest(BaseModel):
    profile_id: int = Field(ge=1)


class JobStatusUpdateRequest(BaseModel):
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: int
    status: JobStatus
    applied_at: datetime | None
    updated_at: datetime


class JobQueueResponse(JobResponse):
    status: JobStatus
    score: float | None
    recommendation: Recommendation | None
    applied_at: datetime | None


class CareerProfileInput(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    skills: list[str] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)
    desired_seniority: str | None = None
    work_modes: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    timezones: list[str] = Field(default_factory=list)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    languages: list[str] = Field(default_factory=list)
    required_technologies: list[str] = Field(default_factory=list)
    desired_technologies: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validates_salary_range(self) -> "CareerProfileInput":
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max.")
        return self


class CareerProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    skills: list[str] | None = None
    target_titles: list[str] | None = None
    desired_seniority: str | None = None
    work_modes: list[str] | None = None
    locations: list[str] | None = None
    timezones: list[str] | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    languages: list[str] | None = None
    required_technologies: list[str] | None = None
    desired_technologies: list[str] | None = None

    @model_validator(mode="after")
    def requires_a_change(self) -> "CareerProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update the profile.")
        return self


class CareerProfileResponse(CareerProfileInput):
    name: str
    id: int
    created_at: datetime


class ResumeExtractionRequest(BaseModel):
    content: str = Field(min_length=20, max_length=100_000)


class ResumeDraftResponse(BaseModel):
    skills: list[str] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    experiences: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)


class ResumeExtractionResponse(BaseModel):
    id: int
    source_content: str
    draft: ResumeDraftResponse
    confirmed_profile_id: int | None
    confirmed_at: datetime | None
    created_at: datetime


class ResumeExtractionConfirmationRequest(BaseModel):
    profile: CareerProfileInput
    profile_id: int | None = Field(default=None, ge=1)
    experiences: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)


class EvaluationRequest(BaseModel):
    job: JobInput
    profile_id: int | None = Field(default=None, ge=1)
    profile: CareerProfileInput | None = None

    @model_validator(mode="after")
    def requires_exactly_one_profile_source(self) -> "EvaluationRequest":
        if (self.profile_id is None) == (self.profile is None):
            raise ValueError("Provide exactly one of profile_id or profile.")
        return self


class EvaluationResponse(BaseModel):
    job_url: str
    score: float
    recommendation: Recommendation
    reasons: list[str]
    missing_requirements: list[str]
    matched_skills: list[str]


class StoredEvaluationResponse(EvaluationResponse):
    id: int
    profile_id: int
    evaluated_at: datetime

class ProfessionalBaseInput(BaseModel):
    resume_content: str = ""
    links: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experiences: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ProfessionalBaseResponse(ProfessionalBaseInput):
    id: int
    created_at: datetime
    updated_at: datetime


class ApplicationProfileFromBaseRequest(CareerProfileInput):
    pass
