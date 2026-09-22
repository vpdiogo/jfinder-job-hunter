from app.domain.enums import Recommendation
from app.domain.models import CareerProfile, Job, JobEvaluation


class JobEvaluator:
    """Evaluate a job with transparent, deterministic matching rules."""

    def __init__(self, profile: CareerProfile) -> None:
        self.profile = profile

    def evaluate(self, job: Job) -> JobEvaluation:
        if not self._has_enriched_criteria(job):
            return self._evaluate_legacy(job)

        requirements = self._unique(
            self._requirements_for(job) + job.required_technologies
        )
        available_technologies = self._unique(
            self.profile.skills
            + self.profile.required_technologies
            + self.profile.desired_technologies
        )
        available_normalized = self._normalized(available_technologies)
        matched_skills = [
            requirement
            for requirement in requirements
            if self._normalize(requirement) in available_normalized
        ]
        missing_requirements = [
            requirement
            for requirement in requirements
            if self._normalize(requirement) not in available_normalized
        ]

        components: list[tuple[float, float]] = []
        reasons: list[str] = []
        if requirements:
            ratio = len(matched_skills) / len(requirements)
            components.append((60, 60 * ratio))
            reasons.append(
                f"Required technologies: {len(matched_skills)}/{len(requirements)} matched."
            )
        else:
            reasons.append("Required technologies: insufficient information.")

        desired_matches = self._matches(job.desired_technologies, available_normalized)
        if job.desired_technologies:
            components.append((10, 10 * len(desired_matches) / len(job.desired_technologies)))
            reasons.append(
                f"Desired technologies: {len(desired_matches)}/{len(job.desired_technologies)} matched."
            )

        if self.profile.target_titles:
            title_matches = self._title_matches(job.title)
            components.append((10, 10 if title_matches else 0))
            reasons.append(
                "Target role: matched."
                if title_matches
                else "Target role: no match."
            )

        self._add_exact_match_component(
            components,
            reasons,
            "Seniority",
            job.seniority,
            self.profile.desired_seniority,
            5,
        )
        self._add_list_match_component(
            components,
            reasons,
            "Work mode",
            job.work_mode,
            self.profile.work_modes,
            5,
        )
        self._add_location_component(components, reasons, job)
        self._add_salary_component(components, reasons, job)
        self._add_language_component(components, reasons, job)

        if not components:
            return JobEvaluation(
                job_url=job.url,
                score=0.0,
                recommendation=Recommendation.REVIEW,
                reasons=reasons,
                missing_requirements=missing_requirements,
                matched_skills=matched_skills,
            )

        total_weight = sum(weight for weight, _ in components)
        score = round(100 * sum(value for _, value in components) / total_weight, 2)
        return JobEvaluation(
            job_url=job.url,
            score=score,
            recommendation=self._recommendation(score),
            reasons=reasons,
            missing_requirements=missing_requirements,
            matched_skills=matched_skills,
        )

    def _evaluate_legacy(self, job: Job) -> JobEvaluation:
        requirements = self._requirements_for(job)
        profile_skills = self._normalized(self.profile.skills)
        matched_skills = self._matches(requirements, profile_skills)
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
                reasons=["Insufficient skill requirements for a reliable score."],
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
            reasons=self._legacy_reasons(matched_skills, title_matches),
            missing_requirements=missing_requirements,
            matched_skills=matched_skills,
        )

    def _add_exact_match_component(
        self,
        components: list[tuple[float, float]],
        reasons: list[str],
        label: str,
        job_value: str | None,
        profile_value: str | None,
        weight: float,
    ) -> None:
        if job_value is None and profile_value is None:
            return
        if job_value is None or profile_value is None:
            reasons.append(f"{label}: insufficient information.")
            return
        matches = self._normalize(job_value) == self._normalize(profile_value)
        components.append((weight, weight if matches else 0))
        reasons.append(f"{label}: {'matched' if matches else 'no match'}.")

    def _add_list_match_component(
        self,
        components: list[tuple[float, float]],
        reasons: list[str],
        label: str,
        job_value: str | None,
        profile_values: list[str],
        weight: float,
    ) -> None:
        if job_value is None and not profile_values:
            return
        if job_value is None or not profile_values:
            reasons.append(f"{label}: insufficient information.")
            return
        matches = self._normalize(job_value) in self._normalized(profile_values)
        components.append((weight, weight if matches else 0))
        reasons.append(f"{label}: {'matched' if matches else 'no match'}.")

    def _add_location_component(
        self,
        components: list[tuple[float, float]],
        reasons: list[str],
        job: Job,
    ) -> None:
        checks: list[bool] = []
        if job.location is not None and self.profile.locations:
            checks.append(self._normalize(job.location) in self._normalized(self.profile.locations))
        elif job.location is not None or self.profile.locations:
            reasons.append("Location: insufficient information.")
        if job.timezone is not None and self.profile.timezones:
            checks.append(self._normalize(job.timezone) in self._normalized(self.profile.timezones))
        elif job.timezone is not None or self.profile.timezones:
            reasons.append("Timezone: insufficient information.")
        if checks:
            components.append((5, 5 * sum(checks) / len(checks)))
            reasons.append("Location/timezone: matched." if all(checks) else "Location/timezone: no match.")

    def _add_salary_component(
        self,
        components: list[tuple[float, float]],
        reasons: list[str],
        job: Job,
    ) -> None:
        job_range = (job.salary_min, job.salary_max)
        profile_range = (self.profile.salary_min, self.profile.salary_max)
        if job_range == (None, None) and profile_range == (None, None):
            return
        if None in job_range or None in profile_range:
            reasons.append("Salary: insufficient information.")
            return
        overlaps = max(job.salary_min, self.profile.salary_min) <= min(job.salary_max, self.profile.salary_max)  # type: ignore[arg-type]
        components.append((5, 5 if overlaps else 0))
        reasons.append("Salary: range overlaps." if overlaps else "Salary: range does not overlap.")

    def _add_language_component(
        self,
        components: list[tuple[float, float]],
        reasons: list[str],
        job: Job,
    ) -> None:
        if not job.languages and not self.profile.languages:
            return
        if not job.languages or not self.profile.languages:
            reasons.append("Languages: insufficient information.")
            return
        matches = self._matches(job.languages, self._normalized(self.profile.languages))
        components.append((5, 5 * len(matches) / len(job.languages)))
        reasons.append(f"Languages: {len(matches)}/{len(job.languages)} matched.")

    def _has_enriched_criteria(self, job: Job) -> bool:
        return any(
            (
                job.required_technologies,
                job.desired_technologies,
                job.seniority,
                job.work_mode,
                job.location,
                job.timezone,
                job.salary_min is not None,
                job.salary_max is not None,
                job.languages,
                self.profile.desired_seniority,
                self.profile.work_modes,
                self.profile.locations,
                self.profile.timezones,
                self.profile.salary_min is not None,
                self.profile.salary_max is not None,
                self.profile.languages,
                self.profile.required_technologies,
                self.profile.desired_technologies,
            )
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

    def _matches(self, values: list[str], available: set[str]) -> list[str]:
        return [value for value in values if self._normalize(value) in available]

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        return [
            value
            for value in values
            if not (normalized := self._normalize(value)) in seen and not seen.add(normalized)
        ]

    @staticmethod
    def _recommendation(score: float) -> Recommendation:
        if score >= 75:
            return Recommendation.APPLY
        if score >= 45:
            return Recommendation.REVIEW
        return Recommendation.SKIP

    @staticmethod
    def _legacy_reasons(matched_skills: list[str], title_matches: bool) -> list[str]:
        reasons = [f"Matched skills: {', '.join(matched_skills)}."]
        if title_matches:
            reasons.append("The job title matches a target role.")
        return reasons
