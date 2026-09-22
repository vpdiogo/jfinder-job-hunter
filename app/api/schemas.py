from pydantic import BaseModel, Field

from app.domain.enums import Recommendation


class JobInput(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    url: str = Field(min_length=1)
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)


class CareerProfileInput(BaseModel):
    skills: list[str] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)


class EvaluationRequest(BaseModel):
    job: JobInput
    profile: CareerProfileInput


class EvaluationResponse(BaseModel):
    job_url: str
    score: float
    recommendation: Recommendation
    reasons: list[str]
    missing_requirements: list[str]
    matched_skills: list[str]
