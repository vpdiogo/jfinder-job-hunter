from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import JobStatus, Recommendation


@dataclass(slots=True)
class Job:
    title: str
    company: str
    url: str
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    discovered_at: datetime | None = None


@dataclass(slots=True)
class CareerProfile:
    """Structured information used to evaluate job opportunities."""

    skills: list[str] = field(default_factory=list)
    target_titles: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JobEvaluation:
    job_url: str
    score: float
    recommendation: Recommendation
    reasons: list[str]
    missing_requirements: list[str]
    matched_skills: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Application:
    job_url: str
    status: JobStatus
    applied_at: datetime | None = None
