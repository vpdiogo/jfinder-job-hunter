import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    database_path = tmp_path / "jfinder-test.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    with TestClient(app) as test_client:
        yield test_client


def evaluation_payload() -> dict[str, object]:
    return {
        "job": {
            "title": "Senior Backend Engineer",
            "company": "Acme",
            "url": "https://example.com/jobs/1",
            "required_skills": ["Python", "FastAPI", "Kubernetes"],
        },
        "profile": {
            "skills": ["python", "FastAPI"],
            "target_titles": ["Backend Engineer"],
        },
    }


def test_evaluates_and_persists_job(client: TestClient) -> None:
    response = client.post("/evaluations", json=evaluation_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["score"] == 73.33
    assert body["recommendation"] == "review"
    assert body["missing_requirements"] == ["Kubernetes"]
    assert body["evaluated_at"]


def test_lists_and_filters_evaluations(client: TestClient) -> None:
    created = client.post("/evaluations", json=evaluation_payload()).json()

    response = client.get(
        "/evaluations",
        params={"recommendation": "review", "min_score": 70},
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == created["id"]


def test_gets_evaluation_by_id(client: TestClient) -> None:
    created = client.post("/evaluations", json=evaluation_payload()).json()

    response = client.get(f"/evaluations/{created['id']}")

    assert response.status_code == 200
    assert response.json()["job_url"] == "https://example.com/jobs/1"


def test_returns_not_found_for_unknown_evaluation(client: TestClient) -> None:
    response = client.get("/evaluations/999")

    assert response.status_code == 404


def test_rejects_incomplete_evaluation_request(client: TestClient) -> None:
    response = client.post("/evaluations", json={"job": {}})

    assert response.status_code == 422
