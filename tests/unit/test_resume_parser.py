from app.services.resume_parser import ResumeParser

RESUME_TEXT = """
Experiência Profissional
Senior Backend Engineer — Acme
Desenvolvedor Python — Globex

Competências
Python, FastAPI, SQLAlchemy
Docker | Kubernetes

Idiomas
Português, English

Formação
Bacharelado em Ciência da Computação — Universidade Exemplo
"""


def test_extracts_structured_resume_data() -> None:
    draft = ResumeParser().extract(RESUME_TEXT)

    assert draft.skills == ["Python", "FastAPI", "SQLAlchemy", "Docker", "Kubernetes"]
    assert draft.languages == ["Português", "English"]
    assert draft.target_titles == [
        "Senior Backend Engineer — Acme",
        "Desenvolvedor Python — Globex",
    ]
    assert draft.education == [
        "Bacharelado em Ciência da Computação — Universidade Exemplo"
    ]


def test_uses_tech_lead_experience_as_a_target_role() -> None:
    draft = ResumeParser().extract(
        """
Experiência Profissional
Tech Lead — Acme

Competências
Python
"""
    )

    assert draft.target_titles == ["Tech Lead — Acme"]
