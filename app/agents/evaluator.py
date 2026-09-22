from app.domain.enums import Recommendation
from app.domain.models import CareerProfile, Job, JobEvaluation


class JobEvaluator:
    """Evaluate a job with transparent, deterministic matching rules."""

    def __init__(self, profile: CareerProfile) -> None:
        self.profile = profile

    def evaluate(self, job: Job) -> JobEvaluation:
        requirements = self._requirements_for(job)
        profile_skills = self._normalized(self.profile.skills)
        matched_skills = [
            skill
            for skill in requirements
            if self._normalize(skill) in profile_skills
        ]
        missing_requirements = [
            skill
            for skill in requirements
            if self._normalize(skill) not in profile_skills
        ]
        title_matches = self._title_matches(job.title)

        if not requirements:
            return JobEvaluation(
                job_url=job.url,
                score=20.0 if title_matches else 0.0,
                recommendation=Recommendation.REVIEW,
                reasons=[
                    "Insufficient skill requirements for a reliable score."
                ],
                missing_requirements=[],
                matched_skills=[],
            )

        skill_score = 80 * len(matched_skills) / len(requirements)
        title_score = 20 if title_matches else 0
        score = round(skill_score + title_score, 2)

        return JobEvaluation(
            job_url=job.url,
            score=score,
            recommendation=self._recommendation(score),
            reasons=self._reasons(matched_skills, title_matches),
            missing_requirements=missing_requirements,
            matched_skills=matched_skills,
        )

    def _requirements_for(self, job: Job) -> list[str]:
        if job.required_skills:
            return job.required_skills

        description = self._normalize(job.description)
        return [
            skill
            for skill in self.profile.skills
            if self._normalize(skill) in description
        ]

    def _title_matches(self, title: str) -> bool:
        normalized_title = self._normalize(title)
        return any(
            self._normalize(target_title) in normalized_title
            for target_title in self.profile.target_titles
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    def _normalized(self, values: list[str]) -> set[str]:
        return {self._normalize(value) for value in values}

    @staticmethod
    def _recommendation(score: float) -> Recommendation:
        if score >= 75:
            return Recommendation.APPLY
        if score >= 45:
            return Recommendation.REVIEW
        return Recommendation.SKIP

    @staticmethod
    def _reasons(matched_skills: list[str], title_matches: bool) -> list[str]:
        reasons = [f"Matched skills: {', '.join(matched_skills)}."]
        if title_matches:
            reasons.append("The job title matches a target role.")
        return reasons
