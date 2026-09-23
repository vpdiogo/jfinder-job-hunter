import re

_TECHNOLOGIES = (
    "Python", "FastAPI", "Django", "Flask", "SQLAlchemy", "PostgreSQL",
    "SQLite", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
    "React", "TypeScript", "JavaScript", "Node.js", "Java", "Go", "Kafka",
)
_DESIRED_HEADINGS = ("desejável", "desejáveis", "desejaveis", "diferencial", "diferenciais", "nice to have", "bonus")
_RESPONSIBILITY_HEADINGS = ("responsabilidades", "responsibilities", "o que você fará", "what you will do")


class JobDescriptionParser:
    """Extract transparent, reviewable signals from pasted job descriptions."""

    def extract(self, description: str) -> dict[str, object]:
        normalized = description.casefold()
        desired_lines = self._section_lines(description, _DESIRED_HEADINGS)
        desired_text = "\n".join(desired_lines).casefold()
        required_technologies = [
            technology
            for technology in _TECHNOLOGIES
            if technology.casefold() in normalized and technology.casefold() not in desired_text
        ]
        desired_technologies = [
            technology
            for technology in _TECHNOLOGIES
            if technology.casefold() in desired_text
        ]
        return {
            "responsibilities": self._section_lines(description, _RESPONSIBILITY_HEADINGS),
            "required_technologies": required_technologies,
            "desired_technologies": desired_technologies,
            "seniority": self._seniority(normalized),
            "work_mode": self._work_mode(normalized),
            "languages": self._languages(normalized),
        }

    def _section_lines(self, description: str, headings: tuple[str, ...]) -> list[str]:
        lines = [line.strip().lstrip("-•* ") for line in description.splitlines()]
        collecting = False
        values: list[str] = []
        for line in lines:
            normalized = line.rstrip(":").casefold()
            if any(heading in normalized for heading in headings):
                collecting = True
                continue
            if collecting and not line:
                break
            if collecting and line:
                values.append(line)
        return values[:8]

    @staticmethod
    def _seniority(description: str) -> str | None:
        for value in ("tech lead", "staff", "senior", "pleno", "mid", "junior"):
            if re.search(rf"\b{re.escape(value)}\b", description):
                return value
        return None

    @staticmethod
    def _work_mode(description: str) -> str | None:
        if "remote" in description or "remoto" in description:
            return "remote"
        if "hybrid" in description or "híbrido" in description or "hibrido" in description:
            return "hybrid"
        if "on-site" in description or "presencial" in description:
            return "on-site"
        return None

    @staticmethod
    def _languages(description: str) -> list[str]:
        return [
            language
            for language, terms in (
                ("English", ("english", "inglês", "ingles")),
                ("Portuguese", ("portuguese", "português", "portugues")),
                ("Spanish", ("spanish", "espanhol")),
            )
            if any(term in description for term in terms)
        ]
