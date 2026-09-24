from fastapi.testclient import TestClient

DESCRIPTION = """\
Senior Backend Engineer

Responsabilidades:
- Liderar a evolução da plataforma
- Orientar pessoas do time

Requisitos:
- Python, FastAPI e Kubernetes
- Inglês avançado
- Trabalho remoto

Diferenciais:
- Terraform e AWS
"""


def create_profile(client: TestClient) -> int:
    return client.post(
        "/profiles",
        json={
            "name": "Backend Engineer",
            "skills": ["Python", "FastAPI", "Kubernetes"],
            "target_titles": ["Backend Engineer"],
        },
    ).json()["id"]


def test_extracts_reviewable_job_data(client: TestClient) -> None:
    response = client.post("/jobs/extract", json={"description": DESCRIPTION})

    assert response.status_code == 200
    assert response.json() == {
        "responsibilities": [
            "Liderar a evolução da plataforma",
            "Orientar pessoas do time",
        ],
        "required_technologies": ["Python", "FastAPI", "Kubernetes"],
        "desired_technologies": ["AWS", "Terraform"],
        "seniority": "senior",
        "work_mode": "remote",
        "languages": ["English"],
    }


def test_creates_manual_job_associates_profile_and_evaluates(
    client: TestClient,
) -> None:
    profile_id = create_profile(client)
    response = client.post(
        "/jobs/manual",
        json={
            "profile_id": profile_id,
            "job": {
                "title": "Senior Backend Engineer",
                "company": "Acme",
                "url": "https://www.linkedin.com/jobs/view/123",
                "description": DESCRIPTION,
                "responsibilities": ["Liderar a evolução da plataforma"],
                "required_technologies": ["Python", "FastAPI", "Kubernetes"],
                "desired_technologies": ["Terraform", "AWS"],
                "seniority": "senior",
                "work_mode": "remote",
                "languages": ["English"],
                "source": "linkedin",
            },
        },
    )

    assert response.status_code == 201
    job = response.json()
    assert job["focus_profile_id"] == profile_id
    assert job["source"] == "linkedin"
    assert job["status"] == "evaluated"
    assert job["recommendation"] == "apply"
    assert job["responsibilities"] == ["Liderar a evolução da plataforma"]

    duplicate = client.post(
        "/jobs/manual",
        json={
            "profile_id": profile_id,
            "job": {
                "title": "Same job",
                "company": "Acme",
                "url": "https://www.linkedin.com/jobs/view/123",
            },
        },
    )
    assert duplicate.status_code == 409


def test_extracts_accented_plural_desired_section(client: TestClient) -> None:
    response = client.post(
        "/jobs/extract",
        json={
            "description": """\
Requisitos:
- Python

Desejáveis:
- Terraform e AWS
"""
        },
    )

    assert response.status_code == 200
    assert response.json()["required_technologies"] == ["Python"]
    assert response.json()["desired_technologies"] == ["AWS", "Terraform"]


def test_updates_manual_job_and_stores_a_fresh_evaluation(client: TestClient) -> None:
    profile_id = create_profile(client)
    created = client.post(
        "/jobs/manual",
        json={
            "profile_id": profile_id,
            "job": {
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://example.com/jobs/backend",
                "required_technologies": ["Python"],
            },
        },
    ).json()

    updated = client.put(
        f"/jobs/{created['id']}",
        json={
            "title": "Senior Backend Engineer",
            "company": "Globex",
            "url": "https://example.com/jobs/backend",
            "description": "Detalhes confirmados com a recrutadora.",
            "required_skills": [],
            "responsibilities": ["Liderar o time"],
            "source": "manual",
            "required_technologies": ["Python", "FastAPI"],
            "desired_technologies": ["Kubernetes"],
            "seniority": "senior",
            "work_mode": "remote",
            "location": None,
            "timezone": None,
            "salary_min": None,
            "salary_max": None,
            "languages": ["English"],
        },
    )

    assert updated.status_code == 200
    assert updated.json()["title"] == "Senior Backend Engineer"
    assert updated.json()["company"] == "Globex"
    assert updated.json()["responsibilities"] == ["Liderar o time"]
    evaluations = client.get(f"/jobs/{created['id']}/evaluations").json()
    assert len(evaluations) == 2
    assert evaluations[0]["profile_id"] == profile_id
