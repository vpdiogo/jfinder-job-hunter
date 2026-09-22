from sqlalchemy.orm import Session

from app.agents.evaluator import JobEvaluator
from app.domain.models import CareerProfile, Job
from app.repositories.tables import (
    CareerProfileRecord,
    EvaluationRecord,
    JobRecord,
)
from app.services.application_service import mark_evaluated


def evaluate_and_store(
    session: Session,
    job_record: JobRecord,
    profile_record: CareerProfileRecord,
) -> EvaluationRecord:
    job = Job(
        title=job_record.title,
        company=job_record.company,
        url=job_record.url,
        description=job_record.description,
        required_skills=job_record.required_skills,
    )
    profile = CareerProfile(
        skills=profile_record.skills,
        target_titles=profile_record.target_titles,
    )
    evaluation = JobEvaluator(profile).evaluate(job)
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
    mark_evaluated(session, job_record.id)
    return record
