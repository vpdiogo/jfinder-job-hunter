from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluates_job_from_api_request() -> None:
    response = client.post(
        "/evaluations",
        json={
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
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_url": "https://example.com/jobs/1",
        "score": 73.33,
        "recommendation": "review",
        "reasons": [
            "Matched skills: Python, FastAPI.",
            "The job title matches a target role.",
        ],
        "missing_requirements": ["Kubernetes"],
        "matched_skills": ["Python", "FastAPI"],
    }


def test_rejects_incomplete_evaluation_request() -> None:
    response = client.post("/evaluations", json={"job": {}})

    assert response.status_code == 422
