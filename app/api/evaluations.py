from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.evaluator import JobEvaluator
from app.api.schemas import EvaluationRequest, StoredEvaluationResponse
from app.domain.enums import Recommendation
from app.domain.models import CareerProfile, Job
from app.repositories.database import get_session
from app.repositories.tables import (
    CareerProfileRecord,
    EvaluationRecord,
    JobRecord,
)

router = APIRouter(tags=["evaluations"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post(
    "/evaluations",
    response_model=StoredEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_job(
    request: EvaluationRequest,
    session: SessionDependency,
) -> StoredEvaluationResponse:
    profile_record, profile = _profile_for_evaluation(session, request)
    job = Job(
        title=request.job.title,
        company=request.job.company,
        url=request.job.url,
        description=request.job.description,
        required_skills=request.job.required_skills,
    )
    evaluation = JobEvaluator(profile).evaluate(job)

    job_record = JobRecord(
        title=job.title,
        company=job.company,
        url=job.url,
        description=job.description,
        required_skills=job.required_skills,
    )
    session.add(job_record)
    session.flush()

    record = EvaluationRecord(
        job_id=job_record.id,
        profile_id=profile_record.id,
        score=evaluation.score,
        recommendation=evaluation.recommendation,
        reasons=evaluation.reasons,
        missing_requirements=evaluation.missing_requirements,
        matched_skills=evaluation.matched_skills,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return _response(record, job_record.url)


@router.get("/evaluations", response_model=list[StoredEvaluationResponse])
def list_evaluations(
    session: SessionDependency,
    recommendation: Recommendation | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
) -> list[StoredEvaluationResponse]:
    statement = select(EvaluationRecord, JobRecord.url).join(
        JobRecord,
        EvaluationRecord.job_id == JobRecord.id,
    )
    if recommendation is not None:
        statement = statement.where(
            EvaluationRecord.recommendation == recommendation
        )
    if min_score is not None:
        statement = statement.where(EvaluationRecord.score >= min_score)

    rows = session.execute(statement.order_by(EvaluationRecord.id.desc())).all()
    return [_response(record, job_url) for record, job_url in rows]


@router.get("/evaluations/{evaluation_id}", response_model=StoredEvaluationResponse)
def get_evaluation(
    evaluation_id: int,
    session: SessionDependency,
) -> StoredEvaluationResponse:
    row = session.execute(
        select(EvaluationRecord, JobRecord.url)
        .join(JobRecord, EvaluationRecord.job_id == JobRecord.id)
        .where(EvaluationRecord.id == evaluation_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")

    record, job_url = row
    return _response(record, job_url)


def _profile_for_evaluation(
    session: Session,
    request: EvaluationRequest,
) -> tuple[CareerProfileRecord, CareerProfile]:
    if request.profile_id is not None:
        profile_record = session.get(CareerProfileRecord, request.profile_id)
        if profile_record is None:
            raise HTTPException(status_code=404, detail="Profile not found.")
    else:
        assert request.profile is not None
        profile_record = CareerProfileRecord(
            skills=request.profile.skills,
            target_titles=request.profile.target_titles,
        )
        session.add(profile_record)
        session.flush()

    profile = CareerProfile(
        skills=profile_record.skills,
        target_titles=profile_record.target_titles,
    )
    return profile_record, profile


def _response(
    record: EvaluationRecord,
    job_url: str,
) -> StoredEvaluationResponse:
    return StoredEvaluationResponse(
        id=record.id,
        profile_id=record.profile_id,
        job_url=job_url,
        score=record.score,
        recommendation=record.recommendation,
        reasons=record.reasons,
        missing_requirements=record.missing_requirements,
        matched_skills=record.matched_skills,
        evaluated_at=record.evaluated_at,
    )
