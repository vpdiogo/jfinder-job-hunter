from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import JobStatus
from app.repositories.tables import ApplicationRecord, EvaluationRecord


class InvalidStatusTransition(ValueError):
    pass


ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.DISCOVERED: {JobStatus.EVALUATED},
    JobStatus.EVALUATED: {JobStatus.INTERESTED},
    JobStatus.INTERESTED: {JobStatus.APPLIED},
    JobStatus.APPLIED: {JobStatus.RECRUITER, JobStatus.REJECTED},
    JobStatus.RECRUITER: {JobStatus.TECHNICAL, JobStatus.REJECTED},
    JobStatus.TECHNICAL: {JobStatus.FINAL, JobStatus.REJECTED},
    JobStatus.FINAL: {JobStatus.OFFER, JobStatus.REJECTED},
    JobStatus.OFFER: set(),
    JobStatus.REJECTED: set(),
}


def get_or_create_application(
    session: Session,
    job_id: int,
) -> ApplicationRecord:
    application = session.scalar(
        select(ApplicationRecord).where(ApplicationRecord.job_id == job_id)
    )
    if application is not None:
        return application

    existing_evaluation = session.scalar(
        select(EvaluationRecord.id)
        .where(EvaluationRecord.job_id == job_id)
        .limit(1)
    )
    status = (
        JobStatus.EVALUATED
        if existing_evaluation is not None
        else JobStatus.DISCOVERED
    )
    application = ApplicationRecord(
        job_id=job_id,
        status=status,
        applied_at=None,
    )
    session.add(application)
    session.flush()
    return application


def mark_evaluated(session: Session, job_id: int) -> ApplicationRecord:
    application = get_or_create_application(session, job_id)
    if JobStatus(application.status) is JobStatus.DISCOVERED:
        application.status = JobStatus.EVALUATED
    return application


def transition_application(
    session: Session,
    job_id: int,
    target_status: JobStatus,
) -> ApplicationRecord:
    application = get_or_create_application(session, job_id)
    current_status = JobStatus(application.status)
    if target_status is current_status:
        return application
    if target_status not in ALLOWED_TRANSITIONS[current_status]:
        raise InvalidStatusTransition(
            f"Cannot transition from {current_status} to {target_status}."
        )

    application.status = target_status
    if target_status is JobStatus.APPLIED and application.applied_at is None:
        application.applied_at = datetime.now(UTC)
    return application
