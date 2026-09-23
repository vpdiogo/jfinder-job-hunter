import re
from collections.abc import Iterable
from dataclasses import dataclass

_SECTION_NAMES = {
    "skills": {"skills", "competências", "competencias", "tecnologias"},
    "languages": {"languages", "idiomas"},
    "experiences": {
        "experience",
        "experiences",
        "experiência",
        "experiencias",
        "experiências profissionais",
        "experiência profissional",
    },
    "education": {"education", "formação", "formacao", "academic background"},
    "target_titles": {"target roles", "cargos alvo", "cargos-alvo", "objetivo"},
}
_ROLE_PATTERN = re.compile(
    r"\b(engineer|developer|desenvolvedor|analyst|analista|architect|arquiteto|"
    r"manager|gerente|specialist|especialista|tech lead|líder técnico|lider tecnico|lead)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ResumeDraft:
    skills: list[str]
    target_titles: list[str]
    languages: list[str]
    experiences: list[str]
    education: list[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "skills": self.skills,
            "target_titles": self.target_titles,
            "languages": self.languages,
            "experiences": self.experiences,
            "education": self.education,
        }


class ResumeParser:
    """Extract reviewable profile data from conventional plain-text resumes."""

    def extract(self, content: str) -> ResumeDraft:
        sections = {name: [] for name in _SECTION_NAMES}
        current_section: str | None = None
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            section = self._section_for(line)
            if section is not None:
                current_section = section
                continue
            if current_section is not None:
                sections[current_section].append(line.lstrip("-•* "))

        skills = self._items(sections["skills"])
        languages = self._items(sections["languages"])
        experiences = self._unique(sections["experiences"])
        education = self._unique(sections["education"])
        target_titles = self._items(sections["target_titles"])
        if not target_titles:
            target_titles = [
                experience for experience in experiences if _ROLE_PATTERN.search(experience)
            ]

        return ResumeDraft(
            skills=skills,
            target_titles=self._unique(target_titles),
            languages=languages,
            experiences=experiences,
            education=education,
        )

    def _section_for(self, line: str) -> str | None:
        normalized = " ".join(line.rstrip(":").casefold().split())
        for section, names in _SECTION_NAMES.items():
            if normalized in names:
                return section
        return None

    def _items(self, lines: list[str]) -> list[str]:
        return self._unique(
            item.strip()
            for line in lines
            for item in re.split(r"[,;|]", line)
            if item.strip()
        )

    @staticmethod
    def _unique(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            normalized = " ".join(value.casefold().split())
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(value)
        return result
