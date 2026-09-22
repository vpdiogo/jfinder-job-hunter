from fastapi import APIRouter

from app.agents.evaluator import JobEvaluator
from app.api.schemas import EvaluationRequest, EvaluationResponse
from app.domain.models import CareerProfile, Job

router = APIRouter(tags=["evaluations"])


@router.post("/evaluations", response_model=EvaluationResponse)
def evaluate_job(request: EvaluationRequest) -> EvaluationResponse:
    profile = CareerProfile(
        skills=request.profile.skills,
        target_titles=request.profile.target_titles,
    )
    job = Job(
        title=request.job.title,
        company=request.job.company,
        url=request.job.url,
        description=request.job.description,
        required_skills=request.job.required_skills,
    )
    evaluation = JobEvaluator(profile).evaluate(job)

    return EvaluationResponse(
        job_url=evaluation.job_url,
        score=evaluation.score,
        recommendation=evaluation.recommendation,
        reasons=evaluation.reasons,
        missing_requirements=evaluation.missing_requirements,
        matched_skills=evaluation.matched_skills,
    )
