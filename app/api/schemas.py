from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import Recommendation


class JobInput(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    url: str = Field(min_length=1)
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)


class JobResponse(JobInput):
    id: int
    created_at: datetime


class JobImportRequest(BaseModel):
    jobs: list[JobInput] = Field(min_length=1)


class JobImportResponse(BaseModel):
    imported: list[JobResponse]
    skipped_urls: list[str]


class JobEvaluationRequest(BaseModel):
    profile_id: int = Field(ge=1)


class CareerProfileInput(BaseModel):
    skills: list[str] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)


class CareerProfileUpdate(BaseModel):
    skills: list[str] | None = None
    target_titles: list[str] | None = None

    @model_validator(mode="after")
    def requires_a_change(self) -> "CareerProfileUpdate":
        if self.skills is None and self.target_titles is None:
            raise ValueError("Provide skills or target_titles to update the profile.")
        return self


class CareerProfileResponse(CareerProfileInput):
    id: int
    created_at: datetime


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
