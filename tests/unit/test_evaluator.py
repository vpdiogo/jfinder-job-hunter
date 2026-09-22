from app.agents.evaluator import JobEvaluator
from app.domain.enums import Recommendation
from app.domain.models import CareerProfile, Job


def test_recommends_apply_for_a_strong_match() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python", "FastAPI", "SQLAlchemy", "Docker"],
            target_titles=["Backend Engineer"],
        )
    )
    job = Job(
        title="Senior Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/1",
        required_skills=["python", "FastAPI", "SQLAlchemy"],
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 100.0
    assert evaluation.recommendation is Recommendation.APPLY
    assert evaluation.matched_skills == ["python", "FastAPI", "SQLAlchemy"]
    assert evaluation.missing_requirements == []


def test_reports_missing_requirements_and_recommends_review() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python", "FastAPI"],
            target_titles=["Backend Engineer"],
        )
    )
    job = Job(
        title="Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/2",
        required_skills=["Python", "Kubernetes", "FastAPI"],
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 73.33
    assert evaluation.recommendation is Recommendation.REVIEW
    assert evaluation.missing_requirements == ["Kubernetes"]


def test_uses_description_when_no_requirements() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python", "FastAPI", "Kubernetes"],
            target_titles=["Platform Engineer"],
        )
    )
    job = Job(
        title="Platform Engineer",
        company="Acme",
        url="https://example.com/jobs/3",
        description="Build APIs with Python and FastAPI.",
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 100.0
    assert evaluation.recommendation is Recommendation.APPLY
    assert evaluation.missing_requirements == []


def test_keeps_low_information_jobs_for_review() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python"],
            target_titles=["Backend Engineer"],
        )
    )
    job = Job(
        title="Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/4",
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 20.0
    assert evaluation.recommendation is Recommendation.REVIEW


def test_enriched_matching_uses_job_preferences_and_profile_constraints() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python", "FastAPI"],
            target_titles=["Backend Engineer"],
            desired_seniority="senior",
            work_modes=["remote"],
            locations=["Brazil"],
            timezones=["America/Sao_Paulo"],
            salary_min=120_000,
            salary_max=180_000,
            languages=["English"],
            desired_technologies=["Docker"],
        )
    )
    job = Job(
        title="Senior Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/enriched",
        required_technologies=["Python", "FastAPI"],
        desired_technologies=["Docker"],
        seniority="Senior",
        work_mode="Remote",
        location="Brazil",
        timezone="America/Sao_Paulo",
        salary_min=130_000,
        salary_max=170_000,
        languages=["English"],
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 100.0
    assert evaluation.recommendation is Recommendation.APPLY
    assert "Seniority: matched." in evaluation.reasons
    assert "Salary: range overlaps." in evaluation.reasons


def test_enriched_matching_reports_missing_information_without_penalty() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python"],
            desired_seniority="senior",
            work_modes=["remote"],
        )
    )
    job = Job(
        title="Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/incomplete",
        required_technologies=["Python"],
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.score == 100.0
    assert "Seniority: insufficient information." in evaluation.reasons
    assert "Work mode: insufficient information." in evaluation.reasons


def test_enriched_matching_identifies_incompatible_constraints() -> None:
    evaluator = JobEvaluator(
        CareerProfile(
            skills=["Python"],
            desired_seniority="senior",
            work_modes=["remote"],
            salary_min=150_000,
            salary_max=180_000,
            languages=["English"],
        )
    )
    job = Job(
        title="Backend Engineer",
        company="Acme",
        url="https://example.com/jobs/mismatch",
        required_technologies=["Python", "Kubernetes"],
        seniority="mid",
        work_mode="on-site",
        salary_min=80_000,
        salary_max=100_000,
        languages=["Portuguese", "English"],
    )

    evaluation = evaluator.evaluate(job)

    assert evaluation.recommendation is Recommendation.SKIP
    assert "Kubernetes" in evaluation.missing_requirements
    assert "Seniority: no match." in evaluation.reasons
    assert "Work mode: no match." in evaluation.reasons
    assert "Salary: range does not overlap." in evaluation.reasons
