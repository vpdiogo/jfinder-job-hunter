from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    JobDescriptionExtractionRequest,
    JobDescriptionExtractionResponse,
    JobEvaluationRequest,
    JobImportRequest,
    JobImportResponse,
    JobNoteInput,
    JobNoteResponse,
    JobQueueResponse,
    JobResponse,
    JobStatusResponse,
    JobStatusUpdateRequest,
    ManualJobCreateRequest,
    StoredEvaluationResponse,
)
from app.domain.enums import JobStatus, Recommendation
from app.repositories.database import get_session
from app.repositories.tables import (
    ApplicationRecord,
    CareerProfileRecord,
    EvaluationRecord,
    JobNoteRecord,
    JobRecord,
)
from app.services.application_service import (
    InvalidStatusTransition,
    get_or_create_application,
    transition_application,
)
from app.services.evaluation_service import evaluate_and_store
from app.services.job_description_parser import JobDescriptionParser

router = APIRouter(prefix="/jobs", tags=["jobs"])
SessionDependency = Annotated[Session, Depends(get_session)]
StatusFilter = Annotated[JobStatus | None, Query(alias="status")]


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

        record = JobRecord(**job.model_dump())
        session.add(record)
        imported.append(record)
        seen_urls.add(job.url)

    session.flush()
    for record in imported:
        get_or_create_application(session, record.id)
    session.commit()
    for record in imported:
        session.refresh(record)

    return JobImportResponse(
        imported=[_job_response(record) for record in imported],
        skipped_urls=skipped_urls,
    )


@router.post("/extract", response_model=JobDescriptionExtractionResponse)
def extract_job_description(
    request: JobDescriptionExtractionRequest,
) -> JobDescriptionExtractionResponse:
    return JobDescriptionExtractionResponse(
        **JobDescriptionParser().extract(request.description)
    )


@router.post(
    "/manual",
    response_model=JobQueueResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_job(
    request: ManualJobCreateRequest,
    session: SessionDependency,
) -> JobQueueResponse:
    existing = session.scalar(
        select(JobRecord.id).where(JobRecord.url == request.job.url)
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A job with this URL already exists.",
        )

    profile = session.get(CareerProfileRecord, request.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    job = JobRecord(**request.job.model_dump(), focus_profile_id=profile.id)
    session.add(job)
    session.flush()
    application = get_or_create_application(session, job.id)
    evaluation = evaluate_and_store(session, job, profile)
    session.commit()
    session.refresh(job)
    session.refresh(application)
    session.refresh(evaluation)
    return _queue_response(job, application, evaluation)


@router.get("", response_model=list[JobResponse])
def list_jobs(session: SessionDependency) -> list[JobResponse]:
    jobs = session.scalars(select(JobRecord).order_by(JobRecord.id.desc())).all()
    return [_job_response(job) for job in jobs]


@router.get("/queue", response_model=list[JobQueueResponse])
def list_job_queue(
    session: SessionDependency,
    job_status: StatusFilter = None,
    recommendation: Recommendation | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
) -> list[JobQueueResponse]:
    latest_evaluation_id = (
        select(EvaluationRecord.id)
        .where(EvaluationRecord.job_id == JobRecord.id)
        .order_by(EvaluationRecord.id.desc())
        .limit(1)
        .correlate(JobRecord)
        .scalar_subquery()
    )
    queue_status = case(
        (ApplicationRecord.status.is_not(None), ApplicationRecord.status),
        (EvaluationRecord.id.is_not(None), JobStatus.EVALUATED),
        else_=JobStatus.DISCOVERED,
    )
    statement = (
        select(JobRecord, ApplicationRecord, EvaluationRecord)
        .outerjoin(ApplicationRecord, ApplicationRecord.job_id == JobRecord.id)
        .outerjoin(EvaluationRecord, EvaluationRecord.id == latest_evaluation_id)
    )
    if job_status is not None:
        statement = statement.where(
            queue_status == job_status
        )
    if recommendation is not None:
        statement = statement.where(EvaluationRecord.recommendation == recommendation)
    if min_score is not None:
        statement = statement.where(EvaluationRecord.score >= min_score)

    rows = session.execute(
        statement.order_by(EvaluationRecord.score.desc(), JobRecord.id.desc())
    ).all()
    return [_queue_response(job, application, evaluation) for job, application, evaluation in rows]


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


@router.post("/{job_id}/interest", response_model=JobStatusResponse)
def mark_job_interesting(
    job_id: int,
    session: SessionDependency,
) -> JobStatusResponse:
    return _transition_response(session, job_id, JobStatus.INTERESTED)


@router.post("/{job_id}/apply", response_model=JobStatusResponse)
def mark_job_applied(
    job_id: int,
    session: SessionDependency,
) -> JobStatusResponse:
    return _transition_response(session, job_id, JobStatus.APPLIED)


@router.post("/{job_id}/status", response_model=JobStatusResponse)
def update_job_status(
    job_id: int,
    request: JobStatusUpdateRequest,
    session: SessionDependency,
) -> JobStatusResponse:
    return _transition_response(session, job_id, request.status)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, session: SessionDependency) -> JobResponse:
    return _job_response(_get_job_or_404(session, job_id))


@router.get("/{job_id}/notes", response_model=list[JobNoteResponse])
def list_job_notes(
    job_id: int,
    session: SessionDependency,
) -> list[JobNoteResponse]:
    _get_job_or_404(session, job_id)
    notes = session.scalars(
        select(JobNoteRecord)
        .where(JobNoteRecord.job_id == job_id)
        .order_by(JobNoteRecord.updated_at.desc(), JobNoteRecord.id.desc())
    ).all()
    return [_note_response(note) for note in notes]


@router.post(
    "/{job_id}/notes",
    response_model=JobNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job_note(
    job_id: int,
    request: JobNoteInput,
    session: SessionDependency,
) -> JobNoteResponse:
    _get_job_or_404(session, job_id)
    note = JobNoteRecord(job_id=job_id, content=request.content)
    session.add(note)
    session.commit()
    session.refresh(note)
    return _note_response(note)


@router.put("/{job_id}/notes/{note_id}", response_model=JobNoteResponse)
def update_job_note(
    job_id: int,
    note_id: int,
    request: JobNoteInput,
    session: SessionDependency,
) -> JobNoteResponse:
    _get_job_or_404(session, job_id)
    note = session.get(JobNoteRecord, note_id)
    if note is None or note.job_id != job_id:
        raise HTTPException(status_code=404, detail="Job note not found.")
    note.content = request.content
    session.commit()
    session.refresh(note)
    return _note_response(note)


def _transition_response(
    session: Session,
    job_id: int,
    target_status: JobStatus,
) -> JobStatusResponse:
    _get_job_or_404(session, job_id)
    try:
        application = transition_application(session, job_id, target_status)
    except InvalidStatusTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    session.commit()
    session.refresh(application)
    return JobStatusResponse(
        job_id=job_id,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
    )


def _get_job_or_404(session: Session, job_id: int) -> JobRecord:
    job = session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


def _note_response(record: JobNoteRecord) -> JobNoteResponse:
    return JobNoteResponse(
        id=record.id,
        job_id=record.job_id,
        content=record.content,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _job_response(record: JobRecord) -> JobResponse:
    return JobResponse(
        id=record.id,
        title=record.title,
        company=record.company,
        url=record.url,
        description=record.description,
        required_skills=record.required_skills,
        responsibilities=record.responsibilities or [],
        source=record.source or "manual",
        focus_profile_id=record.focus_profile_id,
        required_technologies=record.required_technologies or [],
        desired_technologies=record.desired_technologies or [],
        seniority=record.seniority,
        work_mode=record.work_mode,
        location=record.location,
        timezone=record.timezone,
        salary_min=record.salary_min,
        salary_max=record.salary_max,
        languages=record.languages or [],
        created_at=record.created_at,
    )


def _queue_response(
    job: JobRecord,
    application: ApplicationRecord | None,
    evaluation: EvaluationRecord | None,
) -> JobQueueResponse:
    return JobQueueResponse(
        **_job_response(job).model_dump(),
        status=(
            application.status
            if application
            else JobStatus.EVALUATED
            if evaluation
            else JobStatus.DISCOVERED
        ),
        score=evaluation.score if evaluation else None,
        recommendation=evaluation.recommendation if evaluation else None,
        applied_at=application.applied_at if application else None,
    )

@router.get(
    "/{job_id}/evaluations",
    response_model=list[StoredEvaluationResponse],
)
def list_job_evaluations(
    job_id: int,
    session: SessionDependency,
) -> list[StoredEvaluationResponse]:
    job = _get_job_or_404(session, job_id)
    records = session.scalars(
        select(EvaluationRecord)
        .where(EvaluationRecord.job_id == job.id)
        .order_by(EvaluationRecord.id.desc())
    ).all()
    return [
        StoredEvaluationResponse(
            id=record.id,
            profile_id=record.profile_id,
            job_url=job.url,
            score=record.score,
            recommendation=record.recommendation,
            reasons=record.reasons,
            missing_requirements=record.missing_requirements,
            matched_skills=record.matched_skills,
            evaluated_at=record.evaluated_at,
        )
        for record in records
    ]
