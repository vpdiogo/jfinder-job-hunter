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
        required_technologies=job_record.required_technologies or [],
        desired_technologies=job_record.desired_technologies or [],
        seniority=job_record.seniority,
        work_mode=job_record.work_mode,
        location=job_record.location,
        timezone=job_record.timezone,
        salary_min=job_record.salary_min,
        salary_max=job_record.salary_max,
        languages=job_record.languages or [],
    )
    profile = CareerProfile(
        skills=profile_record.skills,
        target_titles=profile_record.target_titles,
        desired_seniority=profile_record.desired_seniority,
        work_modes=profile_record.work_modes or [],
        locations=profile_record.locations or [],
        timezones=profile_record.timezones or [],
        salary_min=profile_record.salary_min,
        salary_max=profile_record.salary_max,
        languages=profile_record.languages or [],
        required_technologies=profile_record.required_technologies or [],
        desired_technologies=profile_record.desired_technologies or [],
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
