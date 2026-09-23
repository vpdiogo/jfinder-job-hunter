from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CareerProfileRecord(Base):
    __tablename__ = "career_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON)
    target_titles: Mapped[list[str]] = mapped_column(JSON)
    desired_seniority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    work_modes: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    locations: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    timezones: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    languages: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    required_technologies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    desired_technologies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResumeExtractionRecord(Base):
    __tablename__ = "resume_extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_content: Mapped[str] = mapped_column(String)
    extracted_data: Mapped[dict[str, object]] = mapped_column(JSON)
    confirmed_data: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("career_profiles.id"), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    description: Mapped[str] = mapped_column(String, default="")
    required_skills: Mapped[list[str]] = mapped_column(JSON)
    responsibilities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    focus_profile_id: Mapped[int | None] = mapped_column(ForeignKey("career_profiles.id"), nullable=True)
    required_technologies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    desired_technologies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    work_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    languages: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class JobNoteRecord(Base):
    __tablename__ = "job_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class ApplicationRecord(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    profile_id: Mapped[int] = mapped_column(ForeignKey("career_profiles.id"))
    score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String(20))
    reasons: Mapped[list[str]] = mapped_column(JSON)
    missing_requirements: Mapped[list[str]] = mapped_column(JSON)
    matched_skills: Mapped[list[str]] = mapped_column(JSON)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
