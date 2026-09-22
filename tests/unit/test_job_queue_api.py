from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.repositories.database import get_engine
from app.repositories.tables import ApplicationRecord


def create_job(client: TestClient) -> int:
    response = client.post(
        "/jobs/import",
        json={
            "jobs": [
                {
                    "title": "Backend Engineer",
                    "company": "Acme",
                    "url": "https://example.com/jobs/queue-1",
                    "required_skills": ["Python", "FastAPI"],
                }
            ]
        },
    )
    return response.json()["imported"][0]["id"]


def create_profile(client: TestClient) -> int:
    response = client.post(
        "/profiles",
        json={
            "skills": ["Python", "FastAPI"],
            "target_titles": ["Backend Engineer"],
        },
    )
    return response.json()["id"]


def test_queue_shows_discovered_imported_job(client: TestClient) -> None:
    job_id = create_job(client)

    response = client.get("/jobs/queue", params={"status": "discovered"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == job_id
    assert response.json()[0]["status"] == "discovered"
    assert response.json()[0]["score"] is None


def test_evaluation_moves_job_to_evaluated_queue(client: TestClient) -> None:
    job_id = create_job(client)
    profile_id = create_profile(client)

    client.post(f"/jobs/{job_id}/evaluate", json={"profile_id": profile_id})
    response = client.get("/jobs/queue", params={"status": "evaluated"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == job_id
    assert response.json()[0]["score"] == 100.0
    assert response.json()[0]["recommendation"] == "apply"


def test_backfills_status_for_existing_evaluation(client: TestClient) -> None:
    job_id = create_job(client)
    profile_id = create_profile(client)
    client.post(f"/jobs/{job_id}/evaluate", json={"profile_id": profile_id})
    with Session(get_engine()) as session:
        session.execute(
            delete(ApplicationRecord).where(ApplicationRecord.job_id == job_id)
        )
        session.commit()

    queue = client.get("/jobs/queue", params={"status": "evaluated"})
    interested = client.post(f"/jobs/{job_id}/interest")

    assert queue.json()[0]["status"] == "evaluated"
    assert interested.status_code == 200
    assert interested.json()["status"] == "interested"


def test_transitions_job_from_interest_to_application(client: TestClient) -> None:
    job_id = create_job(client)
    profile_id = create_profile(client)
    client.post(f"/jobs/{job_id}/evaluate", json={"profile_id": profile_id})

    interested = client.post(f"/jobs/{job_id}/interest")
    applied = client.post(f"/jobs/{job_id}/apply")

    assert interested.status_code == 200
    assert interested.json()["status"] == "interested"
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"
    assert applied.json()["applied_at"]


def test_rejects_invalid_status_transition(client: TestClient) -> None:
    job_id = create_job(client)

    response = client.post(
        f"/jobs/{job_id}/status",
        json={"status": "technical"},
    )

    assert response.status_code == 409
