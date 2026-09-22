from fastapi.testclient import TestClient


def jobs_payload() -> dict[str, object]:
    return {
        "jobs": [
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://example.com/jobs/1",
                "required_skills": ["Python", "FastAPI"],
            },
            {
                "title": "Platform Engineer",
                "company": "Globex",
                "url": "https://example.com/jobs/2",
                "description": "Build systems with Python.",
                "required_skills": ["Python", "Kubernetes"],
            },
        ]
    }


def test_imports_lists_and_deduplicates_jobs(client: TestClient) -> None:
    imported = client.post("/jobs/import", json=jobs_payload())

    assert imported.status_code == 201
    body = imported.json()
    assert len(body["imported"]) == 2
    assert body["skipped_urls"] == []

    duplicate = client.post("/jobs/import", json=jobs_payload())

    assert duplicate.status_code == 201
    assert duplicate.json()["imported"] == []
    assert duplicate.json()["skipped_urls"] == [
        "https://example.com/jobs/1",
        "https://example.com/jobs/2",
    ]

    listed = client.get("/jobs")

    assert listed.status_code == 200
    assert len(listed.json()) == 2


def test_evaluates_imported_job_with_profile(client: TestClient) -> None:
    job = client.post("/jobs/import", json=jobs_payload()).json()["imported"][0]
    profile = client.post(
        "/profiles",
        json={
            "skills": ["Python", "FastAPI"],
            "target_titles": ["Backend Engineer"],
        },
    ).json()

    response = client.post(
        f"/jobs/{job['id']}/evaluate",
        json={"profile_id": profile["id"]},
    )

    assert response.status_code == 201
    assert response.json()["profile_id"] == profile["id"]
    assert response.json()["recommendation"] == "apply"


def test_returns_not_found_for_unknown_job(client: TestClient) -> None:
    response = client.post("/jobs/999/evaluate", json={"profile_id": 1})

    assert response.status_code == 404


def test_rejects_empty_job_import(client: TestClient) -> None:
    response = client.post("/jobs/import", json={"jobs": []})

    assert response.status_code == 422


def test_lists_evaluations_for_an_imported_job(client: TestClient) -> None:
    job = client.post("/jobs/import", json=jobs_payload()).json()["imported"][0]
    profile = client.post(
        "/profiles",
        json={
            "skills": ["Python", "FastAPI"],
            "target_titles": ["Backend Engineer"],
        },
    ).json()
    client.post(f"/jobs/{job['id']}/evaluate", json={"profile_id": profile["id"]})

    response = client.get(f"/jobs/{job['id']}/evaluations")

    assert response.status_code == 200
    assert response.json()[0]["job_url"] == "https://example.com/jobs/1"


def test_persists_enriched_job_fields(client: TestClient) -> None:
    response = client.post(
        "/jobs/import",
        json={
            "jobs": [
                {
                    "title": "Senior Backend Engineer",
                    "company": "Acme",
                    "url": "https://example.com/jobs/enriched",
                    "required_technologies": ["Python"],
                    "desired_technologies": ["Docker"],
                    "seniority": "senior",
                    "work_mode": "remote",
                    "location": "Brazil",
                    "timezone": "America/Sao_Paulo",
                    "salary_min": 120000,
                    "salary_max": 180000,
                    "languages": ["English"],
                }
            ]
        },
    )

    assert response.status_code == 201
    job = response.json()["imported"][0]
    assert job["required_technologies"] == ["Python"]
    assert job["work_mode"] == "remote"
