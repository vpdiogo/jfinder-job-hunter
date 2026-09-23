from fastapi.testclient import TestClient


def test_saves_base_and_creates_a_profile_snapshot(client: TestClient) -> None:
    base = client.put(
        "/professional-base",
        json={
            "resume_content": "Python engineer with platform experience.",
            "links": ["https://example.com/profile"],
            "skills": ["Python", "FastAPI"],
            "experiences": ["Platform Engineer at Acme"],
            "education": ["Computer Science"],
            "languages": ["English"],
        },
    )
    assert base.status_code == 200
    assert base.json()["id"] == 1
    assert client.get("/professional-base").json()["skills"] == ["Python", "FastAPI"]

    profile = client.post(
        "/professional-base/application-profiles",
        json={"name": "Tech Lead", "skills": ["Python"], "target_titles": ["Tech Lead"]},
    )
    assert profile.status_code == 201
    assert profile.json()["name"] == "Tech Lead"

    client.put("/professional-base", json={"resume_content": "Updated", "skills": ["Go"]})
    assert client.get(f"/profiles/{profile.json()['id']}").json()["skills"] == ["Python"]


def test_requires_base_before_creating_profile(client: TestClient) -> None:
    response = client.post(
        "/professional-base/application-profiles",
        json={"name": "Tech Lead", "skills": [], "target_titles": []},
    )
    assert response.status_code == 409
