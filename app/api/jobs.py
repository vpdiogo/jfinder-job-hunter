from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    JobEvaluationRequest,
    JobImportRequest,
    JobImportResponse,
    JobResponse,
    StoredEvaluationResponse,
)
from app.repositories.database import get_session
from app.repositories.tables import (
    CareerProfileRecord,
    JobRecord,
)
from app.services.evaluation_service import evaluate_and_store

router = APIRouter(prefix="/jobs", tags=["jobs"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post(
    "/import",
    response_model=JobImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_jobs(
    request: JobImportRequest,
    session: SessionDependency,
) -> JobImportResponse:
    urls = [job.url for job in request.jobs]
    existing_urls = set(
        session.scalars(select(JobRecord.url).where(JobRecord.url.in_(urls))).all()
    )
    seen_urls: set[str] = set()
    imported: list[JobRecord] = []
    skipped_urls: list[str] = []

    for job in request.jobs:
        if job.url in existing_urls or job.url in seen_urls:
            skipped_urls.append(job.url)
            continue

        record = JobRecord(
            title=job.title,
            company=job.company,
            url=job.url,
            description=job.description,
            required_skills=job.required_skills,
        )
        session.add(record)
        imported.append(record)
        seen_urls.add(job.url)

    session.commit()
    for record in imported:
        session.refresh(record)

    return JobImportResponse(
        imported=[_job_response(record) for record in imported],
        skipped_urls=skipped_urls,
    )


@router.get("", response_model=list[JobResponse])
def list_jobs(session: SessionDependency) -> list[JobResponse]:
    jobs = session.scalars(select(JobRecord).order_by(JobRecord.id.desc())).all()
    return [_job_response(job) for job in jobs]


@router.post(
    "/{job_id}/evaluate",
    response_model=StoredEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_saved_job(
    job_id: int,
    request: JobEvaluationRequest,
    session: SessionDependency,
) -> StoredEvaluationResponse:
    job = _get_job_or_404(session, job_id)
    profile = session.get(CareerProfileRecord, request.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    evaluation = evaluate_and_store(session, job, profile)
    session.commit()
    session.refresh(evaluation)
    return StoredEvaluationResponse(
        id=evaluation.id,
        profile_id=evaluation.profile_id,
        job_url=job.url,
        score=evaluation.score,
        recommendation=evaluation.recommendation,
        reasons=evaluation.reasons,
        missing_requirements=evaluation.missing_requirements,
        matched_skills=evaluation.matched_skills,
        evaluated_at=evaluation.evaluated_at,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, session: SessionDependency) -> JobResponse:
    return _job_response(_get_job_or_404(session, job_id))


def _get_job_or_404(session: Session, job_id: int) -> JobRecord:
    job = session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


def _job_response(record: JobRecord) -> JobResponse:
    return JobResponse(
        id=record.id,
        title=record.title,
        company=record.company,
        url=record.url,
        description=record.description,
        required_skills=record.required_skills,
        created_at=record.created_at,
    )
