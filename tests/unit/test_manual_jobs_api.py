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
